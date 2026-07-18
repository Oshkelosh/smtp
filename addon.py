"""SMTP email notification integration."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any, ClassVar, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel, Field, SecretStr

from app.addons.notifications.base import NotificationAddon
from app.addons.log import info, warning
from app.addons.config_serialization import dump_addon_config


class SmtpConfig(BaseModel):
    host: str = Field(default=..., description="SMTP server hostname")
    port: int = Field(default=587, description="SMTP server port")
    username: str = Field(default="", description="SMTP username (optional)")
    password: SecretStr = Field(default="", description="SMTP password (optional)")
    use_tls: bool = Field(default=True, description="Use STARTTLS")
    from_address: str = Field(default=..., description="Default From email address")

    @classmethod
    def config_model(cls):
        return cls


def _send_smtp_sync(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool,
    from_address: str,
    to: str,
    subject: str,
    body: str,
    html: bool,
) -> str:
    msg = EmailMessage()
    msg["From"] = from_address
    msg["To"] = to
    msg["Subject"] = subject
    if html:
        msg.set_content(body, subtype="html")
    else:
        msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=15) as server:
        if use_tls:
            server.starttls()
        if username:
            server.login(username, password)
        server.send_message(msg)
    return ""


class SmtpAddon(NotificationAddon):
    addon_id: str = "smtp"
    addon_name: str = "SMTP"
    addon_description: str = "Send transactional emails via SMTP."
    addon_category: str = "notification"
    version: str = "1.0.0"
    is_enabled: bool = False
    supported_channels: ClassVar[list[str]] = ["email"]

    _config: Dict[str, Any] | None = None
    _host: str = ""
    _port: int = 587
    _username: str = ""
    _password: str = ""
    _use_tls: bool = True
    _from_address: str = ""

    @classmethod
    def config_schema(cls):
        return SmtpConfig

    async def initialize(self, config: dict) -> None:
        validated = self.config_schema()(**config)
        self._config = dump_addon_config(validated)
        self._host = validated.host
        self._port = validated.port
        self._username = validated.username
        self._password = validated.password.get_secret_value()
        self._use_tls = validated.use_tls
        self._from_address = validated.from_address
        self.is_enabled = True
        info("SMTP", "Initialized (host={}, from={})", self._host, self._from_address)

    async def validate_config(self, config: dict) -> None:
        import asyncio

        from app.core.exceptions import ValidationError

        validated = self.config_schema()(**config)
        password = validated.password.get_secret_value()
        if not password:
            return

        def _check_login() -> None:
            with smtplib.SMTP(validated.host, validated.port, timeout=15) as server:
                if validated.use_tls:
                    server.starttls()
                if validated.username:
                    server.login(validated.username, password)
                else:
                    server.login(validated.from_address, password)

        try:
            await asyncio.to_thread(_check_login)
        except smtplib.SMTPAuthenticationError as exc:
            raise ValidationError(message="Invalid SMTP password — check your credentials") from exc
        except smtplib.SMTPException as exc:
            raise ValidationError(message=f"SMTP server rejected credentials: {exc}") from exc
        except OSError as exc:
            raise ValidationError(message=f"Could not reach SMTP server: {exc}") from exc

    async def shutdown(self) -> None:
        self._host = ""
        self._password = ""
        self.is_enabled = False

    async def _deliver(self, to: str, subject: str, body: str, html: bool) -> Dict[str, Any]:
        if not self._host or not self._from_address:
            return {"success": False, "message_id": "", "error": "Not configured", "to": to}

        kwargs = {
            "host": self._host,
            "port": self._port,
            "username": self._username,
            "password": self._password,
            "use_tls": self._use_tls,
            "from_address": self._from_address,
            "to": to,
            "subject": subject,
            "body": body,
            "html": html,
        }
        try:
            try:
                import aiosmtplib
                from email.message import EmailMessage as AsyncEmailMessage

                msg = AsyncEmailMessage()
                msg["From"] = self._from_address
                msg["To"] = to
                msg["Subject"] = subject
                if html:
                    msg.set_content(body, subtype="html")
                else:
                    msg.set_content(body)

                await aiosmtplib.send(
                    msg,
                    hostname=self._host,
                    port=self._port,
                    username=self._username or None,
                    password=self._password or None,
                    start_tls=self._use_tls,
                    timeout=15,
                )
            except ImportError:
                await asyncio.to_thread(_send_smtp_sync, **kwargs)
            return {"success": True, "message_id": "", "to": to}
        except Exception as exc:
            warning("SMTP", "send_email to={} error: {}", to, exc)
            return {"success": False, "message_id": "", "error": str(exc), "to": to}

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False,
    ) -> Dict[str, Any]:
        return await self._deliver(to, subject, body, html)

    async def send_sms(self, to: str, body: str) -> Dict[str, Any]:
        return self.channel_not_supported("sms", to)

    async def send_push(
        self,
        to: str,
        title: str,
        body: str,
        data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return self.channel_not_supported("push", to)

    def get_routers(self) -> List[APIRouter]:
        return []

    def get_admin_routes(self) -> List[APIRouter]:
        from app.addons.notifications.smtp.routes import admin_router

        return [admin_router]

    def get_admin_templates(self) -> str:
        from pathlib import Path

        return str(Path(__file__).resolve().parent / "templates")

    def get_admin_static(self) -> str:
        from pathlib import Path

        return str(Path(__file__).resolve().parent / "static")
