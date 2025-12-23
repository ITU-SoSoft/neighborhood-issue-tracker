"""Integration tests for SMS service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.sms import SMSService, sms_service


class TestSMSServiceIntegration:
    """Integration tests for SMS service."""

    async def test_send_otp_when_disabled(self):
        """send_otp should log and return True when twilio is disabled."""
        # Default test configuration has twilio disabled
        result = await sms_service.send_otp("+905551234567", "123456")
        assert result is True

    async def test_send_ticket_status_update_when_disabled(self):
        """send_ticket_status_update should return True when twilio is disabled."""
        result = await sms_service.send_ticket_status_update(
            "+905551234567",
            "abc12345-test-ticket-id",
            "in_progress",
        )
        assert result is True

    async def test_send_ticket_status_update_resolved(self):
        """send_ticket_status_update with resolved status."""
        result = await sms_service.send_ticket_status_update(
            "+905551234567",
            "abc12345-test-ticket-id",
            "resolved",
        )
        assert result is True

    async def test_send_ticket_status_update_closed(self):
        """send_ticket_status_update with closed status."""
        result = await sms_service.send_ticket_status_update(
            "+905551234567",
            "abc12345-test-ticket-id",
            "closed",
        )
        assert result is True

    async def test_send_ticket_status_update_escalated(self):
        """send_ticket_status_update with escalated status."""
        result = await sms_service.send_ticket_status_update(
            "+905551234567",
            "abc12345-test-ticket-id",
            "escalated",
        )
        assert result is True

    async def test_send_ticket_status_update_unknown_status(self):
        """send_ticket_status_update with unknown status uses raw status text."""
        result = await sms_service.send_ticket_status_update(
            "+905551234567",
            "abc12345-test-ticket-id",
            "unknown_custom_status",
        )
        assert result is True

    async def test_send_sms_when_disabled(self):
        """send_sms should log and return True when twilio is disabled."""
        result = await sms_service.send_sms("+905551234567", "Test message")
        assert result is True


class TestSMSServiceWithTwilioEnabled:
    """Tests for SMS service with Twilio enabled (mocked)."""

    async def test_send_sms_success_with_client(self):
        """send_sms should send via Twilio client when enabled."""
        service = SMSService()
        # Mock the client
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(sid="SM123")
        service._client = mock_client

        with patch("app.services.sms.settings") as mock_settings:
            mock_settings.twilio_enabled = True
            mock_settings.twilio_phone_number = "+15551234567"

            result = await service.send_sms("+905551234567", "Test message")

        assert result is True
        mock_client.messages.create.assert_called_once()

    async def test_send_sms_failure_with_client(self):
        """send_sms should return False on Twilio error."""
        service = SMSService()
        # Mock the client to raise an exception
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Twilio error")
        service._client = mock_client

        with patch("app.services.sms.settings") as mock_settings:
            mock_settings.twilio_enabled = True
            mock_settings.twilio_phone_number = "+15551234567"

            result = await service.send_sms("+905551234567", "Test message")

        assert result is False

    async def test_send_sms_returns_false_when_client_not_initialized(self):
        """send_sms should return False when client is None but twilio is enabled."""
        service = SMSService()
        service._client = None

        with patch("app.services.sms.settings") as mock_settings:
            mock_settings.twilio_enabled = True

            result = await service.send_sms("+905551234567", "Test message")

        assert result is False
