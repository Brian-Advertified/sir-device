from email.message import EmailMessage
import smtplib

from app.core.config import Settings
from app.core.errors import ConfigurationError


class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send(self, *, recipient: str, subject: str, body: str) -> None:
        if not self._settings.smtp_host:
            raise ConfigurationError("SMTP_HOST is not configured")
        message = EmailMessage()
        message["From"] = self._settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port, timeout=15) as smtp:
            if self._settings.smtp_use_tls:
                smtp.starttls()
            if self._settings.smtp_username and self._settings.smtp_password:
                smtp.login(self._settings.smtp_username, self._settings.smtp_password)
            smtp.send_message(message)
