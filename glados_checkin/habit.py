"""Standalone Bark habit reminder task."""

import hashlib
import json
import os
import re
from datetime import datetime

from .bark import bark_event_push
from .config import env_flag, env_int, env_text
from .paths import DATA_FILE
from .utils import BJT, log, now_bjt


HABIT_TYPES = {
    "water": {
        "label": "喝水",
        "title": "喝水提醒",
        "sound": "birdsong",
        "level": "active",
        "messages": [
            "喝一杯水，给接下来的专注留点余量。",
            "先把水杯补满，再继续今天的节奏。",
            "起身倒杯水，顺手放松一下肩颈。",
        ],
    },
    "stand": {
        "label": "活动",
        "title": "起身活动",
        "sound": "birdsong",
        "level": "active",
        "messages": [
            "站起来活动 2 分钟，肩颈和腰背都需要一点空间。",
            "离开座位走一小圈，让身体重新上线。",
            "做一次简单拉伸，再回到手头的事。",
        ],
    },
    "study": {
        "label": "学习",
        "title": "学习提醒",
        "sound": "bell",
        "level": "active",
        "messages": [
            "开启一段 25 分钟专注学习，先做最容易开始的一小步。",
            "把学习资料打开，今天只要先进入状态。",
            "给自己一段不被打断的学习时间，完成一个小闭环。",
        ],
    },
    "exercise": {
        "label": "运动",
        "title": "运动提醒",
        "sound": "bell",
        "level": "active",
        "messages": [
            "今天给身体一点进度：散步、拉伸或完成计划运动。",
            "运动不用等完美时间，现在做一个小开始也算数。",
            "把运动任务推进一点，哪怕只是 10 分钟。",
        ],
    },
    "sleep": {
        "label": "睡觉",
        "title": "睡觉提醒",
        "sound": "bell",
        "level": "timeSensitive",
        "messages": [
            "可以准备收尾了，放下屏幕，给明天留一个清醒的开头。",
            "今天到这里也很好，开始进入睡前节奏。",
            "整理一下明天要做的事，然后让自己早点休息。",
        ],
    },
    "medicine": {
        "label": "用药",
        "title": "用药提醒",
        "sound": "bell",
        "level": "timeSensitive",
        "messages": [
            "如果今天有用药或保健品安排，现在核对一下。",
            "检查一下今天的用药计划，完成后可以安心继续。",
            "别把这件事留到太晚，现在确认一下更稳。",
        ],
    },
    "eye": {
        "label": "护眼",
        "title": "护眼提醒",
        "sound": "birdsong",
        "level": "active",
        "messages": [
            "看远处 20 秒，放松眼睛和肩颈。",
            "闭眼休息一小会儿，让眼睛从屏幕里出来。",
            "做一次 20-20-20 护眼休息，再继续。",
        ],
    },
}


HABIT_ALIASES = {
    "drink": "water",
    "drink_water": "water",
    "hydrate": "water",
    "喝水": "water",
    "move": "stand",
    "stretch": "stand",
    "activity": "stand",
    "活动": "stand",
    "拉伸": "stand",
    "learn": "study",
    "focus": "study",
    "学习": "study",
    "exercise": "exercise",
    "sport": "exercise",
    "workout": "exercise",
    "运动": "exercise",
    "bed": "sleep",
    "bedtime": "sleep",
    "睡觉": "sleep",
    "休息": "sleep",
    "med": "medicine",
    "medicine": "medicine",
    "medication": "medicine",
    "用药": "medicine",
    "吃药": "medicine",
    "eyes": "eye",
    "eye": "eye",
    "护眼": "eye",
    "random": "random",
    "surprise": "random",
    "随机": "random",
}


DEFAULT_RANDOM_TASKS = [
    "整理桌面 3 分钟。",
    "写下今天最重要的一件事。",
    "深呼吸 5 次，把节奏放稳。",
    "复盘一个刚完成的小任务。",
    "把水杯补满。",
    "清掉一个 2 分钟内能完成的小事项。",
    "打开待办列表，选一个最容易开始的任务。",
]


def _load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _split_items(raw):
    if not raw:
        return []
    parts = re.split(r"[\n;；]+", raw)
    return [part.strip(" -\t") for part in parts if part.strip(" -\t")]


def _normalize_habit_type(raw):
    key = str(raw or "water").strip().lower().replace("-", "_")
    kind = HABIT_ALIASES.get(key, key)
    if kind == "random" or kind in HABIT_TYPES:
        return kind
    log(f"⚠️ 未识别 HABIT_TYPE={raw}，已按 water 处理")
    return "water"


