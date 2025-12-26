"""Email service for sending emails via Resend."""

import logging

import resend

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend."""

    def __init__(self) -> None:
        """Initialize the email service."""
        if settings.resend_enabled and settings.resend_api_key:
            resend.api_key = settings.resend_api_key

    async def send_verification_email(
        self, to_email: str, user_name: str, token: str
    ) -> bool:
        """Send email verification link to new citizen users.

        Args:
            to_email: The recipient email address.
            user_name: The user's name for personalization.
            token: The verification token.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        verification_url = (
            f"{settings.next_public_app_base_url}/verify-email?token={token}"
        )

        subject = "Verify your email address - Sosoft"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Sosoft!</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #333; margin-top: 0;">Hi {user_name},</h2>
        <p>You're signing up for a Sosoft account. Please verify your email address to complete your registration and start using our services.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Verify Email Address</a>
        </div>
        <p style="color: #666; font-size: 14px;">This link will expire in 24 hours.</p>
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 25px 0;">
        <p style="color: #666; font-size: 14px;">If you didn't create an account with Sosoft, you can safely ignore this email.</p>
        <p style="color: #666; font-size: 14px; margin-bottom: 0;">– Sosoft Support</p>
    </div>
</body>
</html>
"""

        return await self._send_email(to_email, subject, html_content)

    async def send_staff_invite_email(
        self, to_email: str, user_name: str, role: str, token: str
    ) -> bool:
        """Send invite email to new staff members (support/manager).

        Args:
            to_email: The recipient email address.
            user_name: The user's name for personalization.
            role: The user's role (SUPPORT or MANAGER).
            token: The invite token.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        set_password_url = (
            f"{settings.next_public_app_base_url}/set-password?token={token}"
        )
        role_display = "Support Team Member" if role == "SUPPORT" else "Manager"

        subject = "You've been invited to join Sosoft"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Sosoft!</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #333; margin-top: 0;">Hi {user_name},</h2>
        <p>You've been invited to join Sosoft as a <strong>{role_display}</strong>.</p>
        <p>Please click the button below to set your password and activate your account.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{set_password_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Set Your Password</a>
        </div>
        <p style="color: #666; font-size: 14px;">This link will expire in 24 hours.</p>
        <p style="color: #666; font-size: 14px;">You'll need to verify your phone number when setting your password.</p>
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 25px 0;">
        <p style="color: #666; font-size: 14px;">If you weren't expecting this invitation, you can safely ignore this email.</p>
        <p style="color: #666; font-size: 14px; margin-bottom: 0;">– Sosoft Support</p>
    </div>
</body>
</html>
"""

        return await self._send_email(to_email, subject, html_content)

    async def send_password_reset_email(
        self, to_email: str, user_name: str, token: str
    ) -> bool:
        """Send password reset link to user.

        Args:
            to_email: The recipient email address.
            user_name: The user's name for personalization.
            token: The password reset token.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        reset_url = f"{settings.next_public_app_base_url}/reset-password?token={token}"

        subject = "Reset your password - Sosoft"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #333; margin-top: 0;">Hi {user_name},</h2>
        <p>We received a request to reset your password. Click the button below to create a new password.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Reset Password</a>
        </div>
        <p style="color: #666; font-size: 14px;">This link will expire in 1 hour.</p>
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 25px 0;">
        <p style="color: #666; font-size: 14px;">If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
        <p style="color: #666; font-size: 14px; margin-bottom: 0;">– Sosoft Support</p>
    </div>
</body>
</html>
"""

        return await self._send_email(to_email, subject, html_content)

    async def _send_email(self, to: str, subject: str, html: str) -> bool:
        """Send an email using Resend.

        Args:
            to: The recipient email address.
            subject: The email subject.
            html: The HTML content of the email.

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        if not settings.resend_enabled:
            logger.info(f"Email (disabled): {to} - {subject}")
            return True

        try:
            resend.Emails.send(
                {
                    "from": f"{settings.resend_from_name} <{settings.resend_from_email}>",
                    "to": to,
                    "subject": subject,
                    "html": html,
                }
            )
            logger.info(f"Email sent to {to}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False


# Singleton instance
email_service = EmailService()
