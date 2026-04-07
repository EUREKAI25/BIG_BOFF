"""
OUTBOUND_EMAIL_MODULE — Abstract Provider Interface
All email providers (Brevo, SES, Mailgun, etc.) must implement this.
"""
from abc import ABC, abstractmethod
from typing import Optional

from ..models import SendingMailboxDB


class AbstractEmailProvider(ABC):
    """
    Base class for email sending providers.
    Each method must return a dict with at minimum {"success": bool}.
    """

    @abstractmethod
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
        """
        Send one email.
        Returns:
          {"success": True, "message_id": "..."}
          {"success": False, "error": "...", "code": "..."}
        """
        ...

    @abstractmethod
    def validate_domain(self, domain_name: str) -> dict:
        """
        Trigger / check domain authentication (SPF, DKIM, DMARC).
        Returns:
          {"success": True, "spf": "valid", "dkim": "valid", "dmarc": "valid"}
          {"success": False, "error": "..."}
        """
        ...

    @abstractmethod
    def get_sending_stats(self, mailbox_email: str, window_hours: int = 24) -> dict:
        """
        Fetch sending stats from provider side (deliveries, bounces, opens, clicks).
        Returns:
          {"sent": int, "bounced": int, "opened": int, "clicked": int}
        """
        ...

    def name(self) -> str:
        return self.__class__.__name__
