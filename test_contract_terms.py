#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for contract commercial terms, legal provider fail-closed check, and private delivery.

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


def real_contract_data():
    return {
        "NOME_CLIENTE": "Cliente Real de Teste",
        "CPF_CNPJ_CLIENTE_LABEL": "inscrito no CPF",
        "CPF_CNPJ_CLIENTE": "123.456.789-00",
        "ENDERECO_CLIENTE": "Rua das Flores, 123",
        "CIDADE_UF_CLIENTE": "Rio Claro/SP",
        "NOME_PRESTADOR": "Leonardo Rosa",
        "CPF_CNPJ_PRESTADOR_LABEL": "inscrito no CPF",
        "CPF_CNPJ_PRESTADOR": "987.654.321-11",
        "ENDERECO_PRESTADOR": "Av. Paulista, 1000",
        "CIDADE_UF_PRESTADOR": "São Paulo/SP",
        "TEXTO_OBJETO": "a criação de uma nova versão da página institucional do CONTRATANTE",
        "URL_PUBLICADA": "https://example.invalid/preview",
        "VALOR": "1.234,00",
        "VALOR_EXTENSO": "mil duzentos e trinta e quatro reais",
        "FORMA_PAGAMENTO": "condição acordada",
        "PRAZO_ENTREGA": "7 (sete) dias úteis",
        "RODADAS_AJUSTES": "1 (uma)",
        "TEXTO_HOSPEDAGEM": (
            "O registro, a titularidade e a renovação do domínio são de responsabilidade do CONTRATANTE. "
            "A hospedagem da página será disponibilizada pelo CONTRATADO(A) sem cobrança separada de hospedagem, "
            "sem que isso implique manutenção mensal ou suporte ilimitado."
        ),
        "CIDADE_FORO": "São Paulo/SP",
        "CIDADE_ASSINATURA": "São Paulo/SP",
        "DATA_EXTENSO": "27 de agosto de 2026",
        "MANUTENCAO": False,
        "dry_run": False,
    }


def synthetic_data():
    d = real_contract_data()
    d["dry_run"] = True
    d["CPF_CNPJ_PRESTADOR"] = "(PREENCHER ANTES DO CONTRATO REAL)"
    d["ENDERECO_PRESTADOR"] = "(PREENCHER ANTES DO CONTRATO REAL)"
    return d


class ContractTermsTest(unittest.TestCase):
    def test_template_does_not_ship_legacy_commercial_text(self):
        html = TEMPLATE.read_text(encoding="utf-8")
        for phrase in LEGACY:
            self.assertNotIn(phrase, html)

    def test_generator_rejects_legacy_commercial_text(self):
        code = GENERATOR.read_text(encoding="utf-8")
        self.assertIn("redação comercial antiga", code)
        self.assertIn("TEXTO_HOSPEDAGEM", code)

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
            data_path.write_text(json.dumps(real_contract_data(), ensure_ascii=False), encoding="utf-8")
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

    def test_real_contract_fails_closed_when_provider_legal_data_missing(self):
        bad_placeholders = [
            "(PREENCHER ANTES DO CONTRATO REAL)",
            "(preencher)",
            "000.000.000-00",
            "",
        ]
        for bad in bad_placeholders:
            with tempfile.TemporaryDirectory() as td:
                td = pathlib.Path(td)
                d = real_contract_data()
                d["CPF_CNPJ_PRESTADOR"] = bad
                d["dry_run"] = False
                data_path = td / "dados.json"
                out_path = td / "contrato.docx"
                data_path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
                proc = subprocess.run(
                    [sys.executable, str(GENERATOR), str(data_path), str(out_path)],
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(proc.returncode, 0)
                out = proc.stdout + proc.stderr
                self.assertTrue("Contrato real bloqueado" in out or "Campos obrigatórios ausentes" in out)

    def test_dry_run_contract_generation_succeeds(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            d = synthetic_data()
            data_path = td / "dados.json"
            out_path = td / "contrato.docx"
            data_path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(GENERATOR), str(data_path), str(out_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
            self.assertTrue(out_path.exists())

    def test_maintenance_requires_explicit_scope(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            d = real_contract_data()
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

    def test_br_contract_delivery_language_rule(self):
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("Atenciosamente", skill)
        self.assertIn("proibido usar `Com os melhores cumprimentos`", skill)

    def test_contract_without_assistant_does_not_contain_assistant_clauses(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            d = real_contract_data()
            d["assistantIncluded"] = False
            data_path = td / "dados.json"
            out_path = td / "contrato.docx"
            data_path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(GENERATOR), str(data_path), str(out_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
            with zipfile.ZipFile(out_path) as zf:
                xml = zf.read("word/document.xml").decode("utf-8")
            self.assertNotIn("Do assistente inteligente do site", xml)
            self.assertNotIn("consumo do serviço de inteligência artificial", xml)

    def test_contract_with_assistant_contains_responsibility_and_variable_estimate(self):
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            d = real_contract_data()
            d["assistantIncluded"] = True
            d["assistantSetupValue"] = "450,00"
            data_path = td / "dados.json"
            out_path = td / "contrato.docx"
            data_path.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(GENERATOR), str(data_path), str(out_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + "\n" + proc.stderr)
            with zipfile.ZipFile(out_path) as zf:
                xml = zf.read("word/document.xml").decode("utf-8")
            self.assertIn("Do assistente inteligente do site", xml)
            self.assertIn("informações verificadas", xml)
            self.assertIn("não substituindo avaliação", xml)
            self.assertIn("cobrado separadamente", xml)
            self.assertIn("integral responsabilidade do CONTRATANTE", xml)
            self.assertIn("R$ 1 a R$ 3 por 1.000 respostas curtas", xml)
            self.assertIn("US$ 0,20 a US$ 0,60", xml)
            self.assertIn("caráter meramente referencial e não vinculante", xml)
            self.assertIn("não configura indisponibilidade da hospedagem ou do site", xml)
            self.assertIn("substituídos quando tecnicamente necessário", xml)

            forbidden = [
                "mensagens ilimitadas",
                "preço fixo permanente",
                "uso gratuito para sempre",
                "volume garantido",
            ]
            for term in forbidden:
                self.assertNotIn(term, xml)

    def test_old_groq_based_estimate_is_not_canonical(self):
        skill = SKILL.read_text(encoding="utf-8")
        generator = GENERATOR.read_text(encoding="utf-8")
        self.assertNotIn("R$ 10 a R$ 25 por 1.000 respostas curtas", skill)
        self.assertNotIn("R$ 10 a R$ 25 por 1.000 respostas curtas", generator)
        self.assertIn("pool de produção", skill)


if __name__ == "__main__":
    unittest.main(verbosity=2)
