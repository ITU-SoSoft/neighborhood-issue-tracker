"""SMS service for sending notifications via Twilio."""

import logging

from twilio.rest import Client

from app.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS messages via Twilio."""

    def __init__(self) -> None:
        """Initialize the SMS service."""
        self._client: Client | None = None
        if settings.twilio_enabled:
            self._client = Client(
                settings.twilio_account_sid,
                settings.twilio_auth_token,
            )

    async def send_otp(self, phone_number: str, code: str) -> bool:
        """Send OTP code via SMS.

        Args:
            phone_number: The recipient phone number.
            code: The OTP code to send.

        Returns:
            True if the SMS was sent successfully, False otherwise.
        """
        message = f"SoSoft dogrulama kodunuz: {code}. Bu kod 5 dakika gecerlidir."
        return await self.send_sms(phone_number, message)

    async def send_ticket_status_update(
        self,
        phone_number: str,
        ticket_id: str,
        new_status: str,
    ) -> bool:
        """Send ticket status update notification.

        Args:
            phone_number: The recipient phone number.
            ticket_id: The ticket ID.
            new_status: The new ticket status.

        Returns:
            True if the SMS was sent successfully, False otherwise.
        """
        status_messages = {
            "in_progress": "islem altina alindi",
            "resolved": "cozumlendi",
            "closed": "kapatildi",
            "escalated": "yoneticiye iletildi",
        }
        status_text = status_messages.get(new_status, new_status)
        message = f"SoSoft: #{ticket_id[:8]} numarali bildiriminiz {status_text}."
        return await self.send_sms(phone_number, message)

    async def send_sms(self, phone_number: str, message: str) -> bool:
        """Send an SMS message.

        Args:
            phone_number: The recipient phone number.
            message: The message to send.

        Returns:
            True if the SMS was sent successfully, False otherwise.
        """
        if not settings.twilio_enabled:
            logger.info(f"SMS (disabled): {phone_number} - {message}")
            return True

        if self._client is None:
            logger.error("Twilio client not initialized")
            return False

        try:
            self._client.messages.create(
                body=message,
                from_=settings.twilio_phone_number,
                to=phone_number,
            )
            logger.info(f"SMS sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return False


# Singleton instance
sms_service = SMSService()
