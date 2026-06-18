"""Minimal unit tests for the smtp addon."""

from app.addons.notifications.smtp.addon import SmtpAddon


def test_addon_identity():
    assert SmtpAddon.addon_id == "smtp"
    assert SmtpAddon.addon_category == "notification"
