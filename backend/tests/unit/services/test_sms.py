from unittest.mock import MagicMock, patch


from app.services.sms import SMSService


class TestSMSService:
    """Tests for SMSService class."""

    @patch("app.services.sms.settings")
    @patch("app.services.sms.Client")
    def test_init_with_twilio_enabled(self, mock_client_class, mock_settings):
        """Should initialize Twilio client when enabled."""
        mock_settings.twilio_enabled = True
        mock_settings.twilio_account_sid = "test_sid"
        mock_settings.twilio_auth_token = "test_token"

        service = SMSService()

        mock_client_class.assert_called_once_with("test_sid", "test_token")
        assert service._client is not None

    @patch("app.services.sms.settings")
    def test_init_with_twilio_disabled(self, mock_settings):
        """Should not initialize client when disabled."""
        mock_settings.twilio_enabled = False

        service = SMSService()

        assert service._client is None

    @patch("app.services.sms.settings")
    async def test_send_otp_disabled(self, mock_settings):
        """Should return True when Twilio disabled (logs instead)."""
        mock_settings.twilio_enabled = False

        service = SMSService()
        result = await service.send_otp("+905551234567", "123456")

        assert result is True

    @patch("app.services.sms.settings")
    @patch("app.services.sms.Client")
    async def test_send_otp_success(self, mock_client_class, mock_settings):
        """Should send OTP via Twilio."""
        mock_settings.twilio_enabled = True
        mock_settings.twilio_account_sid = "test_sid"
        mock_settings.twilio_auth_token = "test_token"
        mock_settings.twilio_phone_number = "+15551234567"

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        service = SMSService()
        result = await service.send_otp("+905551234567", "123456")

        assert result is True
        mock_client.messages.create.assert_called_once()

    @patch("app.services.sms.settings")
    async def test_send_ticket_status_update_disabled(self, mock_settings):
        """Should return True when Twilio disabled."""
        mock_settings.twilio_enabled = False

        service = SMSService()
        result = await service.send_ticket_status_update(
            "+905551234567", "abc12345-678", "resolved"
        )

        assert result is True

    @patch("app.services.sms.settings")
    @patch("app.services.sms.Client")
    async def test_send_ticket_status_update_in_progress(
        self, mock_client_class, mock_settings
    ):
        """Should send localized message for in_progress status."""
        mock_settings.twilio_enabled = True
        mock_settings.twilio_account_sid = "test_sid"
        mock_settings.twilio_auth_token = "test_token"
        mock_settings.twilio_phone_number = "+15551234567"

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        service = SMSService()
        await service.send_ticket_status_update(
            "+905551234567", "abc12345-678", "in_progress"
        )

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "islem altina alindi" in call_kwargs["body"]
        assert call_kwargs["to"] == "+905551234567"

    @patch.object(SMSService, "send_sms", return_value=True)
    async def test_send_ticket_status_update_unknown_status_uses_raw_value(
        self, mock_send_sms
    ):
        """Should include raw status text when not mapped."""
        service = SMSService()

        ticket_id = "abc12345-6789"
        await service.send_ticket_status_update(
            "+905551234567", ticket_id, "pending_review"
        )

        mock_send_sms.assert_called_once()
        called_message = mock_send_sms.call_args[0][1]
        assert "pending_review" in called_message
        assert ticket_id[:8] in called_message

    @patch("app.services.sms.settings")
    async def test_send_sms_returns_false_when_client_missing(self, mock_settings):
        """Should return False when Twilio enabled but client missing."""
        mock_settings.twilio_enabled = True
        mock_settings.twilio_account_sid = "sid"
        mock_settings.twilio_auth_token = "token"
        mock_settings.twilio_phone_number = "+10000000000"

        service = SMSService()
        service._client = None

        result = await service.send_sms("+905551234567", "hello")

        assert result is False

    @patch("app.services.sms.settings")
    @patch("app.services.sms.Client")
    async def test_send_sms_handles_client_exception(
        self, mock_client_class, mock_settings
    ):
        """Should return False when Twilio client raises."""
        mock_settings.twilio_enabled = True
        mock_settings.twilio_account_sid = "sid"
        mock_settings.twilio_auth_token = "token"
        mock_settings.twilio_phone_number = "+10000000000"

        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("twilio boom")
        mock_client_class.return_value = mock_client

        service = SMSService()

        result = await service.send_sms("+905551234567", "hello")

        assert result is False
        mock_client.messages.create.assert_called_once()

    @patch("app.services.sms.settings")
    async def test_send_sms_disabled(self, mock_settings):
        """Should return True when Twilio disabled."""
        mock_settings.twilio_enabled = False

        service = SMSService()
        result = await service.send_sms("+905551234567", "Test message")

        assert result is True

    @patch("app.services.sms.settings")
    @patch("app.services.sms.Client")
    async def test_send_sms_success(self, mock_client_class, mock_settings):
        """Should send SMS successfully."""
        mock_settings.twilio_enabled = True
        mock_settings.twilio_account_sid = "test_sid"
        mock_settings.twilio_auth_token = "test_token"
        mock_settings.twilio_phone_number = "+15551234567"

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        service = SMSService()
        result = await service.send_sms("+905551234567", "Hello, world!")

        assert result is True
        mock_client.messages.create.assert_called_once_with(
            body="Hello, world!",
            from_="+15551234567",
            to="+905551234567",
        )
