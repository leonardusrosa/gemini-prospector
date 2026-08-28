#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector Client CMS — Authentication and Session Security Module.
Provides PBKDF2 password hashing, cryptographically signed HMAC session tokens,
rate-limiting brute force protection, and strict tenant authorization.
Never stores plaintext passwords.
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
from typing import Any, Dict, Optional, Set, Tuple


class RateLimiter:
    """In-memory rate limiter to prevent credential brute-force attacks."""

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
) -> str:
    """Issues a cryptographically signed URL-safe HMAC session token."""
    now = int(time.time())
    payload = {
        "slug": slug,
        "actor": actor,
        "iat": now,
        "exp": now + exp_seconds,
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

        # Add base64 padding
        pad = len(b64_payload) % 4
        if pad:
            b64_payload += "=" * (4 - pad)
        payload_bytes = base64.urlsafe_b64decode(b64_payload.encode("utf-8"))
        payload = json.loads(payload_bytes.decode("utf-8"))

        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None  # Expired
        return payload
    except Exception:
        return None


class TenantAuthStore:
    """Manages tenant credentials and authentication."""

    def __init__(self, root_dir: pathlib.Path, secret_key: Optional[str] = None):
        self.root_dir = root_dir
        self.auth_file = root_dir / ".prospector-editor" / "auth.json"
        self.rate_limiter = RateLimiter(max_attempts=5, lockout_seconds=900)
        self.secret_key = secret_key or os.environ.get("PROSPECTOR_CMS_SECRET") or "prospector-cms-default-secret-change-in-prod"
        self._ensure_store()

    def _ensure_store(self) -> None:
        self.auth_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.auth_file.exists():
            self.auth_file.write_text("{}", encoding="utf-8")

    def _load_users(self) -> Dict[str, Any]:
        try:
            return json.loads(self.auth_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_users(self, data: Dict[str, Any]) -> None:
        self.auth_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def register_tenant(self, slug: str, username: str, password: str, display_name: str = "") -> None:
        """Registers or updates a tenant admin user with hashed password."""
        users = self._load_users()
        hash_hex, salt_hex = hash_password(password)
        users[slug] = {
            "username": username,
            "hash": hash_hex,
            "salt": salt_hex,
            "displayName": display_name or slug,
            "updatedAt": int(time.time()),
        }
        self._save_users(users)

    def authenticate(self, slug: str, username: str, password: str, client_ip: str = "127.0.0.1") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Authenticates tenant.
        Returns (success, session_token_or_error_msg, error_code).
        """
        rate_key = f"{client_ip}:{slug}:{username}"
        if self.rate_limiter.is_locked(rate_key):
            rem = self.rate_limiter.remaining_lockout(rate_key)
            return False, f"Muitas tentativas incorretas. Tente novamente em {rem} segundos.", "RATE_LIMITED"

        users = self._load_users()
        user_info = users.get(slug)
        if not user_info:
            self.rate_limiter.record_attempt(rate_key, False)
            return False, "Credenciais inválidas para este site.", "INVALID_CREDENTIALS"

        if user_info.get("username") != username:
            self.rate_limiter.record_attempt(rate_key, False)
            return False, "Credenciais inválidas para este site.", "INVALID_CREDENTIALS"

        stored_hash = user_info.get("hash", "")
        stored_salt = user_info.get("salt", "")
        if not verify_password(password, stored_hash, stored_salt):
            self.rate_limiter.record_attempt(rate_key, False)
            return False, "Credenciais inválidas para este site.", "INVALID_CREDENTIALS"

        self.rate_limiter.record_attempt(rate_key, True)
        token = generate_session_token(slug=slug, actor=username, secret_key=self.secret_key)
        return True, token, None

    def authorize_request(self, token_str: str, target_slug: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validates token and checks authorization for specific target_slug.
        Prevents cross-tenant manipulation.
        """
        payload = verify_session_token(token_str, self.secret_key)
        if not payload:
            return False, None, "Sessão inválida ou expirada. Faça login novamente."

        token_slug = payload.get("slug")
        if token_slug != target_slug:
            return False, None, f"Acesso negado. Sua credencial ({token_slug}) não tem permissão para o site '{target_slug}'."

        return True, payload, None
