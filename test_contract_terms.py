#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for contract commercial terms and private delivery.

No CRM mutation, no outreach, no network calls.
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
SKILL = ROOT / "prospector-de-sites" / "skills" / "contrato-servico" / "SKILL.md"
TEMPLATE = ROOT / "prospector-de-sites" / "skills" / "contrato-servico" / "references" / "contrato-template.html"
GENERATOR = ROOT / "prospector-de-sites" / "skills" / "contrato-servico" / "references" / "gerar-docx.py"

LEGACY = [
    "manutenção mensal da página (hospedagem, pequenas atualizações de texto/imagens e suporte)",
    "a contratação e renovação de hospedagem e domínio próprios são de responsabilidade do CONTRATANTE",
]


def synthetic_data():
    return {
        "NOME_CLIENTE": "Cliente de Teste",
        "CPF_CNPJ_CLIENTE_LABEL": "inscrito no CPF",
        "CPF_CNPJ_CLIENTE": "(preencher)",
        "ENDERECO_CLIENTE": "(preencher)",
        "CIDADE_UF_CLIENTE": "Rio Claro/SP",
        "NOME_PRESTADOR": "Prestador de Teste",
        "CPF_CNPJ_PRESTADOR_LABEL": "inscrito no CPF",
        "CPF_CNPJ_PRESTADOR": "000.000.000-00",
        "ENDERECO_PRESTADOR": "Endereço sintético de teste",
        "CIDADE_UF_PRESTADOR": "São Paulo/SP",
        "TEXTO_OBJETO": "a criação de uma nova versão da página institucional do CONTRATANTE",
        "URL_PUBLICADA": "https://example.invalid/preview",
        "VALOR": "1.234,00",
        "VALOR_EXTENSO": "mil duzentos e trinta e quatro reais",
        "FORMA_PAGAMENTO": "condição sintética usada somente neste teste",
        "PRAZO_ENTREGA": "7 (sete) dias úteis",
        "RODADAS_AJUSTES": "1 (uma)",
        "TEXTO_HOSPEDAGEM": (
            "O registro, a titularidade e a renovação do domínio são de responsabilidade do CONTRATANTE. "
            "A hospedagem da página será disponibilizada pelo CONTRATADO(A) sem cobrança separada de hospedagem, "
            "sem que isso implique manutenção mensal ou suporte ilimitado."
        ),
        "CIDADE_FORO": "Rio Claro/SP",
        "CIDADE_ASSINATURA": "Rio Claro/SP",
        "DATA_EXTENSO": "",
        "MANUTENCAO": False,
    }


class ContractTermsTest(unittest.TestCase):
    def test_no_legacy_commercial_text(self):
        combined = TEMPLATE.read_text(encoding="utf-8") + "\n" + GENERATOR.read_text(encoding="utf-8")
        for phrase in LEGACY:
            self.assertNotIn(phrase, combined)

    def test_private_delivery_rule_is_explicit(self):
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("NUNCA publicar contrato", skill)
        self.assertIn("PDF/DOCX", skill)
        self.assertIn("área local/privada", skill)
        self.assertIn("noindex` não transforma uma URL pública em armazenamento privado", skill)

    def test_template_has_current_terms(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("Do domínio e da hospedagem", html)
        self.assertIn("Do editor de conteúdo e alterações futuras", html)
        self.assertIn("sem cobrança por cada edição", html)
        self.assertIn("orçamento separado", html)
        self.assertIn("NUNCA copiar para o repositório público", html)

    def test_docx_generator_current_terms(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            data_path = td / "dados.json"
            out_path = td / "contrato.docx"
            data_path.write_text(json.dumps(synthetic_data(), ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(GENERATOR), str(data_path), str(out_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
            self.assertTrue(out_path.exists())
            with zipfile.ZipFile(out_path) as zf:
                xml = zf.read("word/document.xml").decode("utf-8")
            self.assertIn("Do domínio e da hospedagem", xml)
            self.assertIn("Do editor de conteúdo e alterações futuras", xml)
            self.assertIn("sem cobrança por cada edição", xml)
            self.assertIn("orçamento separado", xml)

    def test_maintenance_requires_explicit_scope(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            d = synthetic_data()
            d["MANUTENCAO"] = True
            d["VALOR_MANUTENCAO"] = "99,00"
            data_path = td / "dados.json"
            out_path = td / "contrato.docx"
            data_path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(GENERATOR), str(data_path), str(out_path)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("TEXTO_MANUTENCAO", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
