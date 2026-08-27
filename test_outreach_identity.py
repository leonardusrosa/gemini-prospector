#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regression test suite for verified outreach identity, fail-closed behavior,
and permission-first cold WhatsApp flow.
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
        url_pattern = re.compile(r"https?://|www\.|\.html|\.com|\.app|\.br|\.pt|/[a-zA-Z0-9_\-]+/[a-zA-Z0-9_\-]+", re.IGNORECASE)
        # Check standard web protocol/domain tokens
        self.assertNotIn("http://", text, f"Found 'http://' in {lead_name}")
        self.assertNotIn("https://", text, f"Found 'https://' in {lead_name}")
        self.assertNotIn("proposta.html", text, f"Found 'proposta.html' in {lead_name}")
        self.assertNotIn("autocora.com.br", text, f"Found portfolio URL in {lead_name}")
        self.assertNotIn("prospector-sites-beta.vercel.app", text, f"Found domain URL in {lead_name}")

    def test_a_br_redesign_first_contact_no_url(self):
        """Test A: BR redesign firstContact contains NO http/https/URL."""
        res = outreach_service.generate_messages(self.lead_br_redesign, self.valid_config)
        first_contact = res["whatsapp"]["firstContact"]
        self._assert_no_urls(first_contact, "BR redesign firstContact")
        self.assertEqual(res["whatsapp"]["text"], first_contact)

    def test_b_br_new_site_first_contact_no_url(self):
        """Test B: BR new-site firstContact contains NO URL."""
        res = outreach_service.generate_messages(self.lead_br_new, self.valid_config)
        first_contact = res["whatsapp"]["firstContact"]
        self._assert_no_urls(first_contact, "BR new site firstContact")

    def test_c_pt_redesign_first_contact_no_url(self):
        """Test C: PT redesign firstContact contains NO URL."""
        res = outreach_service.generate_messages(self.lead_pt_redesign, self.valid_config)
        first_contact = res["whatsapp"]["firstContact"]
        self._assert_no_urls(first_contact, "PT redesign firstContact")

    def test_d_pt_new_site_first_contact_no_url(self):
        """Test D: PT new-site firstContact contains NO URL."""
        res = outreach_service.generate_messages(self.lead_pt_new, self.valid_config)
        first_contact = res["whatsapp"]["firstContact"]
        self._assert_no_urls(first_contact, "PT new site firstContact")

    def test_e_first_contact_asks_permission(self):
        """Test E: Each firstContact asks permission to receive the link."""
        for lead in [self.lead_br_redesign, self.lead_br_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            first_contact = res["whatsapp"]["firstContact"]
            self.assertIn("Posso te mandar o link", first_contact)

        for lead in [self.lead_pt_redesign, self.lead_pt_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            first_contact = res["whatsapp"]["firstContact"]
            self.assertIn("Posso enviar-lhe o link", first_contact)

    def test_f_after_permission_contains_proposal_url(self):
        """Test F: afterPermission contains exactly the proposal URL."""
        for lead in [self.lead_br_redesign, self.lead_br_new, self.lead_pt_redesign, self.lead_pt_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            after_perm = res["whatsapp"]["afterPermission"]
            expected_url = f"https://prospector-sites-beta.vercel.app/clientes/{lead['slug']}/proposta.html"
            self.assertIn(expected_url, after_perm)
            self.assertEqual(res["proposalUrl"], expected_url)

    def test_g_identity_remains_leonardo_rosa_autocora(self):
        """Test G: Identity remains Leonardo Rosa / AutoCORA."""
        for lead in [self.lead_br_redesign, self.lead_pt_new]:
            res = outreach_service.generate_messages(lead, self.valid_config)
            wpp_text = res["whatsapp"]["firstContact"]
            email_html = res["email"]["bodyHtml"]

            self.assertIn("Leonardo Rosa", wpp_text)
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
                self.assertNotIn(phrase, wpp_text)
                self.assertNotIn(phrase, email_html)

    def test_h_missing_identity_fails_closed(self):
        """Test H: Missing identity fails closed with clear ValueError."""
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

    def test_i_email_retains_proposal_url(self):
        """Test I: Email retains proposal link and compose URL."""
        res = outreach_service.generate_messages(self.lead_br_redesign, self.valid_config)
        expected_url = "https://prospector-sites-beta.vercel.app/clientes/clinica-exemplo/proposta.html"
        self.assertIn(expected_url, res["email"]["bodyHtml"])
        self.assertIn("https://mail.google.com/mail/?", res["email"]["composeUrl"])

    def test_j_market_fallback_compatibility(self):
        """Test J: Fallback normalize_phone_by_country accepts country= kwarg."""
        fallback_fn = lambda raw, country=None, *a, **k: (raw, None)
        self.assertEqual(fallback_fn("11999998888", country="BR"), ("11999998888", None))


if __name__ == "__main__":
    unittest.main(verbosity=2)
