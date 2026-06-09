"""Helpers for iOS Shortcuts deep links."""

from urllib.parse import urlencode

from .config import env_text


def shortcut_url(name="", shortcut_input="", text=""):
    """Build a shortcuts:// URL for running a shortcut by name."""
    name = str(name or "").strip()
    if not name:
        return ""

    params = {"name": name}
    shortcut_input = str(shortcut_input or "").strip()
    text = str(text or "").strip()
    if shortcut_input:
        params["input"] = shortcut_input
    if text:
        params["text"] = text
    return "shortcuts://run-shortcut?" + urlencode(params)


def shortcut_url_from_env(prefix):
    """Build a Shortcuts URL from PREFIX_SHORTCUT_* variables."""
    prefix = str(prefix or "").strip().upper()
    if not prefix:
        return ""
    return shortcut_url(
        env_text(f"{prefix}_SHORTCUT_NAME"),
        shortcut_input=env_text(f"{prefix}_SHORTCUT_INPUT"),
        text=env_text(f"{prefix}_SHORTCUT_TEXT"),
    )


def bark_url_or_shortcut(url_name, shortcut_prefix, default=""):
    """Use an explicit Bark URL first, otherwise fall back to a Shortcuts URL."""
    explicit = env_text(url_name)
    if explicit:
        return explicit
    generated = shortcut_url_from_env(shortcut_prefix)
    if generated:
        return generated
    return default
