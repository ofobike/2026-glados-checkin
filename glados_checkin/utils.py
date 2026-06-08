"""Shared utility helpers."""

import sys
from datetime import datetime, timedelta, timezone


if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')


BJT = timezone(timedelta(hours=8))  # Beijing time, UTC+8


def now_bjt():
    """Return current Beijing time."""
    return datetime.now(BJT)


def log(msg):
    ts = now_bjt().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def mask_email(email):
    """Mask an email address while keeping the original project style."""
    if not email or '@' not in email or email == '?':
        return email
    user, domain = email.split('@', 1)
    if len(user) <= 3:
        return user[0] + '***@' + domain
    return user[:3] + '***' + user[-2:] + '@' + domain


def shorten(text, limit):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[:max(limit - 3, 0)] + "..."


def utf8_len(value):
    return len(str(value or "").encode("utf-8"))


def parse_int(value):
    try:
        return int(float(str(value).strip()))
    except Exception:
        return None
