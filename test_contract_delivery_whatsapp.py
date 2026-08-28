#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression test suite for private contract PDF delivery via WhatsApp (Evolution API).

NO messages are sent, NO CRM mutations occur, NO public URLs created.
"""

import os
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from evolution_client import EvolutionClient
import outreach_service

ROOT = pathlib.Path(__file__).resolve().parent
DRY_RUN_PDF = ROOT / "private" / "contracts" / "dry-run-instituto-ferreira" / "contrato-dry-run.pdf"


class TestContractDeliveryWhatsApp(unittest.TestCase):
    def setUp(self):
        self.config = {
            "evolution": {
                "baseUrl": "https://evolution.example.com",
                "instance": "autocora-instance",
                "apiKey": "SECRET_API_KEY_DO_NOT_LOG",
                "enabled": True,
            },
            "assinatura": {
                "nome": "Leonardo Rosa",
                "apresentacao": "AutoCORA | Landing pages e automação com IA",
                "whatsapp": "5511994289238",
            },
            "market": {
                "defaultCountry": "BR",
                "defaultLocale": "pt-BR",
            },
            "outreach": {
                "channelPriority": ["whatsapp", "email"],
            }
        }
        self.client = EvolutionClient(self.config)

    def test_a_confirmed_false_sends_nothing(self):
        """Test A: confirmed=False never triggers provider request."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test contract content")
            tmp_pdf = f.name

        try:
            with patch.object(self.client, "_make_request") as mock_req:
                res = self.client.send_document(
                    number="11999998888",
                    file_path=tmp_pdf,
                    filename="contrato-teste.pdf",
                    caption="Segue o contrato",
                    confirmed=False,
                    country="BR",
                )
                self.assertFalse(res["success"])
                self.assertTrue(res.get("dryRun"))
                self.assertEqual(res.get("providerRequests"), 0)
                mock_req.assert_not_called()
        finally:
            if os.path.exists(tmp_pdf):
                os.remove(tmp_pdf)

    def test_b_missing_pdf_fails_closed(self):
        """Test B: Missing PDF file path raises or returns error cleanly."""
        res = self.client.send_document(
            number="11999998888",
            file_path="non_existent_file.pdf",
            confirmed=True,
            country="BR",
        )
        self.assertFalse(res["success"])
        self.assertIn("não encontrado", res["error"].lower())

    def test_c_non_pdf_fails_closed(self):
        """Test C: Non-PDF files or invalid magic bytes fail closed."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not a pdf")
            tmp_txt = f.name

        try:
            res = self.client.send_document(
                number="11999998888",
                file_path=tmp_txt,
                confirmed=True,
                country="BR",
            )
            self.assertFalse(res["success"])
            self.assertIn("apenas arquivos com extensão .pdf", res["error"].lower())
        finally:
            if os.path.exists(tmp_txt):
                os.remove(tmp_txt)

    def test_d_invalid_recipient_fails_closed(self):
        """Test D: Invalid phone number fails closed before any request."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test")
            tmp_pdf = f.name

        try:
            with patch.object(self.client, "_make_request") as mock_req:
                res = self.client.send_document(
                    number="123",  # invalid short number
                    file_path=tmp_pdf,
                    confirmed=True,
                    country="BR",
                )
                self.assertFalse(res["success"])
                self.assertIn("inválido", res["error"].lower())
                mock_req.assert_not_called()
        finally:
            if os.path.exists(tmp_pdf):
                os.remove(tmp_pdf)

    def test_e_build_document_payload_format(self):
        """Test E: Correct media payload built with base64 without public URL."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 synthetic contract bytes")
            tmp_pdf = f.name

        try:
            payload = self.client.build_document_payload(
                number="11999998888",
                file_path=tmp_pdf,
                filename="contrato-instituto.pdf",
                caption="Minuta contratual",
                country="BR",
            )
            self.assertEqual(payload["number"], "5511999998888")
            self.assertEqual(payload["mediatype"], "document")
            self.assertEqual(payload["mimetype"], "application/pdf")
            self.assertEqual(payload["fileName"], "contrato-instituto.pdf")
            self.assertEqual(payload["caption"], "Minuta contratual")
            self.assertTrue(payload["media"].startswith("data:application/pdf;base64,"))
            self.assertNotIn("http://", payload["media"])
            self.assertNotIn("https://", payload["media"])
        finally:
            if os.path.exists(tmp_pdf):
                os.remove(tmp_pdf)

    def test_f_secrets_and_base64_not_in_output_or_error(self):
        """Test F: API key and base64 blob are not exposed in returned error dictionaries."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 secret test")
            tmp_pdf = f.name

        try:
            with patch.object(self.client, "_make_request", return_value=(500, {"error": "Server error"}, "Internal Server Error")):
                res = self.client.send_document(
                    number="11999998888",
                    file_path=tmp_pdf,
                    confirmed=True,
                    country="BR",
                )
                res_str = str(res)
                self.assertNotIn("SECRET_API_KEY", res_str)
                self.assertNotIn("data:application/pdf", res_str)
        finally:
            if os.path.exists(tmp_pdf):
                os.remove(tmp_pdf)

    def test_g_recipient_masked_in_results(self):
        """Test G: Recipient phone number is masked in response."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 test")
            tmp_pdf = f.name

        try:
            res = self.client.send_document(
                number="11999998888",
                file_path=tmp_pdf,
                confirmed=False,
                country="BR",
            )
            self.assertEqual(res["numberNormalized"], "5511****8888")
        finally:
            if os.path.exists(tmp_pdf):
                os.remove(tmp_pdf)

    def test_h_channel_recommendation_whatsapp_preferred(self):
        """Test H: Active WhatsApp conversation channel prefers WhatsApp document delivery."""
        lead = {
            "slug": "instituto-ferreira",
            "nome": "Instituto Ferreira",
            "cidade": "Rio Claro",
            "telefone": "19998887766",
            "email": "contato@institutoferreira.com.br",
            "country": "BR",
        }
        evo_status = {
            "reachable": True,
            "authenticated": True,
            "instanceFound": True,
            "connectionState": "open",
        }
        rec = outreach_service.recommend_contract_delivery_channel(
            lead=lead,
            config=self.config,
            active_channel="whatsapp",
            contract_pdf_path=str(DRY_RUN_PDF) if DRY_RUN_PDF.exists() else None,
            evo_status=evo_status,
        )
        self.assertEqual(rec["recommendedChannel"], "whatsapp")
        self.assertEqual(rec["recipient"], "5519****7766")
        self.assertEqual(rec["attachment"], "contrato-instituto-ferreira.pdf")
        self.assertIn("Conforme combinamos", rec["caption"])
        self.assertEqual(rec["documentCapability"], "SUPPORTED")
        self.assertTrue(rec["requiresConfirmation"])
        self.assertFalse(rec["autoSend"])

    def test_i_channel_recommendation_email_fallback(self):
        """Test I: Falls back to email if WhatsApp is unavailable."""
        lead = {
            "slug": "instituto-ferreira",
            "nome": "Instituto Ferreira",
            "cidade": "Rio Claro",
            "telefone": "",  # no phone
            "email": "contato@institutoferreira.com.br",
            "country": "BR",
        }
        rec = outreach_service.recommend_contract_delivery_channel(
            lead=lead,
            config=self.config,
            active_channel="whatsapp",
        )
        self.assertEqual(rec["recommendedChannel"], "email")
        self.assertEqual(rec["recipient"], "contato@institutoferreira.com.br")

    def test_j_dry_run_synthetic_pdf_inspection(self):
        """Test J: Dry-run synthetic PDF builds payload accurately with 0 sends."""
        if not DRY_RUN_PDF.exists():
            self.skipTest("Dry run synthetic PDF not present in local workspace")

        payload = self.client.build_document_payload(
            number="19998887766",
            file_path=str(DRY_RUN_PDF),
            filename="contrato-instituto-ferreira-dry-run.pdf",
            caption="Minuta do contrato",
            country="BR",
        )
        self.assertEqual(payload["fileName"], "contrato-instituto-ferreira-dry-run.pdf")
        self.assertEqual(payload["mediatype"], "document")
        self.assertEqual(payload["mimetype"], "application/pdf")
        self.assertTrue(len(payload["media"]) > 1000)

        # Ensure confirmed=False generates zero network requests
        with patch.object(self.client, "_make_request") as mock_req:
            res = self.client.send_document(
                number="19998887766",
                file_path=str(DRY_RUN_PDF),
                confirmed=False,
                country="BR",
            )
            self.assertFalse(res["success"])
            self.assertEqual(res.get("providerRequests"), 0)
            mock_req.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
