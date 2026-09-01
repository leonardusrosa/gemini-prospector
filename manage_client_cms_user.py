#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Operator CLI Tool for Prospector Client CMS.
Provides secure tenant user management, credentials setup, password resets,
and recovery email administration without logging or committing secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
MODULE_DIR = HERE / "prospector-de-sites" if (HERE / "prospector-de-sites").exists() else HERE
sys.path.insert(0, str(MODULE_DIR))

from client_cms_auth import TenantAuthStore


def get_store(root_dir: pathlib.Path) -> TenantAuthStore:
    return TenantAuthStore(root_dir=root_dir)


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + "***" + user[-1]
    return f"{masked_user}@{domain}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Prospector Client CMS Operator Tool")
    parser.add_argument("--root", default=str(HERE), help="Root directory containing .prospector-editor")
    subparsers = parser.add_subparsers(dest="action", required=True)

    # register
    p_reg = subparsers.add_parser("register", help="Register or update tenant credentials")
    p_reg.add_argument("slug", help="Tenant slug")
    p_reg.add_argument("username", nargs="?", default="admin", help="Tenant admin username (default: admin)")
    p_reg.add_argument("password", nargs="?", default="admin12345678", help="Tenant admin password (default: admin12345678)")
    p_reg.add_argument("--display-name", default="", help="Display name for client")
    p_reg.add_argument("--email", default="", help="Recovery email")

    # reset-password
    p_reset = subparsers.add_parser("reset-password", help="Force reset tenant password (operator fallback)")
    p_reset.add_argument("slug", help="Tenant slug")
    p_reset.add_argument("--password", default="admin12345678", help="New password (default: admin12345678)")

    # set-email
    p_email = subparsers.add_parser("set-email", help="Configure recovery email for tenant")
    p_email.add_argument("slug", help="Tenant slug")
    p_email.add_argument("email", help="Recovery email address")

    # list
    subparsers.add_parser("list", help="List all registered tenant accounts")

    # info
    p_info = subparsers.add_parser("info", help="Get tenant status and credential version")
    p_info.add_argument("slug", help="Tenant slug")

    args = parser.parse_args()
    root_path = pathlib.Path(args.root).resolve()
    store = get_store(root_path)

    if args.action == "register":
        store.register_tenant(
            slug=args.slug,
            username=args.username,
            password=args.password,
            display_name=args.display_name,
            recovery_email=args.email,
        )
        print(f"[OK] Tenant '{args.slug}' registered successfully (Username: {args.username}).")
        return 0

    if args.action == "reset-password":
        try:
            user, pwd = store.force_reset_password(slug=args.slug, new_password=args.password or None, actor="operator_cli")
            print(f"[OK] Password reset for tenant '{args.slug}'.")
            print(f"Username: {user}")
            print(f"New Password: {pwd}")
            print("[NOTE] All prior active sessions for this tenant have been invalidated.")
            return 0
        except Exception as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1

    if args.action == "set-email":
        ok = store.set_recovery_email(slug=args.slug, email=args.email, actor="operator_cli")
        if ok:
            print(f"[OK] Recovery email for '{args.slug}' set to: {mask_email(args.email)}")
            return 0
        print(f"[ERROR] Tenant '{args.slug}' not found.", file=sys.stderr)
        return 1

    if args.action == "list":
        users = store._load_users()
        print(f"Registered Tenants ({len(users)}):")
        for s, info in users.items():
            email = mask_email(info.get("recoveryEmail", "")) or "[not configured]"
            print(f" - Slug: {s} | User: {info.get('username')} | Version: {info.get('credentialVersion', 1)} | Email: {email}")
        return 0

    if args.action == "info":
        users = store._load_users()
        info = users.get(args.slug)
        if not info:
            print(f"[ERROR] Tenant '{args.slug}' not found.", file=sys.stderr)
            return 1
        email = mask_email(info.get("recoveryEmail", "")) or "[not configured]"
        print(f"Tenant: {args.slug}")
        print(f"Display Name: {info.get('displayName', args.slug)}")
        print(f"Username: {info.get('username')}")
        print(f"Credential Version: {info.get('credentialVersion', 1)}")
        print(f"Recovery Email: {email}")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
