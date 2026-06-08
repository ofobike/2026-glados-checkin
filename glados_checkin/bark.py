"""Bark notification payloads and delivery."""

import json
import re

import requests

from .config import env_flag, env_int, env_text, github_actions_url
from .utils import log, mask_email, parse_int, shorten, utf8_len


def _split_bark_keys(raw):
    """Support one key, multiple keys, or full Bark URLs."""
    if not raw:
        return []
    parts = re.split(r'[\n,;&]+', raw)
    return [p.strip().rstrip('/') for p in parts if p.strip()]


def _bark_endpoint(key, api_host):
    if key.startswith("http://") or key.startswith("https://"):
        return key
    return f"{api_host.rstrip('/')}/{key}"


def _bark_min_days(accounts):
    days_values = []
    for acc in accounts or []:
        days = parse_int(acc.get('days'))
        if days is not None:
            days_values.append(days)
    return min(days_values) if days_values else None


def extract_bark_summary(content, accounts=None, success_cnt=None, total_cnt=None, expired_cookies=None):
    """Extract a compact summary suitable for the iOS lock screen."""
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    summary_parts = []
    total = total_cnt if total_cnt is not None else len(accounts or [])
    expired_cookies = expired_cookies or []

    if total:
        summary_parts.append(f"签到: 成功 {success_cnt}/{total}")
    if expired_cookies:
        summary_parts.append(f"Cookie 异常: 账号 {', '.join(str(i) for i in expired_cookies)}")

    for acc in (accounts or [])[:3]:
        icon = "✅" if acc.get('ok') else "❌"
        summary_parts.append(
            f"{icon} {mask_email(str(acc.get('email', '?')))} | {acc.get('points', '?')}分 | {acc.get('days', '?')}天"
        )
    if accounts and len(accounts) > 3:
        summary_parts.append(f"... 还有 {len(accounts) - 3} 个账号")

    wanted = (
        '签到结果', '本次获得', '连续签到', '本月签到', '月度目标',
        '可兑换', '紧急续期', '即将到期', '到期日期'
    )
    for line in lines:
        if any(key in line for key in wanted) and line not in summary_parts:
            summary_parts.append(line)
        if len("\n".join(summary_parts)) >= 420:
            break

    if not summary_parts:
        summary_parts = lines[:3]

    return shorten('\n'.join(summary_parts), 480)


def _bark_subtitle(success_cnt, total_cnt, accounts, expired_cookies):
    parts = []
    if total_cnt:
        parts.append(f"成功 {success_cnt}/{total_cnt}")
    min_days = _bark_min_days(accounts)
    if min_days is not None:
        parts.append(f"最少剩余 {min_days} 天")
    if expired_cookies:
        parts.append("Cookie 异常")
    return " · ".join(parts)


def _bark_level(success_cnt, total_cnt, accounts, expired_cookies):
    min_days = _bark_min_days(accounts)
    has_fail = total_cnt is not None and success_cnt is not None and success_cnt < total_cnt

    if expired_cookies:
        if env_flag("BARK_CRITICAL_ON_EXPIRE", False):
            return env_text("BARK_LEVEL_EXPIRED", "critical")
        return env_text("BARK_LEVEL_EXPIRED", "timeSensitive")
    if has_fail:
        return env_text("BARK_LEVEL_FAIL", "timeSensitive")
    if min_days is not None and min_days <= env_int("BARK_LOW_DAYS", 7):
        return env_text("BARK_LEVEL_LOW_DAYS", "timeSensitive")
    return env_text("BARK_LEVEL_SUCCESS", "passive")


def _bark_sound(level, expired_cookies, success_cnt, total_cnt):
    has_fail = total_cnt is not None and success_cnt is not None and success_cnt < total_cnt
    if expired_cookies:
        return env_text("BARK_SOUND_EXPIRED", "alarm")
    if has_fail or level in ("timeSensitive", "critical"):
        return env_text("BARK_SOUND_FAIL", "alarm")
    return env_text("BARK_SOUND_SUCCESS", "birdsong")


def _bark_badge(accounts, success_cnt, total_cnt, expired_cookies):
    forced = env_int("BARK_BADGE")
    if forced is not None:
        return forced

    mode = env_text("BARK_BADGE_MODE", "days").strip().lower()
    if mode in ("", "off", "none", "false", "0"):
        return None
    if mode == "success":
        return success_cnt
    if mode in ("fail", "failed"):
        return max((total_cnt or 0) - (success_cnt or 0), len(expired_cookies or []))
    if mode == "days":
        return _bark_min_days(accounts)
    return None


def _bark_target_url(success_cnt, total_cnt, expired_cookies):
    has_fail = total_cnt is not None and success_cnt is not None and success_cnt < total_cnt
    if expired_cookies:
        return env_text("BARK_URL_EXPIRED", "https://glados.cloud/console/checkin")
    if has_fail:
        return env_text("BARK_URL_FAIL", github_actions_url())
    return env_text("BARK_URL_SUCCESS", "https://glados.cloud/console/checkin")


def _bark_copy_text(title, body, content):
    """Keep Bark copy payload small enough to avoid HTTP 413."""
    mode = env_text("BARK_COPY_MODE", "summary").lower()
    if mode in ("", "off", "none", "false", "0"):
        return ""
    limit = env_int("BARK_COPY_LIMIT", 800)
    if limit is None or limit <= 0:
        limit = 800
    if mode in ("full", "content"):
        text = f"{title}\n\n{body}\n\n{content}"
    else:
        text = f"{title}\n\n{body}"
    return shorten(text, min(limit, 3500))


