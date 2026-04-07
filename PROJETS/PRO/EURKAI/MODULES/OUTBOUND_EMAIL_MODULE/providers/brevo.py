"""
OUTBOUND_EMAIL_MODULE — Brevo Provider
Uses Brevo SMTP relay + REST API.
Config via env vars: BREVO_API_KEY, BREVO_SMTP_HOST, BREVO_SMTP_PORT
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests

from ..models import DnsStatus, SendingMailboxDB
from .base import AbstractEmailProvider

log = logging.getLogger("oem.brevo")

BREVO_API_BASE = "https://api.brevo.com/v3"


class BrevoProvider(AbstractEmailProvider):
    """
    Send emails via Brevo SMTP relay.
    Domain authentication check via Brevo REST API.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
    ):
        self.api_key   = api_key   or os.getenv("BREVO_API_KEY", "")
        self.smtp_host = smtp_host or os.getenv("BREVO_SMTP_HOST", "smtp-relay.brevo.com")
        self.smtp_port = smtp_port or int(os.getenv("BREVO_SMTP_PORT", "587"))

        if not self.api_key:
            raise ValueError("BREVO_API_KEY is required")

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _api_headers(self) -> dict:
        return {"api-key": self.api_key, "Content-Type": "application/json"}

    def _smtp_credentials(self, mailbox: SendingMailboxDB) -> tuple[str, str]:
        """Return (username, password) for SMTP auth."""
        username = mailbox.username or mailbox.email
        # password_enc stored as plaintext in this implementation
        # (encryption/decryption layer is responsibility of the consumer)
        password = mailbox.password_enc or ""
        return username, password

    # ── AbstractEmailProvider ──────────────────────────────────────────────────

    def send(
        self,
        mailbox: SendingMailboxDB,
        delivery_id: str,
        prospect_id: str,
        sequence_step_id: str,
        to_email: str,
        to_name: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[dict] = None,
        tracking_opens: bool = True,
        tracking_clicks: bool = True,
    ) -> dict:
        """Send via Brevo SMTP relay using mailbox credentials."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{mailbox.local_part} <{mailbox.email}>"
            msg["To"]      = f"{to_name} <{to_email}>" if to_name else to_email

            # Custom headers (delivery tracking, unsubscribe, etc.)
            extra_headers = headers or {}
            extra_headers["X-OEM-Delivery-ID"] = delivery_id
            for k, v in extra_headers.items():
                msg[k] = v

            if reply_to:
                msg["Reply-To"] = reply_to

            if body_text:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))
            if body_html:
                msg.attach(MIMEText(body_html, "html", "utf-8"))

            username, password = self._smtp_credentials(mailbox)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(username, password)
                smtp.sendmail(mailbox.email, to_email, msg.as_string())

            log.info("Sent via Brevo SMTP: %s → %s (delivery=%s)", mailbox.email, to_email, delivery_id)
            return {"success": True, "message_id": f"brevo-smtp-{delivery_id}"}

        except smtplib.SMTPAuthenticationError as e:
            log.error("SMTP auth failed for %s: %s", mailbox.email, e)
            return {"success": False, "error": f"SMTP auth failed: {e}", "code": "auth_error"}
        except smtplib.SMTPRecipientsRefused as e:
            log.warning("Recipient refused %s: %s", to_email, e)
            return {"success": False, "error": f"Recipient refused: {e}", "code": "bounce_hard"}
        except Exception as e:
            log.exception("Brevo send error: %s", e)
            return {"success": False, "error": str(e), "code": "unknown"}

    def send_via_api(
        self,
        from_email: str,
        from_name: str,
        to_email: str,
        to_name: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        reply_to: Optional[str] = None,
        delivery_id: Optional[str] = None,
    ) -> dict:
        """Alternative: send via Brevo transactional API (no SMTP)."""
        payload = {
            "sender": {"email": from_email, "name": from_name},
            "to": [{"email": to_email, "name": to_name}],
            "subject": subject,
            "htmlContent": body_html,
        }
        if body_text:
            payload["textContent"] = body_text
        if reply_to:
            payload["replyTo"] = {"email": reply_to}
        if delivery_id:
            payload["headers"] = {"X-OEM-Delivery-ID": delivery_id}

        resp = requests.post(
            f"{BREVO_API_BASE}/smtp/email",
            json=payload,
            headers=self._api_headers(),
            timeout=15,
        )
        if resp.status_code in (200, 201):
            return {"success": True, "message_id": resp.json().get("messageId", "")}
        return {"success": False, "error": resp.text, "code": str(resp.status_code)}

    def validate_domain(self, domain_name: str) -> dict:
        """
        Check domain authentication status via Brevo API.
        Brevo does not expose a manual trigger — this reads current status.
        """
        resp = requests.get(
            f"{BREVO_API_BASE}/senders/domains",
            headers=self._api_headers(),
            timeout=10,
        )
        if resp.status_code != 200:
            return {"success": False, "error": resp.text}

        domains = resp.json().get("domains", [])
        for d in domains:
            if d.get("domain_name") == domain_name or d.get("name") == domain_name:
                spf   = DnsStatus.valid if d.get("spf_verified")  else DnsStatus.invalid
                dkim  = DnsStatus.valid if d.get("dkim_verified") else DnsStatus.invalid
                dmarc = DnsStatus.valid if d.get("dmarc_configured") else DnsStatus.unknown
                return {
                    "success": True,
                    "spf": spf,
                    "dkim": dkim,
                    "dmarc": dmarc,
                    "raw": d,
                }
        return {"success": False, "error": f"Domain {domain_name} not found in Brevo"}

    def get_sending_stats(self, mailbox_email: str, window_hours: int = 24) -> dict:
        """Fetch aggregate stats from Brevo (email activity log)."""
        from datetime import datetime, timedelta, timezone
        start = (datetime.now(timezone.utc) - timedelta(hours=window_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")

        resp = requests.get(
            f"{BREVO_API_BASE}/smtp/statistics/aggregatedReport",
            params={"startDate": start[:10], "tag": mailbox_email},
            headers=self._api_headers(),
            timeout=10,
        )
        if resp.status_code != 200:
            log.warning("Brevo stats API error: %s", resp.text)
            return {"sent": 0, "bounced": 0, "opened": 0, "clicked": 0}

        data = resp.json()
        return {
            "sent":    data.get("delivered", 0),
            "bounced": data.get("hardBounces", 0) + data.get("softBounces", 0),
            "opened":  data.get("uniqueOpens", 0),
            "clicked": data.get("uniqueClicks", 0),
        }

    def list_senders(self) -> list[dict]:
        """List all verified senders in Brevo account."""
        resp = requests.get(f"{BREVO_API_BASE}/senders", headers=self._api_headers(), timeout=10)
        if resp.status_code != 200:
            return []
        return resp.json().get("senders", [])

    def create_sender(self, email: str, name: str) -> dict:
        """Add a new sender to Brevo account."""
        resp = requests.post(
            f"{BREVO_API_BASE}/senders",
            json={"email": email, "name": name},
            headers=self._api_headers(),
            timeout=10,
        )
        return {"success": resp.status_code in (200, 201), "status": resp.status_code, "body": resp.json()}

    def name(self) -> str:
        return "brevo"
