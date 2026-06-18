"""SMTP addon routes."""

from __future__ import annotations

from typing import Any

from app.addons.notifications.shared_routes import build_notification_routers


def _parse_smtp_config_form(form: Any) -> tuple[dict[str, Any], bool]:
    port_raw = form.get("port", "587")
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 587
    return (
        {
            "host": form.get("host", ""),
            "port": port,
            "username": form.get("username", ""),
            "password": form.get("password", ""),
            "use_tls": form.get("use_tls") == "on",
            "from_address": form.get("from_address", ""),
        },
        form.get("is_enabled") == "on",
    )


admin_router, jinja_env = build_notification_routers(
    "smtp",
    template_name="smtp_config.html",
    page_title="SMTP Settings",
    secret_keys=("password",),
    parse_config_form=_parse_smtp_config_form,
)
