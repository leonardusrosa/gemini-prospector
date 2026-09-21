#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import tempfile
import unittest

from client_cms_auth import (
    CURRENT_PASSWORD_ITERATIONS,
    TenantAuthStore,
    verify_password,
)


class ClientCmsCredentialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.store = TenantAuthStore(self.root, secret_key="test-secret-" + ("x" * 40))

    def tearDown(self):
        self.tmp.cleanup()

    def test_provision_generates_unique_one_time_password_and_stores_hash_only(self):
        username, password = self.store.register_tenant(
            "dallas-detailing-and-buffing",
            username="admin",
            display_name="Dallas Detailing And Buffing",
        )
        self.assertEqual(username, "admin")
        self.assertGreaterEqual(len(password), 20)
        self.assertNotEqual(password, "admin12345678")

        raw = (self.root / ".prospector-editor" / "auth.json").read_text(encoding="utf-8")
        self.assertNotIn(password, raw)
        data = json.loads(raw)["dallas-detailing-and-buffing"]
        self.assertEqual(data["passwordIterations"], CURRENT_PASSWORD_ITERATIONS)
        self.assertTrue(
            verify_password(password, data["hash"], data["salt"], data["passwordIterations"])
        )

    def test_username_change_removes_admin_alias_and_invalidates_sessions(self):
        _, password = self.store.register_tenant("tenant-a")
        ok, token, _ = self.store.authenticate("tenant-a", "admin", password)
        self.assertTrue(ok)
        self.assertIsNotNone(token)

        before = self.store.get_tenant_summary("tenant-a")
        after = self.store.update_tenant_profile("tenant-a", username="owner")
        self.assertGreater(after["credentialVersion"], before["credentialVersion"])

        ok, _, _ = self.store.authenticate("tenant-a", "admin", password)
        self.assertFalse(ok)
        ok, _, _ = self.store.authenticate("tenant-a", "owner", password)
        self.assertTrue(ok)

        authorized, _, _ = self.store.authorize_request(token or "", "tenant-a")
        self.assertFalse(authorized)

    def test_operator_reset_generates_new_random_password(self):
        _, old_password = self.store.register_tenant("tenant-b")
        username, new_password = self.store.force_reset_password("tenant-b")
        self.assertEqual(username, "admin")
        self.assertNotEqual(old_password, new_password)
        self.assertNotEqual(new_password, "admin12345678")
        ok, _, _ = self.store.authenticate("tenant-b", "admin", old_password)
        self.assertFalse(ok)
        ok, _, _ = self.store.authenticate("tenant-b", "admin", new_password)
        self.assertTrue(ok)

    def test_reset_link_stores_hash_not_raw_token(self):
        self.store.register_tenant("tenant-c")
        reset_url = self.store.create_operator_reset_link(
            "tenant-c", "https://cms.example.test"
        )
        raw_token = reset_url.split("#token=", 1)[1]
        raw_store = (self.root / ".prospector-editor" / "reset_tokens.json").read_text(encoding="utf-8")
        self.assertNotIn(raw_token, raw_store)
        self.assertIn("/clientes/tenant-c/admin/reset/#token=", reset_url)


if __name__ == "__main__":
    unittest.main()