def _bark_payload(title, content, accounts=None, success_cnt=None, total_cnt=None, expired_cookies=None):
    accounts = accounts or []
    expired_cookies = expired_cookies or []
    level = _bark_level(success_cnt, total_cnt, accounts, expired_cookies)
    body = extract_bark_summary(content, accounts, success_cnt, total_cnt, expired_cookies)

    data = {
        "title": title,
        "subtitle": _bark_subtitle(success_cnt, total_cnt, accounts, expired_cookies),
        "body": body,
        "group": env_text("BARK_GROUP", "GLaDOS"),
        "sound": _bark_sound(level, expired_cookies, success_cnt, total_cnt),
        "level": level,
        "url": _bark_target_url(success_cnt, total_cnt, expired_cookies),
    }

    copy_text = _bark_copy_text(title, body, content)
    if copy_text:
        data["copy"] = copy_text

    if env_flag("BARK_ARCHIVE", True):
        data["isArchive"] = "1"

    badge = _bark_badge(accounts, success_cnt, total_cnt, expired_cookies)
    if badge is not None:
        data["badge"] = max(0, badge)

    optional_envs = {
        "BARK_ICON": "icon",
        "BARK_IMAGE": "image",
        "BARK_CATEGORY": "category",
        "BARK_ACTION": "action",
    }
    for env_name, payload_key in optional_envs.items():
        value = env_text(env_name)
        if value:
            data[payload_key] = value

    ttl = env_int("BARK_TTL")
    if ttl is not None:
        data["ttl"] = max(0, ttl)

    volume = env_int("BARK_VOLUME")
    if volume is not None:
        data["volume"] = str(max(0, min(volume, 10)))

    if env_flag("BARK_AUTO_COPY", False):
        data["autoCopy"] = "1"

    if expired_cookies and env_flag("BARK_CALL_ON_EXPIRE", False):
        data["call"] = "1"

    return {k: v for k, v in data.items() if v not in (None, "")}


def _send_bark_payload(key, data):
    """Send an assembled Bark payload."""
    keys = _split_bark_keys(key)
    if not keys:
        log("⚠️ Bark: 未配置 BARK_KEY，跳过推送")
        return False

    api_host = env_text("BARK_SERVER", "https://api.day.app").rstrip("/")

    log("📱 Bark 推送开始...")
    log(f"   设备数: {len(keys)}")
    log(f"   请求地址: {api_host}")
    log(f"   标题: {data.get('title', '')}")
    log(f"   级别: {data.get('level')} | 声音: {data.get('sound')} | 角标: {data.get('badge', '未设置')}")
    log(f"   内容长度: {len(data.get('body', ''))} 字符 | Payload: {utf8_len(json.dumps(data, ensure_ascii=False))} bytes")

    ok_count = 0
    for one_key in keys:
        try:
            url = _bark_endpoint(one_key, api_host)
            resp = requests.post(url, json=data, timeout=15)
            log(f"   响应状态: HTTP {resp.status_code}")
            log(f"   响应内容: {resp.text[:200]}")

            if resp.status_code == 200:
                result = resp.json()
                if result.get('code') == 200:
                    ok_count += 1
                    continue
                log(f"❌ Bark 推送失败: {result.get('message', 'Unknown error')}")
            else:
                log(f"❌ Bark 推送失败: HTTP {resp.status_code}")
        except requests.exceptions.SSLError as e:
            log(f"❌ Bark 推送失败: SSL 连接错误 - {e}")
            log("   提示: 可能是网络环境限制，GitHub Actions 上应该可以正常工作")
        except requests.exceptions.ConnectionError as e:
            log(f"❌ Bark 推送失败: 连接错误 - {e}")
            log("   提示: 无法连接到 Bark API 服务器")
        except requests.exceptions.Timeout as e:
            log(f"❌ Bark 推送失败: 请求超时 - {e}")
        except Exception as e:
            log(f"❌ Bark 推送失败: {type(e).__name__}: {e}")

    if ok_count == len(keys):
        log("✅ Bark 推送成功!")
        return True
    if ok_count > 0:
        log(f"⚠️ Bark 部分推送成功: {ok_count}/{len(keys)}")
    return False


def bark_push(key, title, content, accounts=None, success_cnt=None, total_cnt=None, expired_cookies=None):
    """Send the main GLaDOS report through Bark."""
    data = _bark_payload(title, content, accounts, success_cnt, total_cnt, expired_cookies)
    return _send_bark_payload(key, data)


def bark_event_push(
    key,
    title,
    body,
    level="active",
    sound="birdsong",
    group_suffix="提醒",
    url=None,
    copy_text=None,
    body_limit=None,
    copy_limit=None,
    default_url="https://glados.cloud/console/checkin",
):
    """Send an independent event notification, such as heartbeat or exchange alerts."""
    if not key:
        log("⚠️ Bark: 未配置 BARK_KEY，跳过事件推送")
        return False

    group = env_text("BARK_GROUP", "GLaDOS")
    if group_suffix:
        group = f"{group}/{group_suffix}"

    if body_limit is None:
        body_limit = env_int("BARK_EVENT_BODY_LIMIT", 480) or 480
    if copy_limit is None:
        copy_limit = env_int("BARK_COPY_LIMIT", 800) or 800
    target_url = default_url if url is None else url

    data = {
        "title": title,
        "body": shorten(body, body_limit),
        "group": group,
        "sound": sound,
        "level": level,
        "url": target_url,
        "copy": shorten(copy_text or body, copy_limit),
    }
    if env_flag("BARK_ARCHIVE", True):
        data["isArchive"] = "1"
    if env_flag("BARK_AUTO_COPY", False):
        data["autoCopy"] = "1"

    return _send_bark_payload(key, {k: v for k, v in data.items() if v not in (None, "")})
