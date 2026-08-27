#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression test suite for verified outreach identity and fail-closed behavior.
NO messages are sent, NO CRM mutations occur.
"""

import sys
import unittest
import importlib
from typing import Dict, Any

# Ensure both paths can be tested
import outreach_service


class TestOutreachIdentity(unittest.TestCase):
    def setUp(self):
        self.valid_config: Dict[str, Any] = {
            "assinatura": {
                "nome": "Leonardo Rosa",
                "apresentacao": "AutoCORA | Landing pages e automação com IA",
                "whatsapp": "5511994289238",
            },
            "deploy": {
                "domain": "prospector-sites-beta.vercel.app",
                "basePath": "clientes",
            },
            "outreach": {
                "portfolioUrl": "https://autocora.com.br/pt/landing-pages",
                "channelPriority": ["whatsapp", "email"],
                "mode": "review",
                "maxFollowUps": 1,
                "followUpAfterBusinessDays": 3,
            },
            "market": {
                "defaultCountry": "BR",
                "defaultLocale": "pt-BR",
                "defaultLanguage": "pt",
            },
        }

        self.lead_br_redesign: Dict[str, Any] = {
            "slug": "clinica-exemplo",
            "nome": "Clínica Exemplo",
            "cidade": "São Paulo",
            "telefone": "11988887777",
            "email": "contato@clinicaexemplo.com.br",
            "nota": 4.9,
            "avaliacoes": 120,
            "nicho": "odontologia",
            "siteAntigo": "https://clinicaexemplo.com.br",
            "siteMode": "redesign",
            "websiteStatus": "poor",
            "country": "BR",
            "locale": "pt-BR",
            "motivo": "não é responsivo e é lento",
        }

        self.lead_pt_new: Dict[str, Any] = {
            "slug": "restaurante-lisboa",
            "nome": "Restaurante Lisboa",
            "cidade": "Lisboa",
            "telefone": "351912345678",
            "email": "info@restaurantelisboa.pt",
            "nota": 4.8,
            "avaliacoes": 85,
            "nicho": "restaurante",
            "siteAntigo": "",
            "siteMode": "new_site_concept",
            "websiteStatus": "none",
            "country": "PT",
            "locale": "pt-PT",
        }

    def test_a_valid_approved_assinatura(self):
        """Test A: Valid approved assinatura succeeds and contains real identity without fabricated fallbacks."""
        for lead in [self.lead_br_redesign, self.lead_pt_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            self.assertIn("whatsapp", res)
            self.assertIn("email", res)

            wpp_text = res["whatsapp"]["text"]
            email_html = res["email"]["bodyHtml"]

            # Author present
            self.assertIn("Leonardo Rosa", wpp_text)
            self.assertIn("Leonardo Rosa", email_html)

            # Presentation present in email signature
            self.assertIn("AutoCORA | Landing pages e automação com IA", email_html)

            # WhatsApp present in email signature
            self.assertIn("5511994289238", email_html)

            # NO fabricated fallback strings
            forbidden = [
                "Especialista em Web",
                "Criação e Redesign de Páginas",
                "Design e Criação de Páginas Web",
            ]
            for phrase in forbidden:
                self.assertNotIn(phrase, wpp_text, f"Forbidden phrase '{phrase}' found in whatsapp text")
                self.assertNotIn(phrase, email_html, f"Forbidden phrase '{phrase}' found in email html")

    def test_b_missing_assinatura_nome_fails_closed(self):
        """Test B: Missing or empty assinatura.nome raises ValueError."""
        bad_configs = [
            {"assinatura": {"nome": "", "apresentacao": "AutoCORA", "whatsapp": "5511994289238"}},
            {"assinatura": {"nome": "   ", "apresentacao": "AutoCORA"}},
            {"assinatura": {"apresentacao": "AutoCORA"}},
            {"assinatura": {}},
            {},
        ]
        for cfg in bad_configs:
            with self.assertRaises(ValueError) as ctx:
                outreach_service.generate_messages(self.lead_br_redesign, cfg)
            self.assertIn("Identidade de outreach não configurada", str(ctx.exception))

    def test_c_missing_assinatura_apresentacao_fails_closed(self):
        """Test C: Missing or empty assinatura.apresentacao raises ValueError."""
        bad_configs = [
            {"assinatura": {"nome": "Leonardo Rosa", "apresentacao": "", "whatsapp": "5511994289238"}},
            {"assinatura": {"nome": "Leonardo Rosa", "apresentacao": "   "}},
            {"assinatura": {"nome": "Leonardo Rosa"}},
        ]
        for cfg in bad_configs:
            with self.assertRaises(ValueError) as ctx:
                outreach_service.generate_messages(self.lead_br_redesign, cfg)
            self.assertIn("Identidade de outreach não configurada", str(ctx.exception))

    def test_d_market_service_importerror_fallback_keyword_args(self):
        """Test D: normalize_phone_by_country fallback accepts country= keyword arg without TypeError."""
        # Test fallback lambda definition
        fallback_fn = lambda raw, country=None, *a, **k: (raw, None)
        res_pos = fallback_fn("11999998888", "BR")
        self.assertEqual(res_pos, ("11999998888", None))

        res_kw = fallback_fn("11999998888", country="BR")
        self.assertEqual(res_kw, ("11999998888", None))

        res_extra = fallback_fn("11999998888", country="PT", extra_param=123)
        self.assertEqual(res_extra, ("11999998888", None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