def _deterministic_choice(items, key):
    if not items:
        return ""
    digest = hashlib.md5(key.encode("utf-8")).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def _habit_now_key(kind):
    return f"{now_bjt().strftime('%Y-%m-%d')}:{kind}"


def _habit_preset(kind):
    if kind != "random":
        return HABIT_TYPES.get(kind) or HABIT_TYPES["water"]

    tasks = _split_items(os.environ.get("HABIT_RANDOM_TASKS")) or DEFAULT_RANDOM_TASKS
    task = _deterministic_choice(tasks, _habit_now_key("random"))
    return {
        "label": "随机",
        "title": "随机小任务",
        "sound": "bell",
        "level": "active",
        "messages": [task],
    }


def _habit_state(data):
    if "habit_alerts" not in data:
        data["habit_alerts"] = {}
    return data["habit_alerts"]


def _parse_state_time(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=BJT)
        return dt.astimezone(BJT)
    except Exception:
        return None


def _habit_dedupe_key(kind):
    return _normalize_habit_type(kind)


def _already_sent_recently(state, kind, minutes):
    if minutes <= 0 or env_flag("HABIT_FORCE", False):
        return False
    item = state.get(_habit_dedupe_key(kind), {})
    last_dt = _parse_state_time(item.get("last_sent_at"))
    if not last_dt:
        return False
    return (now_bjt() - last_dt).total_seconds() < minutes * 60


def _mark_sent(state, kind, title):
    state[_habit_dedupe_key(kind)] = {
        "last_sent_at": now_bjt().isoformat(),
        "last_title": title,
    }


def build_habit_notification():
    """Build the habit reminder title/body/options."""
    kind = _normalize_habit_type(env_text("HABIT_TYPE", "water"))
    preset = _habit_preset(kind)
    label = preset["label"]
    title = env_text("HABIT_TITLE") or preset["title"]
    message = env_text("HABIT_MESSAGE")
    if not message:
        message = _deterministic_choice(preset["messages"], _habit_now_key(kind))

    body = "\n".join(
        [
            message,
            "",
            f"类型: {label}",
            f"时间: {now_bjt().strftime('%Y年%m月%d日 %H:%M')}",
        ]
    )
    return {
        "kind": kind,
        "label": label,
        "title": title,
        "body": body,
        "level": env_text("HABIT_BARK_LEVEL", preset["level"]),
        "sound": env_text("HABIT_BARK_SOUND", preset["sound"]),
        "url": env_text("HABIT_BARK_URL", ""),
        "group_suffix": env_text("HABIT_GROUP_SUFFIX", "习惯"),
    }


def send_habit_reminder():
    """Send a standalone Bark habit reminder without requiring GLADOS_COOKIE."""
    log("🌱 Bark 习惯提醒开始...")
    if not env_flag("HABIT_ENABLED", True):
        log("⏭️ HABIT_ENABLED=false，跳过")
        return False

    notification = build_habit_notification()
    dedupe_minutes = env_int("HABIT_DEDUPE_MINUTES", 20) or 0
    data = _load_data()
    state = _habit_state(data)

    log("🔎 习惯提醒参数:")
    log(f"   HABIT_TYPE: {notification['kind']} ({notification['label']})")
    log(f"   HABIT_DEDUPE_MINUTES: {dedupe_minutes}")
    log(f"   HABIT_FORCE: {env_flag('HABIT_FORCE', False)}")
    log(f"   标题: {notification['title']}")

    if _already_sent_recently(state, notification["kind"], dedupe_minutes):
        log(f"⏭️ {notification['label']} 提醒在 {dedupe_minutes} 分钟内已发送过")
        return False

    bark_key = os.environ.get("BARK_KEY")
    if not bark_key:
        log("⚠️ 未配置 BARK_KEY，无法发送习惯提醒；本次仅输出日志")
        for line in notification["body"].splitlines():
            log(f"   {line}")
        return False

    ok = bark_event_push(
        bark_key,
        notification["title"],
        notification["body"],
        level=notification["level"],
        sound=notification["sound"],
        group_suffix=notification["group_suffix"],
        url=notification["url"],
        copy_text=notification["body"],
        body_limit=env_int("HABIT_BARK_BODY_LIMIT", 800) or 800,
        copy_limit=env_int("HABIT_BARK_COPY_LIMIT", 800) or 800,
        default_url="",
    )
    if ok:
        _mark_sent(state, notification["kind"], notification["title"])
        _save_data(data)
        log(f"📣 习惯提醒已发送: {notification['label']}")
    return ok
