#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 GLaDOS 自动签到 (积分增强版)

功能：
- 全自动签到
- 精准获取当前积分 (Points)
- Server酱/钉钉/Telegram 多渠道推送
- 积分趋势、连续签到、价值估算
- 天气预报、每日一句
- Cookie 过期自动告警
- 智能多域名切换 (优先 glados.cloud)
"""

import requests
import json
import os
import sys
import time
import re
import random
from datetime import datetime, timedelta
from pathlib import Path

# Fix Windows Unicode Output
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# ================= 时区配置 =================
from datetime import timezone

BJT = timezone(timedelta(hours=8))  # 北京时间 UTC+8

def now_bjt():
    """获取北京时间"""
    return datetime.now(BJT)

# ================= 配置 =================

# 域名优先级：Cloud 第一
DOMAINS = [
    "https://glados.cloud",
    "https://glados.rocks", 
    "https://glados.network",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Content-Type': 'application/json;charset=UTF-8',
    'Accept': 'application/json, text/plain, */*',
}

# ================= 工具函数 =================

def log(msg):
    ts = now_bjt().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def mask_email(email):
    """邮箱脱敏: 182****44@163.com"""
    if '@' not in email or email == '?':
        return email
    user, domain = email.split('@', 1)
    if len(user) <= 3:
        return user[0] + '***@' + domain
    return user[:3] + '***' + user[-2:] + '@' + domain

def progress_bar(current, target, width=8):
    """生成进度条: █████░░░ 62%"""
    if target <= 0:
        return '█' * width + ' 100%'
    ratio = min(current / target, 1.0)
    filled = round(ratio * width)
    empty = width - filled
    percent = round(ratio * 100)
    return '█' * filled + '░' * empty + f' {percent}%'

def get_greeting():
    """根据时间返回问候语"""
    hour = now_bjt().hour
    if hour < 6:
        return "🌙 深夜好"
    elif hour < 9:
        return "🌅 早上好"
    elif hour < 12:
        return "☀️ 上午好"
    elif hour < 14:
        return "🌤 中午好"
    elif hour < 18:
        return "🌇 下午好"
    elif hour < 22:
        return "🌆 晚上好"
    else:
        return "🌙 夜深了"

# ================= 数据持久化 =================

DATA_FILE = Path(__file__).parent / "glados_data.json"

def load_data():
    """加载历史数据"""
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding='utf-8'))
        except:
            pass
    return {"points_history": {}, "checkin_streak": {}}

def save_data(data):
    """保存历史数据"""
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

# ================= 积分趋势 =================

def record_points(data, email, points):
    """记录当天积分"""
    today = now_bjt().strftime('%Y-%m-%d')
    if email not in data["points_history"]:
        data["points_history"][email] = []
    history = data["points_history"][email]
    # 更新或添加今天的记录
    if history and history[-1]["date"] == today:
        history[-1]["points"] = points
    else:
        history.append({"date": today, "points": points})
    # 只保留最近30天
    data["points_history"][email] = history[-30:]

def format_trend(data, email):
    """格式化积分趋势（近7天）"""
    history = data.get("points_history", {}).get(email, [])
    if len(history) < 2:
        return "📊 趋势: 数据积累中 (至少需要2天数据)"
    recent = history[-7:]
    if len(recent) < 2:
        return "📊 趋势: 数据积累中"
    changes = []
    for i in range(1, len(recent)):
        diff = recent[i]["points"] - recent[i-1]["points"]
        if diff > 0:
            changes.append(f"+{diff}")
        else:
            changes.append(str(diff))
    total_change = recent[-1]["points"] - recent[0]["points"]
    trend_icon = "📈" if total_change > 0 else "📉" if total_change < 0 else "➡️"
    return f"{trend_icon} 近{len(recent)}天趋势: {' '.join(changes)} (共{'+' if total_change>=0 else ''}{total_change})"

# ================= 连续签到 =================

def update_streak(data, email, checkin_ok):
    """更新连续签到天数"""
    today = now_bjt().strftime('%Y-%m-%d')
    if email not in data["checkin_streak"]:
        data["checkin_streak"][email] = {"count": 0, "last_date": "", "best": 0}
    streak = data["checkin_streak"][email]
    if checkin_ok:
        yesterday = (now_bjt() - timedelta(days=1)).strftime('%Y-%m-%d')
        if streak["last_date"] == yesterday:
            streak["count"] += 1
        elif streak["last_date"] != today:
            streak["count"] = 1
        streak["last_date"] = today
        streak["best"] = max(streak["best"], streak["count"])
    else:
        streak["count"] = 0
    return streak

def format_streak(streak):
    """格式化连续签到信息"""
    count = streak.get("count", 0)
    best = streak.get("best", 0)
    if count >= 7:
        icon = "🔥"
    elif count >= 3:
        icon = "⭐"
    else:
        icon = "📅"
    return f"{icon} 连续签到: {count} 天 (最佳: {best} 天)"

# ================= 签到价值估算 =================

def calc_value(points):
    """估算签到价值（基于 GLaDOS 定价）"""
    # GLaDOS 定价: 100分=10天, 200分=30天, 500分=100天
    # 按最优比例: 500分=100天 → 1分=0.2天
    if not isinstance(points, int) or points <= 0:
        return "💰 价值: 暂无数据"
    days_equivalent = points * 0.2
    return f"💰 积分价值: 约 {days_equivalent:.0f} 天会员"

# ================= 天气 =================

WEATHER_CITY = "杭州"

def get_weather():
    """获取天气信息"""
    try:
        resp = requests.get(f"https://wttr.in/{WEATHER_CITY}?format=%C+%t&lang=zh", timeout=10)
        if resp.status_code == 200:
            weather = resp.text.strip()
            if weather and '?' not in weather:
                return f"🌤 {WEATHER_CITY}: {weather}"
        else:
            log(f"⚠️ 天气 API 返回: {resp.status_code}")
    except Exception as e:
        log(f"⚠️ 天气 API 请求失败: {e}")
    return None

# ================= 每日一句 =================

def get_quote():
    """获取每日一句（调用免费 API）"""
    try:
        resp = requests.get("https://v1.hitokoto.cn/?c=d&c=i&c=k&encode=json", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('hitokoto', '')
            source = data.get('from', '')
            author = data.get('from_who', '')
            if not content:
                return None
            if author and source:
                return f'📖 "{content}" —— {author}《{source}》'
            elif source:
                return f'📖 "{content}" —— 《{source}》'
            else:
                return f'📖 "{content}"'
        else:
            log(f"⚠️ 一言 API 返回: {resp.status_code}")
    except Exception as e:
        log(f"⚠️ 一言 API 请求失败: {e}")
    return None

def extract_cookie(raw: str):
    """提取 Cookie，支持 Cookie-Editor 冒号格式"""
    if not raw: return None
    raw = raw.strip()
    
    # Cookie-Editor 格式 (koa:sess=xxx; koa:sess.sig=yyy)
    if 'koa:sess=' in raw or 'koa:sess.sig=' in raw:
        return raw
        
    # JSON
    if raw.startswith('{'):
        try:
            return 'koa.sess=' + json.loads(raw).get('token')
        except: pass
        
    # JWT Token
    if raw.count('.') == 2 and '=' not in raw and len(raw) > 50:
        return 'koa:sess=' + raw
        
    # Standard
    return raw

def get_cookies():
    raw = os.environ.get("GLADOS_COOKIE", "")
    if not raw:
        log("❌ 未配置 GLADOS_COOKIE")
        return []
    
    # Split by enter or &
    sep = '\n' if '\n' in raw else '&'
    return [extract_cookie(c) for c in raw.split(sep) if c.strip()]

# ================= 核心逻辑 =================

class GLaDOS:
    def __init__(self, cookie):
        self.cookie = cookie
        self.domain = DOMAINS[0]
        self.email = "?"
        self.left_days = "?"
        self.points = "?"
        self.points_change = "?"
        self.exchange_info = ""
        self.plan = "?"
        self.plans_list = []  # 存储兑换计划列表
        
    def req(self, method, path, data=None):
        """带自动域名切换的请求"""
        for d in DOMAINS:
            try:
                url = f"{d}{path}"
                h = HEADERS.copy()
                h['Cookie'] = self.cookie
                h['Origin'] = d
                h['Referer'] = f"{d}/console/checkin"
                
                if method == 'GET':
                    resp = requests.get(url, headers=h, timeout=10)
                else:
                    resp = requests.post(url, headers=h, json=data, timeout=10)
                
                if resp.status_code == 200:
                    self.domain = d # Remember working domain
                    return resp.json()
            except Exception as e:
                log(f"⚠️ {d} 请求失败: {e}")
                continue
        return None

    def get_status(self):
        """获取状态：天数、邮箱"""
        res = self.req('GET', '/api/user/status')
        if res and 'data' in res:
            d = res['data']
            self.email = d.get('email', 'Unknown')
            self.left_days = str(d.get('leftDays', '?')).split('.')[0]
            return True
        return False

    def get_points(self):
        """获取积分、变化历史、兑换计划"""
        res = self.req('GET', '/api/user/points')
        if res and 'points' in res:
            # 当前积分
            self.points = str(res.get('points', '0')).split('.')[0]
            
            # 最近一次积分变化
            history = res.get('history', [])
            if history:
                last = history[0]
                change = str(last.get('change', '0')).split('.')[0]
                if not change.startswith('-'):
                    change = '+' + change
                self.points_change = change
            
            # 兑换计划
            plans = res.get('plans', {})
            pts = int(self.points)
            exchange_lines = []
            self.plans_list = []
            for plan_id, plan_data in plans.items():
                need = plan_data['points']
                days = plan_data['days']
                diff = need - pts
                if diff <= 0:
                    exchange_lines.append(f"✅ {need}分→{days}天 (可兑换)")
                    self.plans_list.append({'need': need, 'days': days, 'diff': 0, 'ready': True})
                else:
                    exchange_lines.append(f"❌ {need}分→{days}天 (差{diff}分)")
                    self.plans_list.append({'need': need, 'days': days, 'diff': diff, 'ready': False})
            self.exchange_info = "<br>".join(exchange_lines)
            return True
        return False

    def checkin(self):
        """执行签到"""
        return self.req('POST', '/api/user/checkin', {'token': 'glados.cloud'})

# ================= 主程序 =================

def serverchan(send_key, title, content):
    """Server酱推送（免费推送到微信公众号）"""
    if not send_key: return
    try:
        url = f"https://sctapi.ftqq.com/{send_key}.send"
        # Server酱用 desp 参数传内容，支持 Markdown
        desp = content.replace("<br>", "\n")
        desp = re.sub(r"<[^>]+>", "", desp)  # 去除所有 HTML 标签
        resp = requests.post(url, data={'title': title, 'desp': desp}, timeout=10)
        if resp.status_code == 200:
            log("✅ Server酱推送成功")
        else:
            log(f"❌ Server酱推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ Server酱推送失败: {e}")

def dingtalk(token, title, content):
    """钉钉机器人推送"""
    if not token: return
    try:
        url = f"https://oapi.dingtalk.com/robot/send?access_token={token}"
        # 清理 HTML 标签，保留纯文本
        text = content.replace("<br>", "\n")
        text = re.sub(r"<[^>]+>", "", text)
        msg = f"{title}\n\n{text}"
        data = {"msgtype": "text", "text": {"content": msg}}
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('errcode') == 0:
                log("✅ 钉钉推送成功")
            else:
                log(f"❌ 钉钉推送失败: {result.get('errmsg')}")
        else:
            log(f"❌ 钉钉推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ 钉钉推送失败: {e}")

def telegram_push(token, chat_id, title, content):
    """Telegram 推送（纯文本格式）"""
    if not token or not chat_id: return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = f"{title}\n\n{content}"
        data = {
            "chat_id": chat_id,
            "text": text
        }
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('ok'):
                log("✅ Telegram 推送成功")
            else:
                log(f"❌ Telegram 推送失败: {result.get('description')}")
        else:
            log(f"❌ Telegram 推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ Telegram 推送失败: {e}")

def send_alert(title, content):
    """发送过期/异常告警（仅推送到钉钉和Server酱）"""
    sc_key = os.environ.get("SEND_KEY")
    ding_token = os.environ.get("DINGTALK_TOKEN")
    if sc_key:
        serverchan(sc_key, title, content)
    if ding_token:
        dingtalk(ding_token, title, content)

def format_dingtalk_message(g, msg, checkin_ok, data, streak):
    """格式化推送消息（纯文本，美观排版）"""
    # 计算断粮日期
    try:
        days = int(g.left_days)
        expire_date = (now_bjt() + timedelta(days=days)).strftime('%Y-%m-%d')
    except:
        days = '?'
        expire_date = '?'

    # 状态判断
    if isinstance(days, int):
        if days > 30:
            day_status = "✅ 储备充足"
        elif days > 7:
            day_status = "⚠️ 即将到期"
        else:
            day_status = "🔴 紧急续期"
    else:
        day_status = "❓ 未知"

    # 签到结果
    checkin_icon = "✅" if checkin_ok else "❌"

    # 构建进度条
    progress_lines = []
    for p in g.plans_list:
        if p['ready']:
            bar = progress_bar(p['need'], p['need'])
            label = f"✅ 可兑换 {p['days']}天"
            progress_lines.append(f"{bar} [{label}]")
        else:
            bar = progress_bar(int(g.points) if g.points != '?' else 0, p['need'])
            label = f"积攒中 还差{p['diff']}分"
            progress_lines.append(f"{bar} {p['days']}天 [{label}]")

    progress_text = "\n".join(progress_lines) if progress_lines else "暂无兑换计划"

    # 积分趋势
    trend = format_trend(data, g.email)

    # 连续签到
    streak_text = format_streak(streak)

    # 签到价值
    try:
        pts = int(g.points)
    except:
        pts = 0
    value_text = calc_value(pts)

    # 时间
    now = now_bjt().strftime('%H:%M:%S')

    # 组装消息
    lines = [
        f"{get_greeting()}，这是您的资产简报",
        "",
        f"👤 账号: {mask_email(g.email)}",
        "",
        "━━━━━━ 📊 核心资产报告 ━━━━━━",
        "",
        f"💰 当前积分: {g.points} ({g.points_change})",
        f"⏳ 可用天数: {days} 天  {day_status}",
        f"📅 断粮日期: {expire_date}",
        f"{checkin_icon} 签到结果: {msg}",
        f"{streak_text}",
        f"{value_text}",
        "",
        "━━━━━━ 🎁 资产增值路径 ━━━━━━",
        "",
        progress_text,
        "",
        f"{trend}",
        "",
        f"🕒 更新于: {now}",
    ]

    return "\n".join(lines)

def format_summary(accounts):
    """格式化多账号汇总表"""
    if len(accounts) <= 1:
        return ""
    lines = [
        "",
        "━━━━━━ 📋 账号总览 ━━━━━━",
        "",
    ]
    for acc in accounts:
        icon = "✅" if acc['ok'] else "❌"
        lines.append(f"{icon} {mask_email(acc['email'])} | 积分:{acc['points']} | 天数:{acc['days']}")
    return "\n".join(lines)

def main():
    log("🚀 2026 GLaDOS Checkin Starting...")
    cookies = get_cookies()
    if not cookies:
        send_alert("⚠️ GLaDOS 配置异常", "未配置 GLADOS_COOKIE，请检查 GitHub Secrets。")
        sys.exit(1)

    # 加载历史数据
    data = load_data()

    results = []           # 美观纯文本格式（所有渠道统一）
    accounts = []          # 多账号汇总
    success_cnt = 0
    expired_cookies = []

    for i, cookie in enumerate(cookies, 1):
        g = GLaDOS(cookie)

        # 1. Checkin
        res = g.checkin()

        # 检测 Cookie 是否过期/无效
        if res is None:
            msg = "Cookie 已过期或网络异常"
            log(f"❌ 用户 {i}: 所有域名请求失败，Cookie 可能已过期")
            expired_cookies.append(i)
        elif 'Unauthorized' in str(res) or 'please checkin via' in str(res):
            msg = res.get('message', 'Unauthorized')
            log(f"❌ 用户 {i}: Cookie 已过期 - {msg}")
            expired_cookies.append(i)
        else:
            msg = res.get('message', 'Failure')

        # 2. Get Info (Refresh data)
        status_ok = g.get_status()
        if not status_ok and res is not None:
            log(f"⚠️ 用户 {i}: 获取状态失败，Cookie 可能已过期")
            if i not in expired_cookies:
                expired_cookies.append(i)

        g.get_points()

        # 3. Log
        checkin_ok = "Checkin" in msg
        log(f"用户: {g.email} | 积分: {g.points} | 天数: {g.left_days} | 结果: {msg}")

        if checkin_ok: success_cnt += 1

        # 4. 记录数据（积分趋势 + 连续签到）
        try:
            pts = int(g.points)
        except:
            pts = 0
        record_points(data, g.email, pts)
        streak = update_streak(data, g.email, checkin_ok)

        # 5. 统一纯文本格式
        results.append(format_dingtalk_message(g, msg, checkin_ok, data, streak))

        # 6. 多账号汇总数据
        accounts.append({
            'email': g.email,
            'points': g.points,
            'days': g.left_days,
            'ok': checkin_ok
        })

    # 保存历史数据
    save_data(data)
    log(f"📁 历史数据已保存")

    # 多账号汇总
    summary = format_summary(accounts)

    # Cookie 过期告警
    if expired_cookies:
        alert_content = (
            f"检测到 {len(expired_cookies)} 个账号的 Cookie 已过期或无效！\n\n"
            f"过期账号编号: {', '.join(str(i) for i in expired_cookies)}\n\n"
            f"请尽快处理：\n"
            f"1. 打开 https://glados.cloud 登录\n"
            f"2. 用 Cookie-Editor 复制新的 Cookie\n"
            f"3. 去 GitHub Secrets 更新 GLADOS_COOKIE"
        )
        log(f"⚠️ 检测到 {len(expired_cookies)} 个 Cookie 过期，发送告警...")
        send_alert("⚠️ GLaDOS Cookie 已过期", alert_content)

    # Push
    push_level = os.environ.get("PUSH_LEVEL", "all").lower()

    if push_level == "fail_only" and success_cnt == len(cookies):
        log("⏭️ 根据 PUSH_LEVEL=fail_only 设置，所有账号签到成功，跳过推送")
        return

    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    sc_key = os.environ.get("SEND_KEY")
    ding_token = os.environ.get("DINGTALK_TOKEN")

    if (tg_token and tg_chat_id) or sc_key or ding_token:
        title = f"GLaDOS签到: 成功{success_cnt}/{len(cookies)}"

        # 拼接所有内容
        text_content = "\n\n".join(results)
        if summary:
            text_content += summary

        # 天气 + 每日一句（始终显示）
        footer_parts = []
        weather = get_weather()
        if weather:
            footer_parts.append(weather)
        quote = get_quote()
        if quote:
            footer_parts.append(quote)
        if footer_parts:
            text_content += "\n\n━━━━━━ 🌤 生活资讯 ━━━━━━\n\n" + "\n".join(footer_parts)

        # Server酱
        if sc_key:
            serverchan(sc_key, title, text_content)

        # Telegram
        if tg_token and tg_chat_id:
            telegram_push(tg_token, tg_chat_id, title, text_content)

        # 钉钉
        if ding_token:
            dingtalk(ding_token, title, text_content)

if __name__ == '__main__':
    main()
