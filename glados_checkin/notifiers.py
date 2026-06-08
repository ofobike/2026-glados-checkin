"""Notification channel adapters except Bark."""

import re

import requests

from .renderers import render_pushplus_html, text_to_telegram_html
from .utils import log, now_bjt


def pushplus_push(token, title, content):
    """PushPlus WeChat notification using Apple-style HTML."""
    if not token:
        return False
    try:
        url = "https://www.pushplus.plus/send"
        current_time = now_bjt().strftime('%Y-%m-%d %H:%M')
        full_html = render_pushplus_html(content, current_time)
        data = {
            "token": token,
            "title": title,
            "content": full_html,
            "template": "html"
        }
        resp = requests.post(url, json=data, timeout=15)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('code') == 200:
                log("✅ PushPlus 推送成功")
                return True
            log(f"❌ PushPlus 推送失败: {result.get('msg')}")
        else:
            log(f"❌ PushPlus 推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ PushPlus 推送失败: {e}")
    return False


def serverchan(send_key, title, content):
    """ServerChan notification using Markdown."""
    if not send_key:
        return False
    try:
        url = f"https://sctapi.ftqq.com/{send_key}.send"
        md = content
        md = re.sub(r'━━━━━━ (.+?) ━━━━━━', r'**\1**\n---', md)
        md = re.sub(r'^(\S{1,2})\s*(.+?):\s*(.+)$', r'**\1 \2:** \3', md, flags=re.MULTILINE)
        md = re.sub(r'^([█░▓]+.+)$', r'```\n\1\n```', md, flags=re.MULTILINE)
        md = re.sub(r'^([💕🌈😂🧩📖🍚🌅].+)$', r'> \1', md, flags=re.MULTILINE)
        resp = requests.post(url, data={'title': title, 'desp': md}, timeout=10)
        if resp.status_code == 200:
            log("✅ Server酱推送成功")
            return True
        log(f"❌ Server酱推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ Server酱推送失败: {e}")
    return False


def dingtalk(token, title, content):
    """DingTalk robot notification using Markdown."""
    if not token:
        return False
    try:
        url = f"https://oapi.dingtalk.com/robot/send?access_token={token}"
        md = content
        md = re.sub(r'━━━━━━ (.+?) ━━━━━━', r'**\1**', md)
        md = re.sub(r'^(\S{1,2})\s*(.+?):\s*(.+)$', r'**\1 \2:** \3', md, flags=re.MULTILINE)
        md = re.sub(r'[█░▓]+[^\n]*', lambda m: m.group(0).replace('█', '■').replace('░', '□').replace('▓', '▣'), md)
        md = re.sub(r'^([💕🌈😂🧩📖🍚🌅].+)$', r'> \1', md, flags=re.MULTILINE)
        msg = f"## {title}\n\n{md}"
        data = {"msgtype": "markdown", "markdown": {"title": title, "text": msg}}
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('errcode') == 0:
                log("✅ 钉钉推送成功")
                return True
            log(f"❌ 钉钉推送失败: {result.get('errmsg')}")
        else:
            log(f"❌ 钉钉推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ 钉钉推送失败: {e}")
    return False


def telegram_push(token, chat_id, title, content):
    """Telegram notification using HTML."""
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = text_to_telegram_html(content)
        msg = f"<b>{title}</b>\n\n{text}"
        data = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('ok'):
                log("✅ Telegram 推送成功")
                return True
            log(f"❌ Telegram 推送失败: {result.get('description')}")
            data2 = {"chat_id": chat_id, "text": f"{title}\n\n{content}"}
            resp2 = requests.post(url, json=data2, timeout=10)
            if resp2.status_code == 200 and resp2.json().get('ok'):
                log("✅ Telegram 推送成功 (纯文本降级)")
                return True
        else:
            log(f"❌ Telegram 推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ Telegram 推送失败: {e}")
    return False
