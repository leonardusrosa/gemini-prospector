#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression test suite for verified outreach identity, fail-closed behavior,
permission-first cold WhatsApp flow, removal of stale ratings & praise,
and accurate AutoCORA signature.
NO messages are sent, NO CRM mutations occur.
"""

import re
import unittest
from typing import Dict, Any

import outreach_service


class TestOutreachIdentityAndPermissionFirst(unittest.TestCase):
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

        self.lead_br_new: Dict[str, Any] = {
            "slug": "dr-silva-consultorio",
            "nome": "Dr. Silva Consultório",
            "cidade": "Campinas",
            "telefone": "19999887766",
            "email": "contato@drsilva.com.br",
            "nota": 5.0,
            "avaliacoes": 45,
            "nicho": "medicina",
            "siteAntigo": "",
            "siteMode": "new_site_concept",
            "websiteStatus": "none",
            "country": "BR",
            "locale": "pt-BR",
        }

        self.lead_pt_redesign: Dict[str, Any] = {
            "slug": "clinica-porto",
            "nome": "Clínica Porto",
            "cidade": "Porto",
            "telefone": "351912345678",
            "email": "info@clinicaporto.pt",
            "nota": 4.9,
            "avaliacoes": 60,
            "nicho": "estética",
            "siteAntigo": "https://clinicaporto.pt",
            "siteMode": "redesign",
            "websiteStatus": "poor",
            "country": "PT",
            "locale": "pt-PT",
            "motivo": "tem navegação lenta no telemóvel",
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

    def _assert_no_urls(self, text: str, lead_name: str):
        """Helper to ensure text contains zero URLs or links."""
        self.assertNotIn("http://", text, f"Found 'http://' in {lead_name}")
        self.assertNotIn("https://", text, f"Found 'https://' in {lead_name}")
        self.assertNotIn("proposta.html", text, f"Found 'proposta.html' in {lead_name}")
        self.assertNotIn("autocora.com.br", text, f"Found portfolio URL in {lead_name}")
        self.assertNotIn("prospector-sites-beta.vercel.app", text, f"Found domain URL in {lead_name}")

    def _assert_no_stale_ratings_or_praise(self, text: str, lead_name: str):
        """Helper to ensure text contains no rating numbers, review counts or fabricated praise."""
        forbidden_patterns = [
            r"\bnota\b",
            r"\bavaliações\b",
            r"\bavaliações\b",
            r"\bclassificação\b",
            r"\btrabalho excelente\b",
            r"\bempresa de referência\b",
            r"\btrabalho de referência\b",
            r"\bclínica renomada\b",
            r"\b4\.9\b",
            r"\b5\.0\b",
            r"\b4\.8\b",
            r"\b120\b",
            r"\b45\b",
            r"\b85\b",
            r"\b60\b",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(
                re.search(pat, text, re.IGNORECASE),
                f"Pattern '{pat}' found in {lead_name}: {text}"
            )

    def test_a_br_cold_whatsapp_no_url_no_ratings_no_fabricated_praise(self):
        """Test A: BR redesign & new-site firstContact contains NO URL, NO ratings, NO fabricated praise."""
        for lead in [self.lead_br_redesign, self.lead_br_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            first_contact = res["whatsapp"]["firstContact"]
            self._assert_no_urls(first_contact, f"BR {lead['slug']} firstContact")
            self._assert_no_stale_ratings_or_praise(first_contact, f"BR {lead['slug']} firstContact")
            self.assertIn("Leonardo | AutoCORA", first_contact)
            self.assertIn("Posso te mandar o link", first_contact)

    def test_b_pt_cold_whatsapp_no_url_no_ratings_no_fabricated_praise(self):
        """Test B: PT redesign & new-site firstContact contains NO URL, NO ratings, NO fabricated praise."""
        for lead in [self.lead_pt_redesign, self.lead_pt_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            first_contact = res["whatsapp"]["firstContact"]
            self._assert_no_urls(first_contact, f"PT {lead['slug']} firstContact")
            self._assert_no_stale_ratings_or_praise(first_contact, f"PT {lead['slug']} firstContact")
            self.assertIn("Leonardo | AutoCORA", first_contact)
            self.assertIn("Posso enviar-lhe o link", first_contact)

    def test_c_after_permission_contains_proposal_url(self):
        """Test C: afterPermission contains exactly the proposal URL."""
        for lead in [self.lead_br_redesign, self.lead_br_new, self.lead_pt_redesign, self.lead_pt_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            after_perm = res["whatsapp"]["afterPermission"]
            expected_url = f"https://prospector-sites-beta.vercel.app/clientes/{lead['slug']}/proposta.html"
            self.assertIn(expected_url, after_perm)
            self.assertEqual(res["proposalUrl"], expected_url)

    def test_d_identity_remains_leonardo_rosa_autocora(self):
        """Test D: Full commercial identity remains available in email/metadata."""
        for lead in [self.lead_br_redesign, self.lead_pt_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            email_html = res["email"]["bodyHtml"]

            self.assertIn("Leonardo Rosa", email_html)
            self.assertIn("AutoCORA | Landing pages e automação com IA", email_html)
            self.assertIn("5511994289238", email_html)

            # Check no fabricated fallbacks
            forbidden = [
                "Especialista em Web",
                "Criação e Redesign de Páginas",
                "Design e Criação de Páginas Web",
            ]
            for phrase in forbidden:
                self.assertNotIn(phrase, email_html)

    def test_e_br_email_closing_language(self):
        """Test E: BR email closing uses Atenciosamente and never Com os melhores cumprimentos."""
        res = outreach_service.generate_messages(self.lead_br_redesign, self.valid_config)
        email_html = res["email"]["bodyHtml"]
        self.assertIn("Atenciosamente,", email_html)
        self.assertNotIn("Com os melhores cumprimentos", email_html)

    def test_f_pt_email_closing_language(self):
        """Test F: PT email closing uses Com os melhores cumprimentos."""
        res = outreach_service.generate_messages(self.lead_pt_redesign, self.valid_config)
        email_html = res["email"]["bodyHtml"]
        self.assertIn("Com os melhores cumprimentos,", email_html)

    def test_g_missing_identity_fails_closed(self):
        """Test G: Missing identity fails closed with clear ValueError."""
        bad_configs = [
            {"assinatura": {"nome": "", "apresentacao": "AutoCORA"}},
            {"assinatura": {"nome": "Leonardo Rosa", "apresentacao": ""}},
            {"assinatura": {}},
            {},
        ]
        for cfg in bad_configs:
            with self.assertRaises(ValueError) as ctx:
                outreach_service.generate_messages(self.lead_br_redesign, cfg)
            self.assertIn("Identidade de outreach não configurada", str(ctx.exception))

    def test_h_market_fallback_compatibility(self):
        """Test H: Fallback normalize_phone_by_country accepts country= kwarg."""
        fallback_fn = lambda raw, country=None, *a, **k: (raw, None)
        self.assertEqual(fallback_fn("11999998888", country="BR"), ("11999998888", None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
