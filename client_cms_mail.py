#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prospector Client CMS — Mail Delivery Service.
Provides SMTP transport abstraction for transactional security emails.
Reads configuration strictly from private environment variables.
"""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional, Tuple


class CmsMailService:
    def __init__(self):
        self.host = os.environ.get("PROSPECTOR_CMS_SMTP_HOST", "").strip()
        self.port = int(os.environ.get("PROSPECTOR_CMS_SMTP_PORT", "587"))
        self.user = os.environ.get("PROSPECTOR_CMS_SMTP_USERNAME", "").strip()
        self.password = os.environ.get("PROSPECTOR_CMS_SMTP_PASSWORD", "").strip()
        self.mail_from = os.environ.get("PROSPECTOR_CMS_MAIL_FROM", "").strip() or "noreply@autocora.com.br"
        self.mock_outbox: list[Dict[str, Any]] = []

    def is_configured(self) -> bool:
        return bool(self.host and self.user and self.password)

    def send_reset_email(self, to_email: str, slug: str, display_name: str, reset_url: str) -> Tuple[bool, str]:
        """Sends password reset email or records in mock outbox if not configured."""
        subject = f"Redefinição de senha — Painel do Cliente ({display_name or slug})"
        plain_text = (
            f"Olá,\n\n"
            f"Recebemos uma solicitação de redefinição de senha para o painel do site '{display_name or slug}'.\n\n"
            f"Para definir uma nova senha, acesse o link abaixo (válido por 30 minutos):\n"
            f"{reset_url}\n\n"
            f"Se você não solicitou esta alteração, desconsidere este e-mail. Nenhuma ação é necessária.\n\n"
            f"AutoCORA Client CMS"
        )
        html_text = f"""<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #1e293b; line-height: 1.6; max-width: 540px; margin: 0 auto; padding: 24px;">
  <div style="border-bottom: 2px solid #0f766e; padding-bottom: 12px; margin-bottom: 20px;">
    <h2 style="color: #0f766e; margin: 0; font-size: 20px;">AutoCORA Client CMS</h2>
  </div>
  <p>Olá,</p>
  <p>Recebemos uma solicitação de redefinição de senha para o painel do site <strong>{display_name or slug}</strong>.</p>
  <p style="margin: 28px 0;">
    <a href="{reset_url}" style="background-color: #0f766e; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Redefinir minha senha</a>
  </p>
  <p style="font-size: 13px; color: #64748b;">Este link é seguro e expira em 30 minutos. Se o botão acima não funcionar, copie e cole o link no seu navegador:<br><a href="{reset_url}" style="color: #0f766e;">{reset_url}</a></p>
  <p style="font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 16px; margin-top: 32px;">Se você não solicitou esta alteração, nenhuma ação é necessária.</p>
</body>
</html>"""

        if not self.is_configured():
            self.mock_outbox.append({
                "to": to_email,
                "slug": slug,
                "subject": subject,
                "resetUrl": reset_url,
            })
            return True, "MOCK_DISPATCHED"

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.mail_from
            msg["To"] = to_email
            msg.attach(MIMEText(plain_text, "plain", "utf-8"))
            msg.attach(MIMEText(html_text, "html", "utf-8"))

            if self.port == 465:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=15) as server:
                    server.login(self.user, self.password)
                    server.sendmail(self.mail_from, [to_email], msg.as_string())
            else:
                with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(self.user, self.password)
                    server.sendmail(self.mail_from, [to_email], msg.as_string())
            return True, "SENT_SMTP"
        except Exception as exc:
            return False, f"SMTP_ERROR: {exc}"
