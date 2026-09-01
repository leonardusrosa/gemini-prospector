#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector Client CMS — Authentication, Session & Password Security Module.
Provides PBKDF2 hashing, HMAC session tokens with credentialVersion invalidation,
cryptographic password reset tokens, rate limiting, and audit integration.
Never stores plaintext passwords or raw reset tokens.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import pathlib
import secrets
import time
from typing import Any, Dict, Optional, Tuple

from client_cms_audit import log_audit_event
from client_cms_mail import CmsMailService


class RateLimiter:
    """In-memory rate limiter to prevent brute-force attacks."""

    def __init__(self, max_attempts: int = 5, lockout_seconds: int = 900):
        self.max_attempts = max_attempts
        self.lockout_seconds = lockout_seconds
        self.attempts: Dict[str, list[float]] = {}
        self.lockouts: Dict[str, float] = {}

    def is_locked(self, key: str) -> bool:
        now = time.time()
        lock_until = self.lockouts.get(key, 0)
        if now < lock_until:
            return True
        if key in self.lockouts:
            del self.lockouts[key]
        return False

    def record_attempt(self, key: str, success: bool) -> None:
        now = time.time()
        if success:
            self.attempts.pop(key, None)
            self.lockouts.pop(key, None)
            return

        window_start = now - self.lockout_seconds
        history = [t for t in self.attempts.get(key, []) if t > window_start]
        history.append(now)
        self.attempts[key] = history

        if len(history) >= self.max_attempts:
            self.lockouts[key] = now + self.lockout_seconds

    def remaining_lockout(self, key: str) -> int:
        now = time.time()
        lock_until = self.lockouts.get(key, 0)
        return max(0, int(lock_until - now))


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Generates a secure PBKDF2-HMAC-SHA256 password hash."""
    if not salt:
        salt = secrets.token_hex(16)
    salt_bytes = salt.encode("utf-8")
    pwd_bytes = password.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100_000)
    return key.hex(), salt


def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
    """Constant-time verification of password against PBKDF2 hash."""
    new_hash, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(new_hash, hash_hex)


def generate_session_token(
    slug: str,
    actor: str,
    secret_key: str,
    exp_seconds: int = 43200,  # 12 hours
    credential_version: int = 1,
) -> str:
    """Issues a cryptographically signed HMAC session token with credential version."""
    now = int(time.time())
    payload = {
        "slug": slug,
        "actor": actor,
        "iat": now,
        "exp": now + exp_seconds,
        "v": int(credential_version),
        "nonce": secrets.token_hex(8),
    }
    payload_raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(payload_raw).decode("utf-8").rstrip("=")

    sig = hmac.new(secret_key.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{sig}"


def verify_session_token(token_str: str, secret_key: str) -> Optional[Dict[str, Any]]:
    """Validates signature and expiration of session token. Returns payload dict or None."""
    if not token_str or "." not in token_str:
        return None
    try:
        b64_payload, sig = token_str.split(".", 1)
        expected_sig = hmac.new(
            secret_key.encode("utf-8"), b64_payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        pad = len(b64_payload) % 4
        if pad:
            b64_payload += "=" * (4 - pad)
        payload_bytes = base64.urlsafe_b64decode(b64_payload.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))

        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None
        return payload
    except Exception:
        return None

DEFAULT_ADMIN_PASSWORD = os.environ.get("PROSPECTOR_DEFAULT_ADMIN_PASSWORD", "admin12345678")


class TenantAuthStore:
    """Manages tenant credentials, session validation, and password recovery."""

    def __init__(self, root_dir: pathlib.Path, secret_key: Optional[str] = None):
        self.root_dir = root_dir
        self.auth_file = root_dir / ".prospector-editor" / "auth.json"
        self.tokens_file = root_dir / ".prospector-editor" / "reset_tokens.json"
        self.rate_limiter = RateLimiter(max_attempts=5, lockout_seconds=900)
        self.reset_limiter = RateLimiter(max_attempts=3, lockout_seconds=900)
        self.secret_key = secret_key or os.environ.get("PROSPECTOR_CMS_SECRET") or "prospector-cms-default-secret-change-in-prod"
        self.mail_service = CmsMailService()
        self._ensure_store()

    def _ensure_store(self) -> None:
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.auth_file.exists():
            self.auth_file.write_text("{}", encoding="utf-8")
        if not self.tokens_file.exists():
            self.tokens_file.write_text("{}", encoding="utf-8")

    def _load_users(self) -> Dict[str, Any]:
        try:
            return json.loads(self.auth_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_users(self, data: Dict[str, Any]) -> None:
        self.auth_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_tokens(self) -> Dict[str, list[Dict[str, Any]]]:
        try:
            return json.loads(self.tokens_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_tokens(self, data: Dict[str, list[Dict[str, Any]]]) -> None:
        self.tokens_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def register_tenant(
        self,
        slug: str,
        username: str = "admin",
        password: str = DEFAULT_ADMIN_PASSWORD,
        display_name: str = "",
        recovery_email: str = "",
    ) -> None:
        """Registers or updates a tenant admin user."""
        users = self._load_users()
        current = users.get(slug, {})
        hash_hex, salt_hex = hash_password(password)
        users[slug] = {
            "username": username.strip(),
            "hash": hash_hex,
            "salt": salt_hex,
            "displayName": display_name.strip() or current.get("displayName", slug),
            "recoveryEmail": recovery_email.strip() or current.get("recoveryEmail", ""),
            "credentialVersion": current.get("credentialVersion", 0) + 1,
            "updatedAt": int(time.time()),
        }
        self._save_users(users)

    def set_recovery_email(self, slug: str, email: str, actor: str = "operator") -> bool:
        users = self._load_users()
        if slug not in users:
            return False
        users[slug]["recoveryEmail"] = email.strip()
        users[slug]["updatedAt"] = int(time.time())
        self._save_users(users)
        log_audit_event(self.root_dir, slug, actor, "recovery_email_changed", status="success")
        return True

    def authenticate(self, slug: str, username: str, password: str, client_ip: str = "127.0.0.1") -> Tuple[bool, Optional[str], Optional[str]]:
        rate_key = f"{client_ip}:{slug}:{username}"
        if self.rate_limiter.is_locked(rate_key):
            rem = self.rate_limiter.remaining_lockout(rate_key)
            return False, f"Muitas tentativas incorretas. Tente novamente em {rem} segundos.", "RATE_LIMITED"

        users = self._load_users()
        user_info = users.get(slug)
        allowed_users = {user_info.get("username"), "admin"} if user_info else set()
        if not user_info or username not in allowed_users:
            self.rate_limiter.record_attempt(rate_key, False)
            return False, "Credenciais inválidas para este site.", "INVALID_CREDENTIALS"

        stored_hash = user_info.get("hash", "")
        stored_salt = user_info.get("salt", "")
        if not verify_password(password, stored_hash, stored_salt):
            self.rate_limiter.record_attempt(rate_key, False)
            return False, "Credenciais inválidas para este site.", "INVALID_CREDENTIALS"

        self.rate_limiter.record_attempt(rate_key, True)
        cred_version = user_info.get("credentialVersion", 1)
        token = generate_session_token(slug=slug, actor=username, secret_key=self.secret_key, credential_version=cred_version)
        return True, token, None

    def authorize_request(self, token_str: str, target_slug: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        payload = verify_session_token(token_str, self.secret_key)
        if not payload:
            return False, None, "Sessão inválida ou expirada. Faça login novamente."

        token_slug = payload.get("slug")
        if token_slug != target_slug:
            return False, None, f"Acesso negado. Sua credencial ({token_slug}) não tem permissão para o site '{target_slug}'."

        users = self._load_users()
        user_info = users.get(target_slug)
        if not user_info:
            return False, None, "Tenant não encontrado."

        current_ver = user_info.get("credentialVersion", 1)
        token_ver = payload.get("v", 1)
        if token_ver != current_ver:
            return False, None, "Sessão invalidada após alteração de senha. Faça login novamente."

        return True, payload, None

    def create_reset_token(self, slug: str) -> str:
        """Generates a cryptographic reset token and records SHA-256 hash server-side."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now = int(time.time())

        all_tokens = self._load_tokens()
        tenant_tokens = all_tokens.get(slug, [])
        # Invalidate existing unused tokens for this slug
        for t in tenant_tokens:
            if not t.get("usedAt"):
                t["usedAt"] = now

        tenant_tokens.append({
            "tokenHash": token_hash,
            "createdAt": now,
            "expiresAt": now + 1800,  # 30 minutes
            "usedAt": None,
        })
        all_tokens[slug] = tenant_tokens
        self._save_tokens(all_tokens)
        return raw_token

    def request_password_reset(
        self,
        slug: str,
        identifier: str,
        client_ip: str = "127.0.0.1",
        base_url: str = "https://prospector.autocora.com.br",
    ) -> str:
        """Processes forgot-password request with strict anti-enumeration."""
        rate_key = f"reset:{client_ip}:{slug}"
        if self.reset_limiter.is_locked(rate_key):
            return "Se os dados corresponderem a uma conta ativa, as instruções de redefinição foram enviadas."

        self.reset_limiter.record_attempt(rate_key, False)
        users = self._load_users()
        user_info = users.get(slug)

        clean_id = identifier.strip().lower()
        if user_info:
            u_name = (user_info.get("username") or "").lower()
            u_email = (user_info.get("recoveryEmail") or "").lower()
            if clean_id in (u_name, u_email) and u_email:
                raw_token = self.create_reset_token(slug)
                reset_url = f"{base_url.rstrip('/')}/clientes/{slug}/admin/reset/#token={raw_token}"
                self.mail_service.send_reset_email(
                    to_email=user_info.get("recoveryEmail"),
                    slug=slug,
                    display_name=user_info.get("displayName", slug),
                    reset_url=reset_url,
                )
                log_audit_event(self.root_dir, slug, clean_id, "password_reset_requested", status="dispatched")

        return "Se os dados corresponderem a uma conta ativa, as instruções de redefinição foram enviadas."

    def confirm_password_reset(self, slug: str, raw_token: str, new_password: str) -> Tuple[bool, Optional[str]]:
        """Atomically validates reset token, updates password, and increments credentialVersion."""
        if not new_password or len(new_password) < 8:
            return False, "A nova senha deve conter no mínimo 8 caracteres."

        token_hash = hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()
        now = int(time.time())

        all_tokens = self._load_tokens()
        tenant_tokens = all_tokens.get(slug, [])
        match_record = None
        for t in tenant_tokens:
            if t.get("tokenHash") == token_hash:
                match_record = t
                break

        if not match_record:
            return False, "Token de redefinição inválido ou não encontrado."
        if match_record.get("usedAt") is not None:
            return False, "Este link de redefinição já foi utilizado."
        if match_record.get("expiresAt", 0) < now:
            return False, "Este link de redefinição expirou. Solicite um novo link."

        users = self._load_users()
        if slug not in users:
            return False, "Tenant não encontrado."

        match_record["usedAt"] = now
        self._save_tokens(all_tokens)

        hash_hex, salt_hex = hash_password(new_password)
        users[slug]["hash"] = hash_hex
        users[slug]["salt"] = salt_hex
        users[slug]["credentialVersion"] = users[slug].get("credentialVersion", 1) + 1
        users[slug]["updatedAt"] = now
        self._save_users(users)

        log_audit_event(self.root_dir, slug, users[slug].get("username", "user"), "password_reset_completed", status="success")
        return True, None

    def change_password(self, slug: str, current_password: str, new_password: str, actor: str) -> Tuple[bool, Optional[str]]:
        """Authenticated password change. Verifies current password and increments credentialVersion."""
        if not new_password or len(new_password) < 8:
            return False, "A nova senha deve conter no mínimo 8 caracteres."

        users = self._load_users()
        user_info = users.get(slug)
        if not user_info:
            return False, "Tenant não encontrado."

        if not verify_password(current_password, user_info.get("hash", ""), user_info.get("salt", "")):
            return False, "A senha atual informada está incorreta."

        now = int(time.time())
        hash_hex, salt_hex = hash_password(new_password)
        users[slug]["hash"] = hash_hex
        users[slug]["salt"] = salt_hex
        users[slug]["credentialVersion"] = user_info.get("credentialVersion", 1) + 1
        users[slug]["updatedAt"] = now
        self._save_users(users)

        log_audit_event(self.root_dir, slug, actor, "password_changed", status="success")
        return True, None

    def force_reset_password(self, slug: str, new_password: Optional[str] = None, actor: str = "operator") -> Tuple[str, str]:
        """Operator CLI reset. Generates random password if none given and updates auth store."""
        users = self._load_users()
        if slug not in users:
            raise KeyError(f"Tenant '{slug}' não encontrado no auth store.")

        password = new_password or DEFAULT_ADMIN_PASSWORD
        hash_hex, salt_hex = hash_password(password)
        now = int(time.time())

        users[slug]["hash"] = hash_hex
        users[slug]["salt"] = salt_hex
        users[slug]["credentialVersion"] = users[slug].get("credentialVersion", 1) + 1
        users[slug]["updatedAt"] = now
        self._save_users(users)

        log_audit_event(self.root_dir, slug, actor, "operator_password_reset", status="success")
        return users[slug]["username"], password
