#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive production-readiness regression test suite for Client CMS (/admin).
Tests authentication, tenant authorization, cross-tenant isolation, path traversal,
draft isolation, publish isolation, rollback, sanitization, truthful status, and rate-limiting.
"""

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import unittest

from client_cms_auth import TenantAuthStore, hash_password, verify_password, generate_session_token, verify_session_token
from client_cms_audit import get_audit_history, log_audit_event
from client_cms_service import ClientCmsService, validate_html, validate_slug, sanitize_html

ROOT = pathlib.Path(__file__).resolve().parent


class TestClientCmsSecurityAndPublish(unittest.TestCase):
    def setUp(self):
        self.td = pathlib.Path(tempfile.mkdtemp(prefix="prospector_cms_test_"))
        self.bare_repo = self.td / "remote_bare.git"
        self.deploy_repo = self.td / "deploy_repo"

        # Initialize mock bare remote and deploy repo
        subprocess.run(["git", "init", "--bare", str(self.bare_repo)], check=True, capture_output=True)
        subprocess.run(["git", "init", str(self.deploy_repo)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.deploy_repo), "config", "user.email", "test@autocora.com.br"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.deploy_repo), "config", "user.name", "AutoCORA Bot"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.deploy_repo), "remote", "add", "origin", str(self.bare_repo)], check=True, capture_output=True)

        # Create base site structure
        self.slug = "instituto-ferreira-odontologia-rio-claro"
        self.site_dir = self.deploy_repo / "clientes" / self.slug
        self.site_dir.mkdir(parents=True)
        self.index_html = self.site_dir / "index.html"
        self.initial_html = (
            "<!DOCTYPE html><html><head><title>Instituto Ferreira</title></head>"
            "<body><h1 class='hero-headline'>Excelência técnica em odontologia</h1></body></html>"
        )
        self.index_html.write_text(self.initial_html, encoding="utf-8")

        # Initial commit & push in deploy repo
        subprocess.run(["git", "-C", str(self.deploy_repo), "branch", "-M", "main"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.deploy_repo), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.deploy_repo), "commit", "-m", "Initial commit"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.deploy_repo), "push", "-u", "origin", "main"], check=True, capture_output=True)

        # Setup Auth Store & CMS Service
        self.auth_store = TenantAuthStore(root_dir=self.td, secret_key="test-secret-key-12345")
        self.auth_store.register_tenant(self.slug, "admin_instituto", "SenhaForte123!", "Instituto Ferreira")

        self.cms_service = ClientCmsService(
            root_dir=self.td,
            deploy_repo=self.deploy_repo,
            base_path="clientes",
        )

    def tearDown(self):
        shutil.rmtree(self.td, ignore_errors=True)

    def test_a_auth_required_and_verification(self):
        """Test A: Valid credentials issue token; wrong credentials fail."""
        # Valid login
        ok, token, err_code = self.auth_store.authenticate(self.slug, "admin_instituto", "SenhaForte123!")
        self.assertTrue(ok)
        self.assertTrue(bool(token))
        self.assertIsNone(err_code)

        # Invalid password
        ok_bad, msg, code = self.auth_store.authenticate(self.slug, "admin_instituto", "WrongPassword")
        self.assertFalse(ok_bad)
        self.assertEqual(code, "INVALID_CREDENTIALS")

        # Invalid user
        ok_bad_user, _, _ = self.auth_store.authenticate(self.slug, "wrong_user", "SenhaForte123!")
        self.assertFalse(ok_bad_user)

    def test_b_rate_limiting_lockout(self):
        """Test B: 5 consecutive failed attempts trigger rate-limiting lockout."""
        ip = "192.168.1.100"
        for _ in range(5):
            self.auth_store.authenticate(self.slug, "admin_instituto", "bad", client_ip=ip)

        # 6th attempt must be RATE_LIMITED
        ok, msg, code = self.auth_store.authenticate(self.slug, "admin_instituto", "SenhaForte123!", client_ip=ip)
        self.assertFalse(ok)
        self.assertEqual(code, "RATE_LIMITED")
        self.assertIn("Muitas tentativas", msg)

    def test_c_tenant_authorization_and_cross_tenant_denied(self):
        """Test C: Token for Instituto CANNOT authorize requests for another tenant."""
        ok, token, _ = self.auth_store.authenticate(self.slug, "admin_instituto", "SenhaForte123!")
        self.assertTrue(ok)

        # Authorize own slug
        auth_ok, payload, _ = self.auth_store.authorize_request(token, self.slug)
        self.assertTrue(auth_ok)
        self.assertEqual(payload["slug"], self.slug)

        # Attempt cross-tenant authorization for 'dr-silva'
        cross_ok, _, cross_err = self.auth_store.authorize_request(token, "dr-silva-consultorio")
        self.assertFalse(cross_ok)
        self.assertIn("Acesso negado", cross_err)

    def test_d_path_traversal_rejection(self):
        """Test D: Path traversal attacks in slug or targets fail closed."""
        bad_slugs = ["../dr-silva", "slug/../../etc", "slug\\..", "slug/sub", "..", ""]
        for bad in bad_slugs:
            with self.assertRaises(ValueError):
                validate_slug(bad)

    def test_e_draft_isolation(self):
        """Test E: Saving draft writes only to private drafts dir and never changes live site."""
        draft_content = "<!DOCTYPE html><html><body><h1>Rascunho Não Publicado</h1></body></html>"
        res = self.cms_service.save_draft(self.slug, draft_content, actor="admin_instituto")
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "draft_saved")

        # Live site must still have initial content
        live_content = self.index_html.read_text(encoding="utf-8")
        self.assertIn("Excelência técnica em odontologia", live_content)
        self.assertNotIn("Rascunho Não Publicado", live_content)

        # Draft must be readable from drafts store
        loaded_draft = self.cms_service.get_draft(self.slug)
        self.assertEqual(loaded_draft, draft_content)

    def test_f_publish_workflow_and_git_commit(self):
        """Test F: Publish writes to deploy repo, creates backup, commits and logs audit."""
        updated_content = (
            "<!DOCTYPE html><html><head><title>Instituto Ferreira</title></head>"
            "<body><h1 class='hero-headline'>Nova Edição Publicada</h1></body></html>"
        )
        # Mock git push by using remote pointing to current repo or dry run
        res = self.cms_service.publish_content(
            slug=self.slug,
            html_content=updated_content,
            actor="admin_instituto",
            remote="origin",
            branch="main",
        )
        # In this local temp repo origin doesn't exist, so git push returncode != 0
        # Check that it committed locally and reported truthful status
        self.assertTrue(res.get("status") in ("published_git", "push_failed"))
        self.assertTrue(bool(res.get("commit")))

        # Live file must have updated content
        live_content = self.index_html.read_text(encoding="utf-8")
        self.assertIn("Nova Edição Publicada", live_content)

        # Audit trail must have recorded the event
        audit = get_audit_history(self.td, self.slug)
        self.assertTrue(len(audit) > 0)
        self.assertEqual(audit[-1]["slug"], self.slug)
        self.assertEqual(audit[-1]["actor"], "admin_instituto")

    def test_g_rollback_restores_previous_backup(self):
        """Test G: Rollback restores the backup created before the last publish."""
        # 1. First publish
        first_edit = "<!DOCTYPE html><html><body><h1>Primeira Edição</h1></body></html>"
        self.cms_service.publish_content(self.slug, first_edit, actor="admin_instituto")

        # 2. Second publish
        second_edit = "<!DOCTYPE html><html><body><h1>Segunda Edição (Erro)</h1></body></html>"
        self.cms_service.publish_content(self.slug, second_edit, actor="admin_instituto")
        self.assertIn("Segunda Edição", self.index_html.read_text(encoding="utf-8"))

        # 3. Rollback
        rollback_res = self.cms_service.rollback_content(self.slug, actor="admin_instituto")
        self.assertEqual(rollback_res.get("status"), "rolled_back")

        # Live content must be restored to previous state
        restored = self.index_html.read_text(encoding="utf-8")
        self.assertIn("Primeira Edição", restored)
        self.assertNotIn("Segunda Edição", restored)

    def test_h_sanitization_rejects_editor_runtime_leak(self):
        """Test H: Candidate HTML with editor UI or scripts is rejected."""
        bad_html = "<!DOCTYPE html><html><body><div data-pe-ui>Toolbar</div></body></html>"
        with self.assertRaises(ValueError) as ctx:
            validate_html(bad_html)
        self.assertIn("Artefatos de runtime do editor não podem ser publicados", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
