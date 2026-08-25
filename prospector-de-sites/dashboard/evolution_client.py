#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector — Cliente Evolution API (Python Standard Library).
Gerencia conectividade, autenticação por variável de ambiente e testes seguros de envio.
NUNCA armazena ou expõe a API Key em logs, arquivos ou respostas da API local.
"""

import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple


class EvolutionClient:
    """Cliente seguro para integração com Evolution API v1/v2."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Sincroniza do registro do usuário no Windows se ainda não refletido no processo atual
        if os.name == "nt":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
                for var in ["EVOLUTION_API_KEY", "EVOLUTION_API_URL", "EVOLUTION_INSTANCE"]:
                    if var not in os.environ:
                        try:
                            val, _ = winreg.QueryValueEx(key, var)
                            if val:
                                os.environ[var] = str(val)
                        except FileNotFoundError:
                            pass
                winreg.CloseKey(key)
            except Exception:
                pass

        cfg = config or {}
        evo_cfg = cfg.get("evolution", {}) if "evolution" in cfg else cfg

        # Variáveis de ambiente têm precedência quando o config for vazio/padrão
        self.api_key_env = evo_cfg.get("apiKeyEnv", "EVOLUTION_API_KEY")
        self.api_key = evo_cfg.get("apiKey") or os.environ.get(self.api_key_env) or os.environ.get("EVOLUTION_API_KEY", "")

        base_url = evo_cfg.get("baseUrl") or os.environ.get("EVOLUTION_API_URL") or ""
        self.base_url = self._normalize_url(base_url)

        self.instance = evo_cfg.get("instance") or os.environ.get("EVOLUTION_INSTANCE") or ""
        self.enabled = bool(evo_cfg.get("enabled", False))
        self.timeout = int(evo_cfg.get("timeoutSeconds", 15))

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""
        url = url.strip()
        url = re.sub(r"/+$", "", url)
        return url

    @staticmethod
    def validate_phone_number(raw: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Valida e normaliza o número com DDI e DDD sem adivinhações silenciosas.
        Retorna (clean_number, error_message).
        """
        if not raw or not isinstance(raw, str):
            return None, "Número de telefone não informado."

        has_plus = raw.strip().startswith("+")
        clean = re.sub(r"\D", "", raw)
        if not clean:
            return None, "Número de telefone inválido (deve conter apenas dígitos)."

        # Se começa com 55 (Brasil com DDI)
        if clean.startswith("55"):
            if len(clean) not in (12, 13):
                return None, "Número brasileiro com formato inválido. Esperado: DDI 55 + DDD (2 dígitos) + 8 ou 9 dígitos (ex: 5511999999999)."
            return clean, None

        # Se tem 10 ou 11 dígitos e não tem '+', é número local brasileiro sem DDI 55
        if len(clean) in (10, 11) and not has_plus:
            return None, "Número incompleto ou ambíguo. Informe o código do país DDI (ex: 55 para Brasil). Exemplo: 5511999999999"

        # Validação internacional geral (E.164: entre 10 e 15 dígitos)
        if len(clean) < 10 or len(clean) > 15:
            return None, "Número inválido. Deve conter entre 10 e 15 dígitos incluindo o código de país DDI."

        return clean, None

    @staticmethod
    def mask_phone_number(number: str) -> str:
        """Mascara o número para exibição segura em logs e respostas (ex: 5511****9999)."""
        if not number:
            return ""
        if len(number) >= 8:
            return number[:4] + "****" + number[-4:]
        return "****" + number[-2:] if len(number) >= 2 else "****"

    def is_configured(self) -> bool:
        return bool(self.base_url and self.instance and self.api_key)

    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def _get_ssl_context(self) -> ssl.SSLContext:
        return ssl.create_default_context()

    def _make_request(
        self, endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None, base: Optional[str] = None
    ) -> Tuple[int, Optional[Any], Optional[str]]:
        root = base or self.base_url
        if not root:
            return 0, None, "URL base não configurada."

        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = root + endpoint

        headers = {
            "apikey": self.api_key,
            "User-Agent": "Prospector-Evolution-Client/1.0",
        }

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        ctx = self._get_ssl_context() if url.lower().startswith("https://") else None

        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as response:
                status = response.getcode()
                body = response.read().decode("utf-8")
                try:
                    res_json = json.loads(body)
                except Exception:
                    res_json = {"raw": body}
                return status, res_json, None
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8")
                err_json = json.loads(body)
            except Exception:
                err_json = None
            sanitized_msg = f"HTTP {e.code}: {e.reason}"
            return e.code, err_json, sanitized_msg
        except urllib.error.URLError as e:
            reason_str = str(e.reason)
            return 0, None, f"Falha de conexão: {reason_str}"
        except Exception as e:
            return 0, None, f"Erro inesperado: {type(e).__name__}"

    def test_connection(self) -> Dict[str, Any]:
        """Verifica conectividade, autenticação e status da instância."""
        result: Dict[str, Any] = {
            "configured": bool(self.base_url and self.instance),
            "hasApiKey": bool(self.api_key),
            "baseUrl": self.base_url,
            "effectiveBaseUrl": self.base_url,
            "instance": self.instance,
            "reachable": False,
            "authenticated": False,
            "instanceFound": False,
            "connectionState": None,
            "connectionStateSupported": False,
            "warning": None,
            "error": None,
        }

        if not self.base_url:
            result["error"] = "Base URL não informada."
            return result

        parsed = urllib.parse.urlparse(self.base_url)
        is_local = parsed.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed.scheme == "http" and not is_local:
            result["warning"] = "Aviso de segurança: URL VPS em HTTP puro. Recomendado usar HTTPS."

        if not self.api_key:
            result["error"] = f"Chave de API não configurada. Defina a variável de ambiente {self.api_key_env}."
            return result

        effective_base = self.base_url
        status, data, err = self._make_request("/instance/fetchInstances", method="GET", base=effective_base)

        if status == 404 and not effective_base.endswith("/api"):
            alt_base = effective_base + "/api"
            alt_status, alt_data, alt_err = self._make_request(
                "/instance/fetchInstances", method="GET", base=alt_base
            )
            if alt_status == 200 or alt_status in (401, 403):
                effective_base = alt_base
                status, data, err = alt_status, alt_data, alt_err
                result["effectiveBaseUrl"] = effective_base

        if status == 0:
            result["error"] = err or "Servidor Evolution inalcançável."
            return result

        result["reachable"] = True

        if status in (401, 403):
            result["authenticated"] = False
            result["error"] = "Autenticação recusada (API Key inválida ou sem permissão)."
            return result

        if status != 200:
            result["error"] = f"Resposta inesperada do endpoint de instâncias (HTTP {status})."
            return result

        result["authenticated"] = True

        instances_list = data if isinstance(data, list) else (data.get("instances") if isinstance(data, dict) else [])
        instance_names = []
        if isinstance(instances_list, list):
            for item in instances_list:
                if isinstance(item, dict):
                    name = item.get("name") or item.get("instanceName") or item.get("instance", {}).get("instanceName") or item.get("id")
                    if name:
                        instance_names.append(str(name))

        if self.instance in instance_names:
            result["instanceFound"] = True
        elif not self.instance and instance_names:
            result["instanceFound"] = False
            result["warning"] = f"Instância não especificada. Instâncias disponíveis na API: {', '.join(instance_names)}"
        else:
            result["instanceFound"] = False
            result["error"] = f"Instância '{self.instance}' não encontrada no Evolution API (disponíveis: {', '.join(instance_names) if instance_names else 'nenhuma'})."

        if self.instance:
            st_status, st_data, _ = self._make_request(
                f"/instance/connectionState/{urllib.parse.quote(self.instance)}",
                method="GET",
                base=effective_base,
            )

            if st_status == 200 and isinstance(st_data, dict):
                result["connectionStateSupported"] = True
                state = (
                    st_data.get("instance", {}).get("state")
                    or st_data.get("state")
                    or st_data.get("instance", {}).get("connectionStatus")
                )
                result["connectionState"] = state
            elif st_status == 404:
                result["connectionStateSupported"] = False
                result["connectionState"] = None
            else:
                result["connectionStateSupported"] = False

        return result

    def send_test_message(self, number: str, text: Optional[str] = None, confirmed: bool = False) -> Dict[str, Any]:
        """
        Executa envio de teste estritamente controlado e autorizado.
        Exige número validado e confirmed=True.
        """
        if not confirmed:
            return {
                "success": False,
                "error": "Envio de teste não confirmado. Marque o checkbox de autorização para prosseguir.",
            }

        if not self.is_configured():
            return {
                "success": False,
                "error": "Evolution API não está totalmente configurada (verifique Base URL, Instância e EVOLUTION_API_KEY).",
            }

        clean_number, err = self.validate_phone_number(number)
        if err:
            return {"success": False, "error": err}

        msg_text = (text or "").strip()
        if not msg_text:
            msg_text = "Teste de conexão do Prospector via Evolution API."

        payload = {
            "number": clean_number,
            "text": msg_text,
            "delay": 1200,
            "linkPreview": True,
        }

        status, data, err_msg = self._make_request(
            f"/message/sendText/{urllib.parse.quote(self.instance)}",
            method="POST",
            payload=payload,
        )

        if status in (200, 201) and isinstance(data, dict):
            # Formatos Evolution v2: {"key": {"id": "..."}, "status": "PENDING"} ou {"messageId": "..."}
            key_obj = data.get("key") if isinstance(data.get("key"), dict) else {}
            msg_id = key_obj.get("id") or data.get("messageId") or data.get("id") or "enviado"
            st_val = data.get("status") or "sent"

            return {
                "success": True,
                "instance": self.instance,
                "numberNormalized": self.mask_phone_number(clean_number),
                "messageId": str(msg_id),
                "status": str(st_val).lower(),
            }

        # Tratamento de erros detalhados e higienizados
        detail = ""
        if isinstance(data, dict):
            detail = data.get("message") or data.get("error") or ""
            if isinstance(detail, list):
                detail = ", ".join(str(x) for x in detail)

        full_err = f"Falha HTTP {status}: {detail or err_msg or 'Erro desconhecido ao enviar mensagem'}"
        return {
            "success": False,
            "instance": self.instance,
            "error": full_err,
        }
