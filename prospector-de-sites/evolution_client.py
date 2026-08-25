#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector — Cliente Evolution API (Python Standard Library).
Gerencia conectividade, autenticação por variável de ambiente e checagem de instâncias.
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
        cfg = config or {}
        evo_cfg = cfg.get("evolution", {}) if "evolution" in cfg else cfg

        # Variáveis de ambiente têm precedência sobre o config
        self.api_key_env = evo_cfg.get("apiKeyEnv", "EVOLUTION_API_KEY")
        self.api_key = os.environ.get(self.api_key_env) or os.environ.get("EVOLUTION_API_KEY", "")

        base_url = os.environ.get("EVOLUTION_API_URL") or evo_cfg.get("baseUrl", "")
        self.base_url = self._normalize_url(base_url)

        self.instance = os.environ.get("EVOLUTION_INSTANCE") or evo_cfg.get("instance", "")
        self.enabled = bool(evo_cfg.get("enabled", False))
        self.timeout = int(evo_cfg.get("timeoutSeconds", 15))

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not url:
            return ""
        url = url.strip()
        # Remove barras finais
        url = re.sub(r"/+$", "", url)
        return url

    def is_configured(self) -> bool:
        return bool(self.base_url and self.instance and self.api_key)

    def has_api_key(self) -> bool:
        return bool(self.api_key)

    def _get_ssl_context(self) -> ssl.SSLContext:
        # TLS verification sempre habilitado para conexões HTTPS
        return ssl.create_default_context()

    def _make_request(
        self, endpoint: str, method: str = "GET", payload: Optional[Dict[str, Any]] = None, base: Optional[str] = None
    ) -> Tuple[int, Optional[Any], Optional[str]]:
        """
        Executa requisição HTTP/HTTPS sem expor a API key em erros ou exceções.
        Retorna (status_code, parsed_json, error_message).
        """
        root = base or self.base_url
        if not root:
            return 0, None, "URL base não configurada."

        # Garante endpoint formatado
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

        # Alerta se usar HTTP não local
        parsed_url = urllib.parse.urlparse(url)
        is_local = parsed_url.hostname in ("localhost", "127.0.0.1", "::1")
        if parsed_url.scheme == "http" and not is_local:
            pass  # Warning handled in test_connection

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
            # Erro de conexão de rede ou certificado TLS
            reason_str = str(e.reason)
            return 0, None, f"Falha de conexão: {reason_str}"
        except Exception as e:
            return 0, None, f"Erro inesperado: {type(e).__name__}"

    def test_connection(self) -> Dict[str, Any]:
        """
        Executa verificação de conectividade e autenticação passo a passo.
        Suporta detecção de rotas (/instance/fetchInstances e /instance/connectionState).
        """
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

        # Passo A e B: Testar /instance/fetchInstances
        effective_base = self.base_url
        status, data, err = self._make_request("/instance/fetchInstances", method="GET", base=effective_base)

        # Se deu 404 na raiz, probe /api/instance/fetchInstances
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

        # Verificar se a instância configurada existe na lista
        instances_list = data if isinstance(data, list) else (data.get("instances") if isinstance(data, dict) else [])
        instance_names = []
        if isinstance(instances_list, list):
            for item in instances_list:
                if isinstance(item, dict):
                    # Formatos comuns da Evolution API: 'name', 'instanceName', 'instance'
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

        # Passo C: Checar status da conexão se a instância existir
        if self.instance:
            st_status, st_data, _ = self._make_request(
                f"/instance/connectionState/{urllib.parse.quote(self.instance)}",
                method="GET",
                base=effective_base,
            )

            if st_status == 200 and isinstance(st_data, dict):
                result["connectionStateSupported"] = True
                # Format: {"instance": {"state": "open"}} or {"state": "open"} or {"connection": "open"}
                state = (
                    st_data.get("instance", {}).get("state")
                    or st_data.get("state")
                    or st_data.get("instance", {}).get("connectionStatus")
                )
                result["connectionState"] = state
            elif st_status == 404:
                # Tolerância a versões Evolution v2 onde a rota de conexão tem variação
                result["connectionStateSupported"] = False
                result["connectionState"] = None
            else:
                result["connectionStateSupported"] = False

        return result

    def send_text_isolated(self, number: str, text: str) -> Dict[str, Any]:
        """
        Método isolado e seguro para envio futuro de mensagens via WhatsApp.
        NÃO chamado automaticamente por nenhuma rotina de teste.
        """
        if not self.is_configured():
            return {"ok": False, "error": "Evolution API não configurada ou sem API Key."}

        # Sanitizar número (somente dígitos)
        num_clean = re.sub(r"\D", "", number)
        if not num_clean:
            return {"ok": False, "error": "Número de telefone inválido."}

        payload = {
            "number": num_clean,
            "text": text,
            "delay": 1200,
            "linkPreview": True,
        }

        status, data, err = self._make_request(
            f"/message/sendText/{urllib.parse.quote(self.instance)}",
            method="POST",
            payload=payload,
        )

        if status in (200, 201):
            return {"ok": True, "data": data}
        return {"ok": False, "status": status, "error": err or "Falha no envio"}
