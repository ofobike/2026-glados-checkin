"""Standalone Bark morning report task."""

import os
import re

from .bark import bark_event_push
from .config import env_int, env_text
from .utils import log, now_bjt


def _split_todos(raw):
    if not raw:
        return []
    parts = re.split(r'[\n;；]+', raw)
    return [part.strip(" -\t") for part in parts if part.strip(" -\t")]


def _format_todos():
    todos = _split_todos(os.environ.get("MORNING_TODOS") or os.environ.get("DAILY_TODOS"))
    if not todos:
        return "📌 今日待办: 暂无"
    lines = ["📌 今日待办:"]
    for idx, todo in enumerate(todos[:8], 1):
        lines.append(f"{idx}. {todo}")
    if len(todos) > 8:
        lines.append(f"... 还有 {len(todos) - 8} 项")
    return "\n".join(lines)


def build_morning_report():
    """Build the standalone Bark morning report body."""
    from .app import (
        get_clothing_advice,
        get_countdown,
        get_daily_quote_en,
        get_health_tip,
        get_holiday_countdown,
        get_life_index,
        get_lunar_info,
        get_morning_greeting,
        get_quote,
        get_weather,
    )

    weather_text = get_weather()
    parts = [
        get_morning_greeting(),
        now_bjt().strftime("📅 %Y-%m-%d %H:%M"),
    ]

    for item in (
        weather_text,
        get_clothing_advice(weather_text) if weather_text else "",
        get_life_index(weather_text) if weather_text else "",
        get_health_tip(weather_text),
        get_lunar_info(),
        get_holiday_countdown(),
        get_countdown(),
        get_quote(),
        get_daily_quote_en(),
        _format_todos(),
    ):
        if item:
            parts.append(str(item))

    reminder = env_text("MORNING_REMINDER") or env_text("DAILY_REMINDER")
    if reminder:
        parts.append(f"🔔 每日提醒: {reminder}")

    return "\n\n".join(parts)


def send_morning_report():
    """Send a standalone Bark morning report without requiring GLADOS_COOKIE."""
    log("🌅 Bark 每日早报开始...")
    bark_key = os.environ.get("BARK_KEY")
    if not bark_key:
        log("⚠️ 未配置 BARK_KEY，无法发送每日早报")
        return False

    body = build_morning_report()
    title = env_text("MORNING_TITLE", "每日早报")
    ok = bark_event_push(
        bark_key,
        title,
        body,
        level=env_text("MORNING_BARK_LEVEL", "active"),
        sound=env_text("MORNING_BARK_SOUND", "birdsong"),
        group_suffix=env_text("MORNING_GROUP_SUFFIX", "早报"),
        url=env_text("MORNING_BARK_URL", ""),
        copy_text=body,
        body_limit=env_int("MORNING_BARK_BODY_LIMIT", 1200) or 1200,
        copy_limit=env_int("MORNING_BARK_COPY_LIMIT", 1200) or 1200,
        default_url="",
    )
    if ok:
        log("🌅 每日早报已发送")
    return ok
