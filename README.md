# SMTP (`smtp`)

Send transactional emails through any SMTP relay.

## Overview

| | |
|---|---|
| Addon ID | `smtp` |
| Category | notification |
| Channels | email |
| Version | 1.0.0 |
| Category guide | [../README.md](../README.md) |

Only **one** notification provider per channel can be active at a time.

## Enable and configure

1. Install this package under `app/addons/notifications/smtp/`
2. Open **Admin → Notifications → SMTP** at `/admin/notifications/smtp`
3. Enter relay host, credentials, and from-address
4. Enable the provider checkbox and save

## Configuration schema

| Field | Type | Description |
|-------|------|-------------|
| `host` | string | SMTP server hostname |
| `port` | integer | SMTP port (default `587`) |
| `username` | string | SMTP username (optional) |
| `password` | secret | SMTP password (optional) |
| `use_tls` | boolean | Use STARTTLS (recommended) |
| `from_address` | string | Default **From** email address |

Secrets are stored in `addon_configs`, not in `.env`.

## Routes

### Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/notifications/smtp` | Config form |
| POST | `/admin/notifications/smtp/save` | Save config |

### Public API

None — core calls `send_email()` directly.

## Core integration

Uses `aiosmtplib` when installed; otherwise falls back to `asyncio.to_thread` + stdlib `smtplib`.

## Provider setup

1. Obtain SMTP credentials from your mail host (e.g. Mailtrap, SendGrid SMTP, your ISP relay).
2. Use port **587** with STARTTLS for submission, or **465** with implicit TLS if your provider requires it (set `use_tls` accordingly).
3. Ensure the **From** address is allowed by your relay (SPF/DKIM configured on the domain).
4. Save credentials in admin and enable the addon.

SMS and push are not supported (`channel_not_supported`).

## Package layout

```
smtp/
├── README.md
├── addon.py
├── routes.py
└── templates/
    └── smtp_config.html
```

## See also

- [Notification addon development](../README.md)
- [Oshkelosh addon guide](../../README.md)
