"""Environment variable helpers."""

import os


def env_flag(name, default=False):
    """Read a boolean environment variable."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on", "y")


def env_int(name, default=None):
    """Read an integer environment variable."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except Exception:
        return default


def env_text(name, default=""):
    """Read a text environment variable, treating blank values as missing."""
    value = os.environ.get(name)
    if value is None or str(value).strip() == "":
        return default
    return str(value).strip()


def github_actions_url():
    repo = os.environ.get("GITHUB_REPOSITORY")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com").rstrip("/")
    if repo:
        return f"{server}/{repo}/actions"
    return "https://github.com"
