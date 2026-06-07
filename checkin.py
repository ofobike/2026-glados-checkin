#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 GLaDOS 自动签到 (积分增强版)

功能：
- 全自动签到
- 精准获取当前积分 (Points)
- Server酱/钉钉/Telegram/Bark 多渠道推送
- 积分趋势、连续签到、价值估算
- 签到热力图、本月统计、积分变化明细
- 会员到期预警、本次签到积分
- 签到成就系统、每日签到运势
- 积分预测、周报/月报
- 天气穿衣建议、假期倒计时、日出日落
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
import hashlib
import csv
from datetime import datetime, timedelta, date
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
            d = json.loads(DATA_FILE.read_text(encoding='utf-8'))
            # 兼容旧数据格式
            for key, default in [
                ("checkin_dates", {}),
                ("achievements", {}),
                ("checkin_times", {}),
            ]:
                if key not in d:
                    d[key] = default
            return d
        except:
            pass
    return {"points_history": {}, "checkin_streak": {}, "checkin_dates": {}, "achievements": {}, "checkin_times": {}}

def save_data(data):
    """保存历史数据"""
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def cleanup_old_data(data, keep_days=10):
    """清理超过 N 天的历史数据，防止文件过大"""
    cutoff = (now_bjt() - timedelta(days=keep_days)).strftime('%Y-%m-%d')
    cleaned = 0

    # 清理 points_history
    for email in data.get("points_history", {}):
        before = len(data["points_history"][email])
        data["points_history"][email] = [
            r for r in data["points_history"][email] if r.get("date", "") >= cutoff
        ]
        cleaned += before - len(data["points_history"][email])

    # 清理 checkin_dates
    for email in data.get("checkin_dates", {}):
        before = len(data["checkin_dates"][email])
        data["checkin_dates"][email] = [
            d for d in data["checkin_dates"][email] if d >= cutoff
        ]
        cleaned += before - len(data["checkin_dates"][email])

    # 清理 checkin_times
    for email in data.get("checkin_times", {}):
        before = len(data["checkin_times"][email])
        data["checkin_times"][email] = [
            r for r in data["checkin_times"][email] if r.get("date", "") >= cutoff
        ]
        cleaned += before - len(data["checkin_times"][email])

    if cleaned > 0:
        log(f"🧹 已清理 {cleaned} 条超过 {keep_days} 天的历史数据")
    return cleaned

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
    """格式化积分趋势（近7天 + ASCII 图表）"""
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

    # ASCII 趋势图
    points_list = [r["points"] for r in recent]
    min_pts = min(points_list)
    max_pts = max(points_list)
    chart_height = 3
    chart_width = len(points_list)
    if max_pts > min_pts:
        chart_lines = []
        for row in range(chart_height, 0, -1):
            threshold = min_pts + (max_pts - min_pts) * (row - 0.5) / chart_height
            line = ""
            for pts in points_list:
                if pts >= threshold:
                    line += "█ "
                else:
                    line += "  "
            chart_lines.append(line)
        dates = [r["date"][5:] for r in recent]  # MM-DD
        date_line = " ".join(d[:2] for d in dates)
        chart = "\n".join(chart_lines) + "\n" + date_line
        return f"{trend_icon} 近{len(recent)}天趋势: {' '.join(changes)} (共{'+' if total_change>=0 else ''}{total_change})\n{chart}"
    else:
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

# ================= 智能推荐 =================

def get_recommendation(data, email, points, plans_list):
    """根据积分增速推荐最优兑换方案"""
    history = data.get("points_history", {}).get(email, [])
    if len(history) < 2 or not plans_list:
        return None

    # 计算日均积分增速
    recent = history[-7:]
    if len(recent) < 2:
        return None
    total_change = recent[-1]["points"] - recent[0]["points"]
    days_span = len(recent) - 1
    daily_rate = total_change / days_span if days_span > 0 else 0

    if daily_rate <= 0:
        return "🎯 推荐: 积分增长较慢，建议坚持签到"

    # 找到最优兑换方案（性价比最高）
    best_plan = None
    best_ratio = 0
    for p in plans_list:
        if p['ready']:
            continue
        # 性价比 = 天数 / 所需积分
        ratio = p['days'] / p['need'] if p['need'] > 0 else 0
        if ratio > best_ratio:
            best_ratio = ratio
            best_plan = p

    if not best_plan:
        return "🎯 推荐: 所有方案均可兑换！"

    days_needed = best_plan['diff'] / daily_rate
    target_date = (now_bjt() + timedelta(days=days_needed)).strftime('%Y-%m-%d')
    return f"🎯 最优方案: {best_plan['need']}分兑换{best_plan['days']}天 (性价比{best_ratio:.2f})\n   预计 {target_date} 达成 (还需{best_plan['diff']}分, 日均+{daily_rate:.0f}分)"

# ================= 下次签到提醒 =================

def get_next_checkin():
    """获取下次签到时间（支持自定义签到时间）"""
    # 从环境变量读取自定义签到时间，格式 "09:30,21:30"
    custom = os.environ.get("CHECKIN_HOURS", "09:30,21:30")
    try:
        times = []
        for t in custom.split(","):
            h, m = t.strip().split(":")
            times.append((int(h), int(m)))
        times.sort()
    except:
        times = [(9, 30), (21, 30)]

    now = now_bjt()
    for h, m in times:
        if now.hour < h or (now.hour == h and now.minute < m):
            return f"⏰ 下次签到: 今天 {h:02d}:{m:02d}"
    # 所有时间都过了，显示明天第一个
    h, m = times[0]
    return f"⏰ 下次签到: 明天 {h:02d}:{m:02d}"

# ================= 签到热力图 =================

def record_checkin_date(data, email):
    """记录今日签到（日期+时间）"""
    today = now_bjt().strftime('%Y-%m-%d')
    if email not in data["checkin_dates"]:
        data["checkin_dates"][email] = []
    dates = data["checkin_dates"][email]
    if today not in dates:
        dates.append(today)
    # 只保留最近60天
    data["checkin_dates"][email] = dates[-60:]
    # 记录签到时间
    record_checkin_time(data, email)

def format_heatmap(data, email):
    """生成近30天签到热力图（ASCII）"""
    dates_set = set(data.get("checkin_dates", {}).get(email, []))
    if not dates_set:
        return "🗓 签到日历: 数据积累中"

    today = now_bjt().date()
    # 最近30天
    days = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        days.append(d)

    # 按周排列（周一开始）
    # 找到30天前的周一
    first_day = days[0]
    start_monday = first_day - timedelta(days=first_day.weekday())

    # 构建日历网格
    week_labels = ["一", "二", "三", "四", "五", "六", "日"]
    grid = {}  # (week, weekday) -> date

    current = start_monday
    week_num = 0
    while current <= today:
        wd = current.weekday()
        grid[(week_num, wd)] = current
        if wd == 6:  # 周日，换下一周
            week_num += 1
        current += timedelta(days=1)

    total_weeks = week_num + 1

    # 绘制热力图
    lines = ["🗓 近30天签到日历:"]
    lines.append("    " + "  ".join(week_labels))

    for w in range(total_weeks):
        row = ""
        for wd in range(7):
            d = grid.get((w, wd))
            if d is None:
                row += "  "
            elif d > today:
                row += "  "
            elif d.strftime('%Y-%m-%d') in dates_set:
                row += "🟢"
            else:
                row += "⬜"
            if wd < 6:
                row += " "
        # 显示该周的月份（如果是该月第一周）
        lines.append(row)

    # 统计
    checked = sum(1 for d in dates_set if (today - timedelta(days=29)) <= datetime.strptime(d, '%Y-%m-%d').date() <= today)
    lines.append(f"近30天签到: {checked}/30 天 ({checked*100//30}%)")
    return "\n".join(lines)

# ================= 本月签到统计 =================

def format_monthly_stats(data, email):
    """本月签到统计"""
    dates_list = data.get("checkin_dates", {}).get(email, [])
    if not dates_list:
        return "📅 本月签到: 数据积累中"

    today = now_bjt().date()
    month_start = today.replace(day=1)
    month_prefix = today.strftime('%Y-%m')

    month_dates = [d for d in dates_list if d.startswith(month_prefix)]
    month_days = (today - month_start).days + 1
    checked = len(month_dates)
    rate = checked * 100 // month_days if month_days > 0 else 0

    # 签到率条形图
    bar_width = 10
    filled = round(rate / 100 * bar_width)
    bar = "▓" * filled + "░" * (bar_width - filled)

    return f"📅 本月签到: {checked}/{month_days} 天 [{bar}] {rate}%"

# ================= 历史最高积分 =================

def get_max_points(data, email):
    """获取历史最高积分"""
    history = data.get("points_history", {}).get(email, [])
    if not history:
        return None
    return max(r["points"] for r in history)

# ================= 会员续期预警 =================

def format_renewal_alert(days):
    """会员续期倒计时预警"""
    if not isinstance(days, int):
        return ""
    if days <= 3:
        return f"🚨 紧急！仅剩 {days} 天到期，请立即续期！\n   👉 打开 https://glados.cloud → Console → Renew"
    elif days <= 7:
        return f"⚠️ 警告！{days} 天后到期，建议尽快续期\n   👉 打开 https://glados.cloud → Console → Renew"
    elif days <= 14:
        return f"💡 提醒：{days} 天后到期，可提前规划续期"
    return ""

# ================= 天气 =================

WEATHER_CITY = os.environ.get("WEATHER_CITY", "杭州")

def get_weather():
    """获取天气信息"""
    try:
        resp = requests.get(f"https://wttr.in/{WEATHER_CITY}?format=%C+%t&lang=zh&m", timeout=10)
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

# ================= 每日签到运势 =================

FORTUNE_LIST = [
    ("大吉 🎉", "今日签到如有神助，积分翻倍不是梦！"),
    ("大吉 🌟", "紫气东来，签到顺利，会员指日可待！"),
    ("中吉 😊", "稳中有进，坚持签到，好事自然来。"),
    ("中吉 🍀", "运气不错，签到顺畅，今天适合摸鱼。"),
    ("小吉 🙂", "平淡是真，签到打卡，日积月累见成效。"),
    ("小吉 ☕", "签到顺利，适合喝杯咖啡犒劳自己。"),
    ("吉 😌", "签到完成，运势平稳，保持节奏即可。"),
    ("末吉 😅", "签到虽迟但到，明天记得早点签！"),
]

def get_daily_fortune():
    """根据日期生成每日运势（同一天结果相同）"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(today.encode()).hexdigest()[:8], 16)
    idx = seed % len(FORTUNE_LIST)
    rank, msg = FORTUNE_LIST[idx]
    return f"🎰 今日运势: {rank}\n   {msg}"

# ================= 签到等级系统 =================

LEVELS = [
    (0,    "🌱 青铜", "萌新签到者"),
    (7,    "🌿 白银", "签到新手"),
    (30,   "⚔️ 黄金", "签到达人"),
    (90,   "💎 铂金", "签到精英"),
    (180,  "👑 钻石", "签到大师"),
    (365,  "🏆 王者", "签到传说"),
    (500,  "🌟 超凡", "签到之神"),
    (1000, "🔮 永恒", "签到不朽"),
]

def get_level(data, email):
    """根据累计签到天数获取等级"""
    total_days = len(data.get("checkin_dates", {}).get(email, []))
    current_level = LEVELS[0]
    next_level = None
    for i, (threshold, name, title) in enumerate(LEVELS):
        if total_days >= threshold:
            current_level = (threshold, name, title)
            if i + 1 < len(LEVELS):
                next_level = LEVELS[i + 1]
        else:
            if next_level is None:
                next_level = (threshold, name, title)
            break

    _, name, title = current_level
    result = f"🎮 等级: {name} · {title} (累计{total_days}天)"

    if next_level:
        next_threshold, next_name, _ = next_level
        remaining = next_threshold - total_days
        progress = total_days - current_level[0]
        span = next_threshold - current_level[0]
        bar_width = 8
        filled = round(progress / span * bar_width) if span > 0 else bar_width
        bar = "▓" * filled + "░" * (bar_width - filled)
        result += f"\n   [{bar}] 距{next_name}还需 {remaining} 天"

    return result

# ================= ASCII Art 签到庆祝 =================

def get_ascii_celebration(checkin_ok, earned_points):
    """签到成功时显示庆祝 ASCII Art"""
    if not checkin_ok:
        return ""

    arts = [
        # 大吉大利
        "  ╔══════════════════════════╗\n"
        "  ║   🎉  签 到 成 功  🎉    ║\n"
        "  ║                          ║\n"
        "  ║    ★  +1 +1 +1 +1  ★    ║\n"
        "  ║                          ║\n"
        "  ╚══════════════════════════╝",

        # 荣耀
        "  ┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        "  ┃   🏆  今 日 荣 耀  🏆   ┃\n"
        "  ┃                          ┃\n"
        "  ┃   ⚡ 签到成功 ⚡         ┃\n"
        "  ┃   积分 +1 +1 +1         ┃\n"
        "  ┗━━━━━━━━━━━━━━━━━━━━━━━━┛",

        # 胜利
        "  ╭──────────────────────────╮\n"
        "  │   🌟  V I C T O R Y  🌟  │\n"
        "  │                          │\n"
        "  │   ✨ 每日签到完成 ✨      │\n"
        "  │   坚持就是胜利！         │\n"
        "  ╰──────────────────────────╯",
    ]

    # 根据日期选择不同的 Art
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(today.encode()).hexdigest()[:8], 16)
    art = arts[seed % len(arts)]

    if earned_points and earned_points > 0:
        art += f"\n   💰 本次获得 +{earned_points} 积分！"

    return art

# ================= 农历日期 =================

# 2026-2027 农历数据（压缩格式：月份|日|农历月|农历日|节气）
# 简化版：只提供节气和重要农历节日
LUNAR_SOLAR_TERMS_2026 = [
    ("01-05", "小寒"), ("01-20", "大寒"),
    ("02-04", "立春"), ("02-18", "雨水"),
    ("03-05", "惊蛰"), ("03-20", "春分"),
    ("04-04", "清明"), ("04-20", "谷雨"),
    ("05-05", "立夏"), ("05-21", "小满"),
    ("06-05", "芒种"), ("06-21", "夏至"),
    ("07-07", "小暑"), ("07-22", "大暑"),
    ("08-07", "立秋"), ("08-23", "处暑"),
    ("09-07", "白露"), ("09-23", "秋分"),
    ("10-08", "寒露"), ("10-23", "霜降"),
    ("11-07", "立冬"), ("11-22", "小雪"),
    ("12-07", "大雪"), ("12-22", "冬至"),
]

LUNAR_FESTIVALS = [
    ("01-01", "元旦"),
    ("02-17", "除夕"),
    ("02-18", "春节"),
    ("03-08", "妇女节"),
    ("04-05", "清明节"),
    ("05-01", "劳动节"),
    ("05-31", "端午节"),
    ("06-01", "儿童节"),
    ("08-25", "七夕"),
    ("09-27", "中秋节"),
    ("10-01", "国庆节"),
    ("10-18", "重阳节"),
    ("12-25", "圣诞节"),
]

def get_lunar_info():
    """获取今日农历/节气/节日信息"""
    today = now_bjt().date()
    mm_dd = today.strftime('%m-%d')

    parts = []

    # 检查节气
    for date_str, term in LUNAR_SOLAR_TERMS_2026:
        if date_str == mm_dd:
            parts.append(f"🌿 今日节气: {term}")

    # 检查节日
    for date_str, festival in LUNAR_FESTIVALS:
        if date_str == mm_dd:
            parts.append(f"🎊 今日节日: {festival}")

    # 检查临近节气（前后1天）
    if not parts:
        for date_str, term in LUNAR_SOLAR_TERMS_2026:
            term_date = datetime.strptime(f"2026-{date_str}", '%Y-%m-%d').date()
            diff = (term_date - today).days
            if diff == 1:
                parts.append(f"🌿 明日节气: {term}")
                break
            elif diff == -1:
                parts.append(f"🌿 昨日节气: {term}")
                break

    # 农历日期（简化：使用天干地支纪日）
    # 用日期偏移计算一个简化的农历日
    heavenly_stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    earthly_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    animals = ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"]

    # 2026年是丙午年（马年）
    year_idx = (2026 - 4) % 12  # 以公元4年为甲子年
    stem = heavenly_stems[(2026 - 4) % 10]
    branch = earthly_branches[year_idx]
    animal = animals[year_idx]
    parts.append(f"🏮 {stem}{branch}年 · {animal}年")

    return "\n".join(parts) if parts else ""

# ================= 每日英语名言 =================

# 备用名言（API 失败时使用）
FALLBACK_QUOTES = [
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("The journey of a thousand miles begins with a single step.", "Lao Tzu"),
    ("In the middle of difficulty lies opportunity.", "Albert Einstein"),
]

def get_daily_quote_en():
    """获取每日英语名言（调用 Quotable 免费 API）"""
    # 1. 尝试 Quotable API
    try:
        resp = requests.get("https://api.quotable.io/random", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            content = data.get('content', '')
            author = data.get('author', 'Unknown')
            if content:
                return f'💬 "{content}"\n   —— {author}'
    except Exception as e:
        log(f"⚠️ Quotable API 请求失败: {e}")

    # 2. 备用：硬编码名言（根据日期选择，同一天结果相同）
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("en" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(FALLBACK_QUOTES)
    quote, author = FALLBACK_QUOTES[idx]
    return f'💬 "{quote}"\n   —— {author}'

# ================= 今日头条新闻 =================

def get_daily_news():
    """获取今日热点新闻（调用免费 API）"""
    apis = [
        ("https://api.03c3.cn/api/zb", "03c3"),
        ("https://tenapi.cn/v2/toutiao", "tenapi"),
    ]
    for url, name in apis:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # 适配不同 API 格式
                items = data.get("data", data.get("list", []))
                if isinstance(items, list) and len(items) > 0:
                    lines = ["📰 今日头条:"]
                    for item in items[:3]:
                        title = item.get("title", item.get("name", ""))
                        if title:
                            lines.append(f"  • {title[:40]}")
                    if len(lines) > 1:
                        return "\n".join(lines)
        except Exception as e:
            log(f"⚠️ 新闻 API ({name}) 请求失败: {e}")
            continue
    return ""

# ================= 加密货币/汇率 =================

def get_crypto_forex():
    """获取加密货币价格和美元汇率"""
    parts = []

    # 加密货币（CoinGecko 免费 API）
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true",
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            btc = data.get("bitcoin", {})
            eth = data.get("ethereum", {})
            if btc:
                btc_price = btc.get("usd", 0)
                btc_change = btc.get("usd_24h_change", 0)
                btc_icon = "📈" if btc_change >= 0 else "📉"
                parts.append(f"₿ BTC: ${btc_price:,.0f} {btc_icon}{btc_change:+.1f}%")
            if eth:
                eth_price = eth.get("usd", 0)
                eth_change = eth.get("usd_24h_change", 0)
                eth_icon = "📈" if eth_change >= 0 else "📉"
                parts.append(f"Ξ ETH: ${eth_price:,.0f} {eth_icon}{eth_change:+.1f}%")
    except Exception as e:
        log(f"⚠️ CoinGecko API 请求失败: {e}")

    # 美元汇率
    try:
        resp = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            cny = data.get("rates", {}).get("CNY", 0)
            if cny:
                parts.append(f"💵 USD/CNY: {cny:.2f}")
    except Exception as e:
        log(f"⚠️ 汇率 API 请求失败: {e}")

    if parts:
        return "💰 行情速报:\n  " + "\n  ".join(parts)
    return ""

# ================= 每日健康提示 =================

HEALTH_TIPS = {
    "hot": [
        "🌡️ 高温天气，记得多喝水，避免中暑",
        "☀️ 紫外线强，出门记得涂防晒霜",
        "🍉 多吃西瓜、黄瓜等含水量高的水果",
    ],
    "warm": [
        "🌿 天气舒适，适合户外运动",
        "💧 每天保持 8 杯水的饮水量",
        "🏃 下午 4-6 点是最佳运动时间",
    ],
    "cool": [
        "🧣 天气转凉，注意保暖防感冒",
        "🍵 适合喝杯热茶暖暖身子",
        "😴 早睡早起，保持充足睡眠",
    ],
    "cold": [
        "❄️ 寒冷天气，注意防寒保暖",
        "🧤 外出记得戴手套围巾",
        "🍲 多喝热汤，增强免疫力",
    ],
}

def get_health_tip(weather_text):
    """根据天气和季节推送健康提示"""
    # 根据温度分类
    category = "warm"
    if weather_text:
        match = re.search(r'([+-]?\d+)\s*°?[CcFf]', weather_text)
        if match:
            temp = int(match.group(1))
            if '°F' in weather_text or '°f' in weather_text:
                temp = (temp - 32) * 5 // 9
            if temp >= 30:
                category = "hot"
            elif temp >= 20:
                category = "warm"
            elif temp >= 10:
                category = "cool"
            else:
                category = "cold"

    # 根据日期选择（同一天结果相同）
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("health" + today).encode()).hexdigest()[:8], 16)
    tips = HEALTH_TIPS[category]
    tip = tips[seed % len(tips)]
    return f"🏋️ 健康提示: {tip}"

# ================= 每日电影推荐 =================

def get_movie_recommendation():
    """获取每日电影推荐（调用免费 API）"""
    try:
        resp = requests.get("https://movie.douban.com/j/search_subjects?type=movie&tag=%E7%83%AD%E9%97%A8&page_limit=20&page_start=0", timeout=10,
                           headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            data = resp.json()
            subjects = data.get("subjects", [])
            if subjects:
                today = now_bjt().strftime('%Y-%m-%d')
                seed = int(hashlib.md5(("movie" + today).encode()).hexdigest()[:8], 16)
                movie = subjects[seed % len(subjects)]
                title = movie.get("title", "")
                rate = movie.get("rate", "")
                return f"🎬 今日推荐: 《{title}》 ⭐{rate}"
    except Exception as e:
        log(f"⚠️ 电影 API 请求失败: {e}")
    return ""

# ================= 签到时间分布 =================

def record_checkin_time(data, email):
    """记录签到时间（小时）"""
    hour = now_bjt().hour
    if email not in data.get("checkin_times", {}):
        if "checkin_times" not in data:
            data["checkin_times"] = {}
        data["checkin_times"][email] = []
    data["checkin_times"][email].append({
        "date": now_bjt().strftime('%Y-%m-%d'),
        "hour": hour
    })

def format_time_distribution(data, email):
    """统计签到时间分布"""
    times = data.get("checkin_times", {}).get(email, [])
    if len(times) < 3:
        return ""

    # 统计各时段
    morning = sum(1 for t in times if 5 <= t["hour"] < 12)
    afternoon = sum(1 for t in times if 12 <= t["hour"] < 18)
    evening = sum(1 for t in times if 18 <= t["hour"] < 23)
    night = sum(1 for t in times if t["hour"] >= 23 or t["hour"] < 5)
    total = len(times)

    # 找出最常签到的时段
    periods = [("🌅 早鸟", morning), ("☀️ 午间", afternoon), ("🌆 傍晚", evening), ("🌙 夜猫", night)]
    best = max(periods, key=lambda x: x[1])

    if best[1] == 0:
        return ""

    pct = best[1] * 100 // total
    return f"⏰ 签到习惯: {best[0]}型 ({pct}%在该时段签到)"

# ================= 签到率趋势 =================

def format_checkin_rate_trend(data, email):
    """近4周签到率趋势"""
    dates_set = set(data.get("checkin_dates", {}).get(email, []))
    if not dates_set:
        return ""

    today = now_bjt().date()
    weeks = []
    for w in range(3, -1, -1):
        week_start = today - timedelta(days=today.weekday() + 7 * w)
        week_checked = 0
        for d in range(7):
            day = week_start + timedelta(days=d)
            if day > today:
                break
            if day.strftime('%Y-%m-%d') in dates_set:
                week_checked += 1
            week_days = d + 1
        if w == 0:
            rate = week_checked * 100 // week_days if week_days > 0 else 0
        else:
            rate = week_checked * 100 // 7
        weeks.append(rate)

    # ASCII 趋势
    icons = []
    for i in range(1, len(weeks)):
        if weeks[i] > weeks[i-1]:
            icons.append("📈")
        elif weeks[i] < weeks[i-1]:
            icons.append("📉")
        else:
            icons.append("➡️")

    trend_str = " ".join(icons) if icons else ""
    return f"📉 签到率趋势: {' → '.join(f'{r}%' for r in weeks)} {trend_str}"

# ================= 月度目标 =================

MONTHLY_GOAL = int(os.environ.get("MONTHLY_GOAL", "25"))  # 默认目标：每月签到25天

def format_monthly_goal(data, email):
    """月度签到目标进度"""
    dates_list = data.get("checkin_dates", {}).get(email, [])
    today = now_bjt().date()
    month_prefix = today.strftime('%Y-%m')
    month_start = today.replace(day=1)
    month_days = (today - month_start).days + 1

    month_dates = [d for d in dates_list if d.startswith(month_prefix)]
    checked = len(month_dates)

    # 计算需要在剩余天数内完成
    remaining_days = 30 - month_days  # 大约剩余天数
    needed = MONTHLY_GOAL - checked
    if needed <= 0:
        bar = "▓" * 10
        return f"🎯 月度目标: {checked}/{MONTHLY_GOAL} 天 [{bar}] 🎉 已达成！"
    elif needed > remaining_days and remaining_days > 0:
        bar_filled = round(checked / MONTHLY_GOAL * 10)
        bar = "▓" * bar_filled + "░" * (10 - bar_filled)
        return f"🎯 月度目标: {checked}/{MONTHLY_GOAL} 天 [{bar}] ⚠️ 需每天签到"
    else:
        bar_filled = round(checked / MONTHLY_GOAL * 10)
        bar = "▓" * bar_filled + "░" * (10 - bar_filled)
        return f"🎯 月度目标: {checked}/{MONTHLY_GOAL} 天 [{bar}] 还需{needed}天"

# ================= 签到小游戏 =================

def get_mini_game():
    """签到小游戏：猜数字"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("game" + today).encode()).hexdigest()[:8], 16)
    lucky_num = (seed % 10) + 1  # 1-10

    # 根据小时生成"猜测"
    hour = now_bjt().hour
    guess = (hour % 10) + 1

    if guess == lucky_num:
        return f"🎲 签到小游戏: 今日幸运数字 {lucky_num}，你猜的 {guess} 命中了！🎉 大吉大利！"
    else:
        diff = abs(guess - lucky_num)
        if diff <= 2:
            return f"🎲 签到小游戏: 今日幸运数字 {lucky_num}，你猜的 {guess}，差一点！😅"
        else:
            return f"🎲 签到小游戏: 今日幸运数字 {lucky_num}，你猜的 {guess}，明天再试试！"

# ================= 签到日记 =================

MOOD_NOTE = os.environ.get("MOOD_NOTE", "")

def get_mood_note():
    """获取签到日记（通过环境变量配置）"""
    if MOOD_NOTE:
        return f"📝 今日心情: {MOOD_NOTE}"
    return ""

# ================= 世界问候语 =================

WORLD_GREETINGS = [
    ("🇯🇵 こんにちは", "日语 - 你好"),
    ("🇰🇷 안녕하세요", "韩语 - 你好"),
    ("🇫🇷 Bonjour", "法语 - 你好"),
    ("🇩🇪 Guten Tag", "德语 - 你好"),
    ("🇪🇸 ¡Hola!", "西班牙语 - 你好"),
    ("🇮🇹 Ciao", "意大利语 - 你好"),
    ("🇷🇺 Привет", "俄语 - 你好"),
    ("🇧🇷 Olá", "葡萄牙语 - 你好"),
    ("🇸🇦 مرحبا", "阿拉伯语 - 你好"),
    ("🇮🇳 नमस्ते", "印地语 - 你好"),
    ("🇹🇭 สวัสดี", "泰语 - 你好"),
    ("🇻🇳 Xin chào", "越南语 - 你好"),
]

def get_world_greeting():
    """每日世界问候语"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("greet" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(WORLD_GREETINGS)
    greeting, lang = WORLD_GREETINGS[idx]
    return f"🌍 今日问候: {greeting} ({lang})"

# ================= 服务器状态 =================

def get_server_status():
    """获取运行环境信息"""
    import platform
    parts = [
        f"🐍 Python {platform.python_version()}",
        f"💻 {platform.system()} {platform.machine()}",
    ]
    return "🔋 运行环境: " + " | ".join(parts)

# ================= 历史上的今天 =================

def get_today_in_history():
    """获取历史上的今天（调用免费 API）"""
    try:
        resp = requests.get("https://api.oick.cn/lishi/api.php", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("data", data.get("result", []))
            if isinstance(items, list) and len(items) > 0:
                today = now_bjt().strftime('%m月%d日')
                lines = [f"📅 历史上的今天 ({today}):"]
                for item in items[:3]:
                    title = item.get("title", item.get("event", ""))
                    if title:
                        lines.append(f"  • {title[:50]}")
                if len(lines) > 1:
                    return "\n".join(lines)
    except Exception as e:
        log(f"⚠️ 历史上的今天 API 请求失败: {e}")
    return ""

# ================= 土味情话 =================

SWEET_NOTHINGS = [
    "你知道你和星星的区别吗？星星点亮了黑夜，而你点亮了我的心 ✨",
    "我这个人没什么出息，就想花你的钱，睡你的床，做你的老婆 💕",
    "你猜我的心在哪边？左边？不对，在你那边 💗",
    "我觉得你好像一款游戏——我的世界 🎮",
    "你知道我最大的缺点是什么吗？是缺点你 💫",
    "我想在你那里买一块地——你的死心塌地 🏠",
    "你闻到空气中有什么味道吗？没有？那就是我对你的爱意弥漫在空气中 🌸",
    "你累不累啊？你都在我心里跑了一天了 🏃",
    "我怀疑你的本质是一本书，不然为什么让我越看越想睡（想和你一起睡）📖",
    "你知道你和猴子的区别吗？猴子住在山洞里，而你住在我心里 🐵",
    "你是哪里人？你是我的心上人 💝",
    "我有超能力——超级喜欢你 🦸",
    "你猜我想喝什么？我想呵护你 🥤",
    "我对你的爱就像拖拉机上山——轰轰烈烈 🚜",
    "你知道我的缺点是什么吗？缺点你 😘",
]

def get_sweet_nothing():
    """获取每日土味情话"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("sweet" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(SWEET_NOTHINGS)
    return f"💕 {SWEET_NOTHINGS[idx]}"

# ================= 彩虹屁 =================

RAINBOW_FARTS = [
    "你今天的气色真好，是不是偷偷变好看了？🌈",
    "你笑起来的样子，比今天的天气还晴朗 ☀️",
    "你就是那种让人一看就觉得世界美好的人 🌟",
    "你今天穿的衣服真好看，是你自己选的吗？太有品味了 👗",
    "你的存在本身就是一种治愈 🌻",
    "你认真做事的样子真的好帅/好美 💪",
    "你就是行走的正能量，走到哪里亮到哪里 ✨",
    "和你说话心情就会变好，你是不是有什么魔法？🪄",
    "你的眼光真好，不然怎么会选择关注我呢？😏",
    "你今天也辛苦了，记得对自己好一点哦 💖",
    "你的审美真的很在线，每次都很有品位 🎨",
    "你这么优秀，一定很累吧？今天也要好好休息哦 🌙",
    "你是我见过的最努力的人，未来一定可期 🚀",
    "你说话真好听，应该去做播客 🎙️",
    "你今天的状态看起来很棒，继续保持！💪",
]

def get_rainbow_fart():
    """获取每日彩虹屁"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("rainbow" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(RAINBOW_FARTS)
    return f"🌈 {RAINBOW_FARTS[idx]}"

# ================= 星座运势 =================

ZODIAC_SIGNS = [
    ("摩羯座", 1, 19), ("水瓶座", 2, 18), ("双鱼座", 3, 20),
    ("白羊座", 4, 19), ("金牛座", 5, 20), ("双子座", 6, 21),
    ("巨蟹座", 7, 22), ("狮子座", 8, 22), ("处女座", 9, 22),
    ("天秤座", 10, 23), ("天蝎座", 11, 21), ("射手座", 12, 21),
]

HOROSCOPE_TEXT = {
    "love": ["桃花运旺盛，单身者有机会遇到心仪对象 💕", "感情平稳，适合与伴侣共度温馨时光", "感情上需要多沟通，避免误会", "魅力四射，异性缘不错哦 💗", "适合表白或制造浪漫惊喜 🌹"],
    "work": ["工作顺利，有贵人相助 💼", "适合处理重要事务，效率很高", "注意细节，避免粗心大意", "有新的机会出现，要主动把握 🚀", "团队合作顺利，得到同事认可"],
    "money": ["财运不错，可能有意外收入 💰", "理性消费，避免冲动购物", "适合做理财规划", "偏财运一般，不宜投机", "正财运稳定，收支平衡"],
    "health": ["身体状态良好，精力充沛 💪", "注意休息，避免熬夜", "适合运动锻炼，增强体质", "注意饮食健康，少吃油腻", "心情舒畅，保持乐观心态 😊"],
}

ZODIAC_LUCKY = ["大吉 🎉", "中吉 😊", "小吉 🙂", "吉 😌", "末吉 😅"]
ZODIAC_LUCKY_NUM = list(range(1, 10))
ZODIAC_COLORS = ["红色 🔴", "蓝色 🔵", "绿色 🟢", "黄色 🟡", "紫色 🟣", "白色 ⚪", "橙色 🟠"]

def get_zodiac_horoscope(birthday=None):
    """获取星座运势（通过 ZODIAC_SIGN 环境变量配置星座）"""
    sign_name = os.environ.get("ZODIAC_SIGN", "水瓶座")
    if not sign_name and birthday:
        # 从生日推算星座
        try:
            month, day = int(birthday[:2]), int(birthday[2:])
            for name, m, d in ZODIAC_SIGNS:
                if (month == m and day <= d) or (month == m - 1 and day > d):
                    sign_name = name
                    break
        except:
            pass
    if not sign_name:
        return ""

    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5((sign_name + today).encode()).hexdigest()[:8], 16)

    love = HOROSCOPE_TEXT["love"][seed % len(HOROSCOPE_TEXT["love"])]
    work = HOROSCOPE_TEXT["work"][(seed + 1) % len(HOROSCOPE_TEXT["work"])]
    money = HOROSCOPE_TEXT["money"][(seed + 2) % len(HOROSCOPE_TEXT["money"])]
    health = HOROSCOPE_TEXT["health"][(seed + 3) % len(HOROSCOPE_TEXT["health"])]
    lucky = ZODIAC_LUCKY[(seed + 4) % len(ZODIAC_LUCKY)]
    lucky_num = ZODIAC_LUCKY_NUM[(seed + 5) % len(ZODIAC_LUCKY_NUM)]
    color = ZODIAC_COLORS[(seed + 6) % len(ZODIAC_COLORS)]

    lines = [
        f"♈ {sign_name} 今日运势 ({lucky})",
        f"  💕 爱情: {love}",
        f"  💼 事业: {work}",
        f"  💰 财运: {money}",
        f"  💪 健康: {health}",
        f"  🍀 幸运数字: {lucky_num} | 幸运颜色: {color}",
    ]
    return "\n".join(lines)

# ================= 每日段子 =================

DAILY_JOKES = [
    "为什么程序员总是分不清万圣节和圣诞节？因为 Oct 31 == Dec 25 🎃",
    "老婆给当程序员的老公打电话：下班顺路买一斤包子，如果看到卖西瓜的，就买一个。晚上老公手捧一个包子进了家门... 🍞",
    "医生：你的病很严重。病人：我想看看其他医生。医生：你没机会了，其他医生都说你没救了 😂",
    "问：如何让一只猫喵喵叫？答：在它面前放一个黄瓜 🥒",
    "面试官：你最大的缺点是什么？我：太诚实了。面试官：我不觉得这是缺点。我：我不在乎你怎么想 😏",
    "我问风扇我丑吗，它摇了一晚上的头 🌬️",
    "今天去买菜，老板说一斤10块，我说便宜点，老板说：那就两斤20吧 🥬",
    "朋友说带我去蹦极，我说我恐高，他说没事，掉下去就不恐了 🪂",
    "我妈说我不是亲生的，是从垃圾桶捡来的。我说难怪我这么能装 🗑️",
    "我曾经也有过梦想，只是后来睡着了 💤",
    "别人都是笑起来很好看，而你是看起来很好笑 😄",
    "我的钱包就像洋葱，每次打开都让我泪流满面 😭",
    "减肥就是：今天开始，明天继续，后天再说 🍔",
    "人生就像愤怒的小鸟，当你失败时，总有几头猪在笑 🐷",
    "早起的鸟儿有虫吃，早起的虫儿被鸟吃 🐛",
]

def get_daily_joke():
    """获取每日段子"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("joke" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(DAILY_JOKES)
    return f"😂 {DAILY_JOKES[idx]}"

# ================= 脑筋急转弯 =================

RIDDLES = [
    {"q": "什么东西越洗越脏？", "a": "水 💧"},
    {"q": "什么东西有头没有脚？", "a": "砖头 🧱"},
    {"q": "什么东西有嘴不说话？", "a": "茶壶 🫖"},
    {"q": "什么房子没人住？", "a": "蜂房 🐝"},
    {"q": "什么门关不上？", "a": "球门 ⚽"},
    {"q": "什么书买不到？", "a": "遗书 📜"},
    {"q": "什么水不能喝？", "a": "薪水 💸"},
    {"q": "什么桥不能走？", "a": "鼻梁桥 👃"},
    {"q": "什么蛋不能吃？", "a": "笨蛋 🤪"},
    {"q": "什么鱼不能吃？", "a": "木鱼 🪵"},
    {"q": "什么海没有水？", "a": "辞海 📖"},
    {"q": "什么花不能摸？", "a": "火花 🔥"},
    {"q": "什么路最窄？", "a": "冤家路窄 🛤️"},
    {"q": "什么锁没有孔？", "a": "密码锁 🔐"},
    {"q": "什么帽不能戴？", "a": "螺帽 🔩"},
]

def get_riddle():
    """获取每日脑筋急转弯"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("riddle" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(RIDDLES)
    r = RIDDLES[idx]
    return f"🧩 脑筋急转弯: {r['q']}\n   答案: {r['a']}"

# ================= 每日成语 =================

DAILY_IDIOMS = [
    ("画龙点睛", "比喻写文章或说话时，在关键处加上精辟的话使内容更加生动。"),
    ("守株待兔", "比喻不主动努力，而存万一的侥幸心理，希望得到意外的收获。"),
    ("破釜沉舟", "比喻下定决心，不留退路，非达目的决不罢休。"),
    ("卧薪尝胆", "形容人刻苦自励，发愤图强。"),
    ("望梅止渴", "比喻用空想或空话来安慰自己。"),
    ("掩耳盗铃", "比喻自己欺骗自己，明明掩盖不了的事偏要设法掩盖。"),
    ("刻舟求剑", "比喻不懂事物已发展变化而仍静止地看问题。"),
    ("叶公好龙", "比喻表面上爱好某事物，实际上并不真正爱好。"),
    ("亡羊补牢", "比喻出了问题以后想办法补救，防止继续受损失。"),
    ("对牛弹琴", "比喻对不懂道理的人讲道理，白费口舌。"),
    ("杯弓蛇影", "比喻因疑神疑鬼而引起恐惧。"),
    ("塞翁失马", "比喻坏事在一定条件下可以变为好事。"),
    ("愚公移山", "比喻坚持不懈地改造自然和坚定不移地进行斗争。"),
    ("纸上谈兵", "比喻空谈理论，不能解决实际问题。"),
    ("完璧归赵", "比喻把原物完好地归还本人。"),
]

def get_daily_idiom():
    """获取每日成语"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("idiom" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(DAILY_IDIOMS)
    name, meaning = DAILY_IDIOMS[idx]
    return f"📖 每日成语: 【{name}】\n   {meaning}"

# ================= 今天吃什么 =================

FOOD_SUGGESTIONS = [
    ("🍜 麻辣烫", "想吃辣的时候来一碗"),
    ("🍣 寿司", "清淡健康的选择"),
    ("🍕 披萨", "偶尔放纵一下"),
    ("🥗 沙拉", "减肥日的好选择"),
    ("🍲 火锅", "和朋友聚餐首选"),
    ("🍛 咖喱饭", "简单又好吃"),
    ("🥟 饺子", "北方人的最爱"),
    ("🍝 意面", "换个西式口味"),
    ("🍱 便当", "自己带饭最健康"),
    ("🥘 煲仔饭", "冬天暖胃首选"),
    ("🌮 墨西哥卷饼", "来点异国风味"),
    ("🍔 汉堡", "快餐解馋"),
    ("🍜 拉面", "汤鲜味美"),
    ("🍛 盖浇饭", "经济实惠"),
    ("🥪 三明治", "快手午餐"),
]

def get_food_suggestion():
    """获取今天吃什么推荐"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("food" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(FOOD_SUGGESTIONS)
    food, note = FOOD_SUGGESTIONS[idx]
    return f"🍚 今天吃什么: {food}\n   {note}"

# ================= 早安问候 =================

MORNING_GREETINGS = [
    "每一个清晨都是一个新的开始，今天也要加油哦 ☀️",
    "早安！今天的你比昨天更优秀 🌟",
    "新的一天，新的希望，愿你一切顺利 🌈",
    "早起的鸟儿有虫吃，今天也要元气满满 🐦",
    "早安！记得吃早餐，照顾好自己 🥐",
    "今天也是美好的一天，微笑面对 😊",
    "早安！你的努力终将不被辜负 💪",
    "清晨的阳光正好，你也正好 🌅",
    "新的一天，愿你被世界温柔以待 🌸",
    "早安！今天要比昨天更快乐 🎉",
    "起床啦！今天的任务：开心 😄",
    "早安！生命不息，奋斗不止 🔥",
    "每一个早晨都是一份礼物，拆开看看 🎁",
    "早安！愿你眼中有光，心中有爱 ✨",
    "今天也要做一个温暖的人哦 🌻",
]

def get_morning_greeting():
    """获取早安问候"""
    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("morning" + today).encode()).hexdigest()[:8], 16)
    idx = seed % len(MORNING_GREETINGS)
    return f"🌅 早安: {MORNING_GREETINGS[idx]}"

# ================= 自定义倒数日 =================

COUNTDOWN_EVENTS = []

def _load_countdown_events():
    """从环境变量加载倒数日事件，格式: 纪念日:2026-01-01,生日:03-15"""
    global COUNTDOWN_EVENTS
    raw = os.environ.get("COUNTDOWN_EVENTS", "结婚纪念日:11-18")
    if not raw:
        return
    for item in raw.split(","):
        item = item.strip()
        if ":" in item:
            name, date_str = item.split(":", 1)
            name = name.strip()
            date_str = date_str.strip()
            try:
                if len(date_str) == 5:  # MM-DD 格式（每年重复）
                    month, day = date_str.split("-")
                    event_date = date(int(now_bjt().year), int(month), int(day))
                    if event_date < now_bjt().date():
                        event_date = date(int(now_bjt().year) + 1, int(month), int(day))
                else:  # YYYY-MM-DD 格式
                    event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                COUNTDOWN_EVENTS.append((name, event_date, len(date_str) == 5))
            except:
                pass

def get_countdown():
    """获取自定义倒数日（支持每年重复）"""
    if not COUNTDOWN_EVENTS:
        _load_countdown_events()
    if not COUNTDOWN_EVENTS:
        return ""

    today = now_bjt().date()
    lines = []
    for name, event_date, yearly in COUNTDOWN_EVENTS:
        diff = (event_date - today).days

        # 如果是每年重复的事件且已过，计算下一个
        if yearly and diff < 0:
            # 计算到下一年的同一天还有多少天
            next_year = event_date.replace(year=today.year + 1)
            diff = (next_year - today).days

        # 计算已过天数（用于显示周年）
        if yearly:
            original = event_date.replace(year=2025)  # 假设起始年
            years_passed = today.year - original.year
            if today.month < original.month or (today.month == original.month and today.day < original.day):
                years_passed -= 1
        else:
            years_passed = 0

        if diff == 0:
            if years_passed > 0:
                lines.append(f"🎉 今天是【{name}】{years_passed}周年！")
            else:
                lines.append(f"🎉 今天是【{name}】！")
        elif diff == 1:
            lines.append(f"📅 明天就是【{name}】啦！")
        elif diff <= 7:
            lines.append(f"📅 距【{name}】还有 {diff} 天，快到了！")
        elif diff <= 30:
            lines.append(f"📅 距【{name}】还有 {diff} 天")
        else:
            months = diff // 30
            days = diff % 30
            if months > 0:
                lines.append(f"📅 距【{name}】还有 {months}个月{days}天")
            else:
                lines.append(f"📅 距【{name}】还有 {diff} 天")

    if lines:
        return "🗓 倒数日:\n  " + "\n  ".join(lines)
    return ""

# ================= 生活指数 =================

def get_life_index(weather_text):
    """根据天气生成生活指数（本地计算）"""
    if not weather_text:
        return ""

    match = re.search(r'([+-]?\d+)\s*°?[CcFf]', weather_text)
    if not match:
        return ""
    temp = int(match.group(1))
    if '°F' in weather_text or '°f' in weather_text:
        temp = (temp - 32) * 5 // 9

    today = now_bjt().strftime('%Y-%m-%d')
    seed = int(hashlib.md5(("index" + today).encode()).hexdigest()[:8], 16)

    # 紫外线指数
    if temp >= 30:
        uv = "很强 ☀️ 注意防晒"
    elif temp >= 25:
        uv = "较强 🌤 涂防晒霜"
    elif temp >= 20:
        uv = "中等 ⛅ 适当防护"
    else:
        uv = "较弱 ☁️ 无需特别防护"

    # 运动指数
    if temp >= 35 or temp <= 0:
        sport = "不宜 🚫 避免户外运动"
    elif temp >= 28:
        sport = "较不宜 🌡 选择室内运动"
    elif temp >= 15:
        sport = "适宜 ✅ 户外运动好时机"
    else:
        sport = "较适宜 🧥 注意保暖"

    # 洗车指数
    weather_lower = weather_text.lower()
    if any(k in weather_lower for k in ['rain', '雨', 'snow', '雪', 'shower']):
        wash = "不宜 🚫 明天再洗"
    elif any(k in weather_lower for k in ['cloud', '阴', 'overcast']):
        wash = "较不宜 ☁️ 建议等等"
    else:
        wash = "适宜 ✅ 适合洗车"

    # 穿衣指数
    if temp >= 33:
        dress = "短袖短裤 👕"
    elif temp >= 26:
        dress = "薄衬衫/T恤 👔"
    elif temp >= 20:
        dress = "薄外套+T恤 🧥"
    elif temp >= 15:
        dress = "外套+长袖 🧥"
    elif temp >= 10:
        dress = "厚外套+毛衣 🧣"
    elif temp >= 0:
        dress = "棉衣+保暖内衣 🧤"
    else:
        dress = "羽绒服+围巾 🧣"

    # 舒适度
    if 18 <= temp <= 26:
        comfort = "舒适 😊"
    elif 10 <= temp <= 32:
        comfort = "较舒适 🙂"
    else:
        comfort = "不舒适 😣"

    lines = [
        f"☀️ 紫外线: {uv}",
        f"🏃 运动: {sport}",
        f"🚗 洗车: {wash}",
        f"👔 穿衣: {dress}",
        f"😌 舒适度: {comfort}",
    ]
    return "📊 生活指数:\n  " + "\n  ".join(lines)

# ================= 天气穿衣建议 =================

def get_clothing_advice(weather_text):
    """根据天气文本提供建议"""
    if not weather_text:
        return ""
    # 提取温度
    match = re.search(r'([+-]?\d+)\s*°?[CcFf]', weather_text)
    if not match:
        return ""
    temp_str = match.group(1)
    try:
        temp = int(temp_str)
    except:
        return ""

    # 如果是华氏度，转换为摄氏度（备用逻辑）
    if '°F' in weather_text or '°f' in weather_text:
        temp = (temp - 32) * 5 // 9

    if temp >= 35:
        return "🔥 高温预警！注意防暑降温，多喝水"
    elif temp >= 28:
        return "👕 适合穿短袖短裤，注意防晒"
    elif temp >= 20:
        return "👔 早晚温差大，建议带件薄外套"
    elif temp >= 10:
        return "🧥 天气转凉，记得穿外套"
    elif temp >= 0:
        return "🧣 注意保暖，围巾手套安排上"
    else:
        return "🧤 严寒天气，羽绒服必备，注意防滑"

# ================= 假期倒计时 =================

# 2026年中国法定节假日（按时间顺序）
HOLIDAYS_2026 = [
    ("元旦", date(2026, 1, 1)),
    ("春节", date(2026, 2, 17)),
    ("清明", date(2026, 4, 5)),
    ("劳动节", date(2026, 5, 1)),
    ("端午", date(2026, 6, 19)),
    ("中秋", date(2026, 9, 27)),
    ("国庆", date(2026, 10, 1)),
    # 2027
    ("元旦", date(2027, 1, 1)),
    ("春节", date(2027, 2, 6)),
]

def get_holiday_countdown():
    """获取最近的假期倒计时"""
    today = now_bjt().date()
    for name, h_date in HOLIDAYS_2026:
        diff = (h_date - today).days
        if diff > 0:
            if diff == 1:
                return f"🏖 明天就是{name}啦！🎉"
            elif diff <= 3:
                return f"🏖 距{name}还有 {diff} 天，马上到了！"
            elif diff <= 7:
                return f"🏖 距{name}还有 {diff} 天，倒计时中~"
            else:
                return f"🏖 距{name}还有 {diff} 天"
        elif diff == 0:
            return f"🏖 今天是{name}！节日快乐！🎉"
    return ""

# ================= 日出日落 =================

def get_sun_info():
    """获取日出日落时间（使用免费 API）"""
    try:
        resp = requests.get(f"https://api.sunrise-sunset.org/json?formatted=0&date=today", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'OK':
                results = data['results']
                # 转换为北京时间 (UTC+8)
                sunrise_utc = datetime.fromisoformat(results['sunrise'].replace('Z', '+00:00'))
                sunset_utc = datetime.fromisoformat(results['sunset'].replace('Z', '+00:00'))
                sunrise_bjt = sunrise_utc.astimezone(BJT).strftime('%H:%M')
                sunset_bjt = sunset_utc.astimezone(BJT).strftime('%H:%M')
                # 计算日照时长
                day_length = int(results.get('day_length', 0))
                hours = day_length // 3600
                minutes = (day_length % 3600) // 60
                return f"🌅 日出 {sunrise_bjt} | 🌇 日落 {sunset_bjt} | ☀️ 日照 {hours}h{minutes}m"
    except Exception as e:
        log(f"⚠️ 日出日落 API 请求失败: {e}")
    return ""

# ================= 积分预测 =================

def get_points_prediction(data, email, points, plans_list):
    """根据积分增速预测达成目标的日期"""
    history = data.get("points_history", {}).get(email, [])
    if len(history) < 2 or not plans_list:
        return None

    recent = history[-7:]
    if len(recent) < 2:
        return None
    total_change = recent[-1]["points"] - recent[0]["points"]
    days_span = len(recent) - 1
    daily_rate = total_change / days_span if days_span > 0 else 0

    if daily_rate <= 0:
        return None

    pts = int(points)
    predictions = []
    for p in plans_list:
        if not p['ready'] and p['diff'] > 0:
            days_needed = p['diff'] / daily_rate
            target_date = (now_bjt() + timedelta(days=days_needed)).strftime('%m月%d日')
            predictions.append(f"  📍 {p['need']}分→{p['days']}天: 预计 {target_date} 达成")

    if not predictions:
        return None
    return "🔮 积分预测 (基于日均+" + f"{daily_rate:.0f}分):\n" + "\n".join(predictions)

# ================= 签到成就系统 =================

ACHIEVEMENTS = [
    ("first_checkin", "🔰 初来乍到", "完成第一次签到"),
    ("streak_3", "⭐ 三日之约", "连续签到 3 天"),
    ("streak_7", "🔥 一周不断", "连续签到 7 天"),
    ("streak_30", "💎 月度达人", "连续签到 30 天"),
    ("streak_100", "👑 百日王者", "连续签到 100 天"),
    ("streak_365", "🏆 年度传说", "连续签到 365 天"),
    ("points_100", "💰 小有积蓄", "积分达到 100"),
    ("points_500", "💰 积分富翁", "积分达到 500"),
    ("points_1000", "💰 千分大佬", "积分达到 1000"),
    ("total_7", "📅 签到新手", "累计签到 7 天"),
    ("total_30", "📅 签到常客", "累计签到 30 天"),
    ("total_100", "📅 签到元老", "累计签到 100 天"),
    ("total_365", "📅 签到传说", "累计签到 365 天"),
]

def check_achievements(data, email, points, streak_count, checkin_ok):
    """检查并解锁新成就，返回新解锁的成就列表"""
    if email not in data.get("achievements", {}):
        if "achievements" not in data:
            data["achievements"] = {}
        data["achievements"][email] = []

    unlocked = set(data["achievements"][email])
    new_achievements = []

    # 累计签到天数
    total_days = len(data.get("checkin_dates", {}).get(email, []))

    checks = {
        "first_checkin": checkin_ok,
        "streak_3": streak_count >= 3,
        "streak_7": streak_count >= 7,
        "streak_30": streak_count >= 30,
        "streak_100": streak_count >= 100,
        "streak_365": streak_count >= 365,
        "points_100": points >= 100,
        "points_500": points >= 500,
        "points_1000": points >= 1000,
        "total_7": total_days >= 7,
        "total_30": total_days >= 30,
        "total_100": total_days >= 100,
        "total_365": total_days >= 365,
    }

    for ach_id, condition in checks.items():
        if condition and ach_id not in unlocked:
            unlocked.add(ach_id)
            for aid, icon_desc, desc in ACHIEVEMENTS:
                if aid == ach_id:
                    new_achievements.append(f"{icon_desc} — {desc}")
                    break

    data["achievements"][email] = list(unlocked)
    return new_achievements

def format_achievements(data, email):
    """格式化已解锁成就"""
    unlocked = data.get("achievements", {}).get(email, [])
    if not unlocked:
        return ""
    total = len(ACHIEVEMENTS)
    count = len(unlocked)
    icons = []
    for ach_id, icon_desc, desc in ACHIEVEMENTS:
        if ach_id in unlocked:
            icons.append(icon_desc.split(" ")[0])  # 只取 emoji
    progress = round(count / total * 100)
    return f"🏅 成就: {count}/{total} ({progress}%) {''.join(icons)}"

def format_new_achievements(new_list):
    """格式化新解锁成就通知"""
    if not new_list:
        return ""
    lines = ["", "🎊 🎊 🎊 新成就解锁！🎊 🎊 🎊"]
    for ach in new_list:
        lines.append(f"  ✨ {ach}")
    return "\n".join(lines)

# ================= 周报/月报 =================

def is_weekly_report_day():
    """判断今天是否是周报日（周日）"""
    return now_bjt().weekday() == 6  # 周日

def is_monthly_report_day():
    """判断今天是否是月报日（月末最后一天）"""
    today = now_bjt().date()
    tomorrow = today + timedelta(days=1)
    return tomorrow.month != today.month

def format_weekly_report(data, email, points):
    """生成周报"""
    dates_list = data.get("checkin_dates", {}).get(email, [])
    today = now_bjt().date()
    week_start = today - timedelta(days=today.weekday())  # 本周一
    week_prefix = [str(week_start + timedelta(days=i)) for i in range(7)]
    week_checked = sum(1 for d in dates_list if d in week_prefix)

    history = data.get("points_history", {}).get(email, [])
    week_points_change = 0
    if len(history) >= 2:
        week_ago = today - timedelta(days=7)
        pts_before = None
        pts_now = None
        for r in history:
            d = datetime.strptime(r["date"], '%Y-%m-%d').date()
            if d <= week_ago:
                pts_before = r["points"]
            pts_now = r["points"]
        if pts_before and pts_now:
            week_points_change = pts_now - pts_before

    lines = [
        "",
        "━━━━━━ 📊 本周签到周报 ━━━━━━",
        "",
        f"📅 本周签到: {week_checked}/7 天",
        f"💰 本周积分: {'+' if week_points_change >= 0 else ''}{week_points_change}",
    ]

    streak = data.get("checkin_streak", {}).get(email, {})
    if streak.get("count", 0) >= 7:
        lines.append(f"🔥 连续签到: {streak['count']} 天，保持住！")
    elif week_checked == 7:
        lines.append("🌟 本周全勤！完美签到！")

    return "\n".join(lines)

def format_monthly_report(data, email, points):
    """生成月报"""
    dates_list = data.get("checkin_dates", {}).get(email, [])
    today = now_bjt().date()
    month_start = today.replace(day=1)
    month_prefix = today.strftime('%Y-%m')
    month_dates = [d for d in dates_list if d.startswith(month_prefix)]
    month_days = (today - month_start).days + 1
    checked = len(month_dates)
    rate = checked * 100 // month_days if month_days > 0 else 0

    history = data.get("points_history", {}).get(email, [])
    month_points_change = 0
    if len(history) >= 2:
        pts_start = None
        pts_end = None
        for r in history:
            if r["date"].startswith(month_prefix):
                if pts_start is None:
                    pts_start = r["points"]
                pts_end = r["points"]
        if pts_start and pts_end:
            month_points_change = pts_end - pts_start

    lines = [
        "",
        "━━━━━━ 📊 本月签到月报 ━━━━━━",
        "",
        f"📅 本月签到: {checked}/{month_days} 天 ({rate}%)",
        f"💰 本月积分: {'+' if month_points_change >= 0 else ''}{month_points_change}",
    ]

    if rate >= 90:
        lines.append("🌟 本月签到率优秀！继续保持！")
    elif rate >= 70:
        lines.append("👍 本月签到率不错，加油！")
    else:
        lines.append("💪 本月签到率有待提升，加油！")

    return "\n".join(lines)

# ================= 积分换算人民币 =================

def calc_rmb_value(points):
    """将积分换算为人民币价值（基于 GLaDOS 定价）"""
    # GLaDOS 官方定价参考：年费约 $30 USD ≈ 216 RMB
    # 500分 = 100天 → 约 59 RMB (100天年费比例)
    # 所以 1分 ≈ 0.118 RMB
    if not isinstance(points, int) or points <= 0:
        return ""
    rmb = points * 0.118
    return f"💵 折合人民币: 约 ¥{rmb:.1f}"

# ================= 签到日志导出 =================

EXPORT_FILE = Path(__file__).parent / "glados_checkin_log.csv"

def export_checkin_log(data, email):
    """导出签到日志为 CSV"""
    dates_list = data.get("checkin_dates", {}).get(email, [])
    history = data.get("points_history", {}).get(email, [])
    if not dates_list:
        return ""

    # 合并数据
    points_map = {r["date"]: r["points"] for r in history}
    rows = []
    for d in sorted(dates_list):
        rows.append({
            "日期": d,
            "签到": "✅",
            "积分": points_map.get(d, ""),
        })

    try:
        with open(EXPORT_FILE, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=["日期", "签到", "积分"])
            writer.writeheader()
            writer.writerows(rows)
        return f"📋 日志已导出: {EXPORT_FILE.name} ({len(rows)} 条记录)"
    except Exception as e:
        log(f"⚠️ 导出日志失败: {e}")
        return ""

# ================= 签到周年纪念 =================

def get_anniversary(data, email):
    """检查签到周年纪念"""
    dates_list = data.get("checkin_dates", {}).get(email, [])
    if not dates_list:
        return ""
    first_date = min(dates_list)
    first = datetime.strptime(first_date, '%Y-%m-%d').date()
    today = now_bjt().date()
    total_days = (today - first).days

    # 里程碑
    milestones = [100, 200, 365, 500, 730, 1000]
    for m in milestones:
        if total_days == m:
            if m >= 365:
                years = m // 365
                return f"🎂 恭喜！今天是您签到第 {m} 天！已坚持 {years} 年，非凡毅力！"
            else:
                return f"🎂 里程碑！今天是您签到第 {m} 天！继续加油！"

    # 周年
    if today.month == first.month and today.day == first.day and total_days >= 365:
        years = total_days // 365
        return f"🎂 签到 {years} 周年纪念日！感谢一路坚持！"

    return ""

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

def validate_cookie(raw: str, index: int = 1) -> list:
    """检测 Cookie 格式是否异常，返回警告列表"""
    warnings = []
    if not raw:
        return [f"账号 {index}: Cookie 为空"]

    raw = raw.strip()

    # 1. 检查是否包含多余换行
    if '\n' in raw.replace('\\n', ''):
        warnings.append(f"账号 {index}: Cookie 包含换行符，可能导致解析失败")
        warnings.append(f"  👉 修复: 删除 Cookie 中的换行，确保是单行文本")

    # 2. 检查首尾引号
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        warnings.append(f"账号 {index}: Cookie 首尾有多余引号")
        warnings.append(f"  👉 修复: 去掉首尾的 \" 或 ' 引号")

    # 3. 检查是否包含必要字段
    has_sess = 'koa:sess=' in raw or 'koa.sess=' in raw
    has_sig = 'koa:sess.sig=' in raw

    if not has_sess:
        # 可能是纯 JWT Token 或其他格式，不算错误
        if raw.count('.') == 2 and len(raw) > 50:
            pass  # JWT Token 格式，extract_cookie 会处理
        elif raw.startswith('{'):
            pass  # JSON 格式
        else:
            warnings.append(f"账号 {index}: 缺少 koa:sess 字段，格式可能不正确")
            warnings.append(f"  👉 正确格式: koa:sess=长字符串; koa:sess.sig=短字符串")

    # 4. 检查分号和空格
    if has_sess and ';' in raw:
        parts = raw.split(';')
        for part in parts:
            if part and not part.strip():
                warnings.append(f"账号 {index}: Cookie 包含空的分段（多余分号）")
                warnings.append(f"  👉 修复: 删除多余的分号和空格")
                break

    # 5. 检查是否缺少分号分隔
    if has_sess and not has_sig and 'koa:sess.sig' not in raw:
        warnings.append(f"账号 {index}: 缺少 koa:sess.sig 字段")
        warnings.append(f"  👉 确保同时复制 koa:sess 和 koa:sess.sig 两个 Cookie")

    # 6. 检查长度异常
    if len(raw) < 20:
        warnings.append(f"账号 {index}: Cookie 长度过短 ({len(raw)} 字符)，可能不完整")
    elif len(raw) > 2000:
        warnings.append(f"账号 {index}: Cookie 长度异常 ({len(raw)} 字符)，可能复制了多余内容")

    # 7. 检查 URL 编码问题
    if '%3D' in raw or '%3B' in raw:
        warnings.append(f"账号 {index}: Cookie 包含 URL 编码字符，可能需要解码")
        warnings.append(f"  👉 修复: 使用 Cookie-Editor 扩展直接复制原始值")

    # 8. 检查空格问题（非分隔符位置的空格）
    if '  ' in raw:  # 连续空格
        warnings.append(f"账号 {index}: Cookie 包含连续空格，可能有复制错误")

    return warnings

def get_cookies():
    raw = os.environ.get("GLADOS_COOKIE", "")
    if not raw:
        log("❌ 未配置 GLADOS_COOKIE")
        return []

    # 启动时执行 Cookie 格式检测
    sep = '\n' if '\n' in raw else '&'
    parts = [c for c in raw.split(sep) if c.strip()]

    all_warnings = []
    for i, part in enumerate(parts, 1):
        warnings = validate_cookie(part, i)
        all_warnings.extend(warnings)

    if all_warnings:
        log("🔒 Cookie 格式检测:")
        for w in all_warnings:
            log(f"   {w}")
        # 如果有严重问题（为空、缺字段），发送告警
        severe = [w for w in all_warnings if '为空' in w or '缺少 koa:sess' in w or '长度过短' in w]
        if severe:
            send_alert("🔒 Cookie 格式异常", "\n".join(all_warnings))
    else:
        log("🔒 Cookie 格式检测: ✅ 全部正常")

    return [extract_cookie(c) for c in parts]

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
        self.checkin_result = None  # 签到原始响应
        self.earned_points = None  # 本次签到获得积分
        self.points_history_detail = []  # 积分变化明细
        
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

            # 积分变化历史（存储用于展示明细）
            self.points_history_detail = res.get('history', [])

            # 最近一次积分变化
            history = self.points_history_detail
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
        res = self.req('POST', '/api/user/checkin', {'token': 'glados.cloud'})
        self.checkin_result = res
        # 尝试从响应中提取本次获得积分
        if res:
            for key in ['points', 'earned', 'new_points', 'add_points']:
                if key in res:
                    try:
                        self.earned_points = int(float(str(res[key])))
                    except:
                        pass
                    break
        return res

# ================= 主程序 =================

# Apple 风格 HTML 模板（PushPlus 使用）
APPLE_HTML_TEMPLATE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Display','SF Pro Text','Helvetica Neue','PingFang SC',Arial,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:16px;color:#1d1d1f;line-height:1.6;-webkit-font-smoothing:antialiased}}
.container{{max-width:480px;margin:0 auto}}
.header{{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);border-radius:20px;padding:24px;margin-bottom:16px;color:#fff;text-align:center;position:relative;overflow:hidden}}
.header::before{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(circle,rgba(255,255,255,.08) 0%,transparent 60%);animation:pulse 4s ease-in-out infinite}}
.header .emoji{{font-size:36px;margin-bottom:8px}}
.header .title{{font-size:20px;font-weight:700;letter-spacing:-.5px;margin-bottom:4px}}
.header .subtitle{{font-size:13px;color:rgba(255,255,255,.7)}}
@keyframes pulse{{0%,100%{{opacity:.5}}50%{{opacity:1}}}}
.card{{background:#fff;border-radius:16px;padding:18px;margin-bottom:12px;box-shadow:0 2px 12px rgba(0,0,0,.08);border:1px solid rgba(0,0,0,.04)}}
.card-header{{display:flex;align-items:center;gap:10px;margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #f0f0f0}}
.card-header .icon{{font-size:22px;width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:#f5f5f7;border-radius:10px}}
.card-header .title{{font-size:15px;font-weight:600;color:#1d1d1f;letter-spacing:-.2px}}
.card-header .subtitle{{font-size:12px;color:#86868b;margin-top:1px}}
.row{{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #f8f8f8}}
.row:last-child{{border-bottom:none}}
.row .label{{font-size:14px;color:#636366;display:flex;align-items:center;gap:6px}}
.row .value{{font-size:14px;font-weight:600;color:#1d1d1f;text-align:right}}
.row .value.green{{color:#34c759}}
.row .value.red{{color:#ff3b30}}
.row .value.orange{{color:#ff9500}}
.row .value.blue{{color:#007aff}}
.progress-bar{{height:8px;background:#f0f0f0;border-radius:4px;overflow:hidden;margin:6px 0}}
.progress-fill{{height:100%;border-radius:4px;transition:width .6s ease}}
.progress-fill.green{{background:linear-gradient(90deg,#34c759,#30d158)}}
.progress-fill.blue{{background:linear-gradient(90deg,#007aff,#5ac8fa)}}
.progress-fill.orange{{background:linear-gradient(90deg,#ff9500,#ffcc00)}}
.progress-fill.red{{background:linear-gradient(90deg,#ff3b30,#ff6961)}}
.badge{{display:inline-block;padding:3px 10px;border-radius:8px;font-size:12px;font-weight:500}}
.badge.green{{background:#e8f9ee;color:#34c759}}
.badge.red{{background:#fef0f0;color:#ff3b30}}
.badge.orange{{background:#fff5e6;color:#ff9500}}
.badge.blue{{background:#e8f2ff;color:#007aff}}
.badge.gray{{background:#f5f5f7;color:#636366}}
.badge.purple{{background:#f3e8ff;color:#9b59b6}}
.text-sm{{font-size:13px;color:#86868b}}
.text-xs{{font-size:11px;color:#aeaeb2}}
.mt-8{{margin-top:8px}}
.mt-12{{margin-top:12px}}
.mb-8{{margin-bottom:8px}}
.mb-12{{margin-bottom:12px}}
.footer{{text-align:center;padding:16px 0;margin-top:8px}}
.footer .brand{{font-size:14px;font-weight:600;color:#fff;opacity:.9}}
.footer .text-sm{{font-size:11px;color:rgba(255,255,255,.6);margin-top:4px}}
.divider{{height:1px;background:#f0f0f0;margin:12px 0}}
.alert{{padding:12px 16px;border-radius:12px;margin:8px 0;font-size:13px;line-height:1.5}}
.alert.warning{{background:linear-gradient(135deg,#fff8e1,#fff3cd);color:#c97b00;border:1px solid #ffe0b2}}
.alert.danger{{background:linear-gradient(135deg,#fef0f0,#fde8e8);color:#d70015;border:1px solid #ffcdd2}}
.alert.info{{background:linear-gradient(135deg,#e8f4fd,#dbeafe);color:#007aff;border:1px solid #bbdefb}}
.alert.success{{background:linear-gradient(135deg,#e8f9ee,#d4edda);color:#248a3d;border:1px solid #c8e6c9}}
.alert.fortune{{background:linear-gradient(135deg,#fff9e6,#fff3cd);color:#b8860b;border:1px solid #ffe082;text-align:center;font-size:14px;padding:14px}}
.quote{{border-left:3px solid #007aff;padding:10px 14px;margin:8px 0;background:linear-gradient(90deg,#f5f7fa,#fff);border-radius:0 12px 12px 0;font-size:13px;color:#515154;font-style:italic}}
.chip{{display:inline-block;padding:5px 12px;border-radius:20px;font-size:12px;margin:2px;background:#f5f5f7;color:#515154;font-weight:500}}
.chip.gold{{background:linear-gradient(135deg,#fff6e0,#ffe8b0);color:#b8860b}}
.chip.blue{{background:#e8f2ff;color:#007aff}}
.heatmap{{font-size:15px;line-height:2;letter-spacing:3px}}
.stat-grid{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.stat-item{{text-align:center;padding:14px 8px;background:linear-gradient(135deg,#f5f7fa,#eef1f5);border-radius:14px}}
.stat-item .num{{font-size:24px;font-weight:700;color:#1d1d1f}}
.stat-item .desc{{font-size:11px;color:#86868b;margin-top:4px;font-weight:500}}
.achievement{{display:inline-block;margin:3px;padding:5px 10px;background:linear-gradient(135deg,#fffbe6,#fff6cc);border-radius:10px;font-size:12px;border:1px solid #ffe58f}}
.fun-card{{background:linear-gradient(135deg,#fafbff,#f5f0ff);border-radius:16px;padding:16px;margin-bottom:12px;border:1px solid #e8e0f0}}
.fun-card .fun-title{{font-size:14px;font-weight:600;color:#6b5b95;margin-bottom:8px}}
.fun-card .fun-text{{font-size:13px;color:#515154;line-height:1.6}}
.mini-chart{{display:flex;align-items:flex-end;gap:3px;height:40px;padding:4px 0}}
.mini-chart .bar{{flex:1;border-radius:3px 3px 0 0;transition:height .3s;min-width:8px}}
.mini-chart .bar.up{{background:linear-gradient(180deg,#34c759,#30d158)}}
.mini-chart .bar.down{{background:linear-gradient(180deg,#ff3b30,#ff6961)}}
.mini-chart .bar.neutral{{background:linear-gradient(180deg,#8e8e93,#aeaeb2)}}
.timeline{{padding-left:16px;border-left:2px solid #e0e0e0}}
.timeline-item{{padding:6px 0 6px 16px;position:relative;font-size:13px;color:#515154}}
.timeline-item::before{{content:'';position:absolute;left:-21px;top:12px;width:10px;height:10px;border-radius:50%;background:#007aff;border:2px solid #fff}}
.timeline-item:first-child::before{{background:#34c759}}
</style></head><body>
<div class="container">
<div class="header">
<div class="emoji">🎮</div>
<div class="title">GLaDOS Daily Report</div>
<div class="subtitle">{time}</div>
</div>
{content}
<div class="footer">
<div class="brand">GLaDOS Auto Checkin</div>
<div class="text-sm">Powered by GitHub Actions · Made with ❤️</div>
</div>
</div>
</body></html>"""

def _text_to_apple_html(content):
    """将纯文本推送内容转换为 Apple 风格 HTML"""
    lines = content.split('\n')
    html_parts = []
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 分隔线 → section header
        m = re.match(r'━━━━━━ (.+?) ━━━━━━', line)
        if m:
            if current_section:
                html_parts.append('</div>')
            section_name = m.group(1).strip()
            icon = section_name.split(' ')[0] if ' ' in section_name else '📊'
            title = ' '.join(section_name.split(' ')[1:]) if ' ' in section_name else section_name
            html_parts.append(f'<div class="card"><div class="card-header"><span class="icon">{icon}</span><div><div class="title">{title}</div></div></div>')
            current_section = section_name
            continue

        # 进度条行
        progress_match = re.match(r'([█▓]+[░█▓]*\s*\d+%?)\s*(.*)', line)
        if progress_match:
            bar_text = progress_match.group(1)
            label = progress_match.group(2)
            pct_match = re.search(r'(\d+)%', bar_text)
            pct = pct_match.group(1) if pct_match else '50'
            pct_int = int(pct)
            color = 'green' if pct_int >= 80 else 'blue' if pct_int >= 50 else 'orange'
            html_parts.append(f'<div class="mb-8">')
            if label:
                html_parts.append(f'<div class="text-sm" style="margin-bottom:4px">{label}</div>')
            html_parts.append(f'<div class="progress-bar"><div class="progress-fill {color}" style="width:{pct}%"></div></div>')
            html_parts.append(f'<div class="text-xs" style="text-align:right;margin-top:2px">{pct}%</div></div>')
            continue

        # 键值对行（emoji + label: value）
        kv_match = re.match(r'^(\S{1,2})\s*(.+?):\s*(.+)$', line)
        if kv_match:
            icon = kv_match.group(1)
            label = kv_match.group(2).strip()
            value = kv_match.group(3).strip()
            value_class = ''
            if any(k in value for k in ['✅', '可兑换', '储备充足', '达成']):
                value_class = 'green'
            elif any(k in value for k in ['❌', '紧急', '过期']):
                value_class = 'red'
            elif any(k in value for k in ['⚠️', '即将到期']):
                value_class = 'orange'
            elif any(k in value for k in ['+']):
                value_class = 'green'
            html_parts.append(f'<div class="row"><span class="label">{icon} {label}</span><span class="value {value_class}">{value}</span></div>')
            continue

        # 运势/情话/彩虹屁/段子等趣味内容
        if any(k in line for k in ['💕', '🌈', '😂', '🧩', '📖', '🍚', '🌅']):
            html_parts.append(f'<div class="fun-card"><div class="fun-text">{line}</div></div>')
            continue

        # 星座运势标题
        if '♈' in line and '运势' in line:
            html_parts.append(f'<div class="fun-card"><div class="fun-title">{line}</div>')
            continue
        # 星座运势子项
        if re.match(r'^\s+(💕|💼|💰|💪|🍀)', line):
            html_parts.append(f'<div class="fun-text" style="margin:4px 0">{line}</div>')
            continue

        # 成就/等级/庆祝
        if any(k in line for k in ['🎊', '✨', '🏆', '🎉', '新成就']):
            html_parts.append(f'<div class="alert success">{line}</div>')
            continue
        if any(k in line for k in ['🚨', '⚠️']) and '到期' in line:
            html_parts.append(f'<div class="alert danger">{line}</div>')
            continue
        if '等级' in line or '成就' in line:
            html_parts.append(f'<div class="mt-8"><span class="chip gold">{line}</span></div>')
            continue
        if '💡' in line or '🏖' in line:
            html_parts.append(f'<div class="alert info">{line}</div>')
            continue

        # 倒数日
        if '📅' in line and '距' in line and '还有' in line:
            html_parts.append(f'<div class="alert info">{line}</div>')
            continue
        if '🎉' in line and '今天是' in line:
            html_parts.append(f'<div class="alert success">{line}</div>')
            continue

        # 普通行
        html_parts.append(f'<div class="mt-8">{line}</div>')

    if current_section:
        html_parts.append('</div>')

    return '\n'.join(html_parts)

def _text_to_telegram_html(content):
    """将纯文本转换为 Telegram HTML 格式（Apple 风格）"""
    lines = content.split('\n')
    html_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            html_parts.append('')
            continue

        # 分隔线 → 斜体标题
        m = re.match(r'━━━━━━ (.+?) ━━━━━━', line)
        if m:
            section = m.group(1).strip()
            html_parts.append(f'\n<b>══ {section} ══</b>')
            continue

        # 进度条 → code 块
        if re.match(r'[█░▓]+', line):
            html_parts.append(f'<code>{line}</code>')
            continue

        # 键值对行 → 加粗标签
        kv_match = re.match(r'^(\S{1,2})\s*(.+?):\s*(.+)$', line)
        if kv_match:
            icon = kv_match.group(1)
            label = kv_match.group(2).strip()
            value = kv_match.group(3).strip()
            html_parts.append(f'{icon} <b>{label}:</b>  <i>{value}</i>')
            continue

        # 运势/情话/彩虹屁/段子
        if any(k in line for k in ['💕', '🌈', '😂', '🧩', '📖', '🍚', '🌅']):
            html_parts.append(f'<blockquote>{line}</blockquote>')
            continue

        # 星座运势子项
        if re.match(r'^\s+(💕|💼|💰|💪|🍀)', line):
            html_parts.append(f'  <i>{line.strip()}</i>')
            continue

        # 成就/庆祝行
        if any(k in line for k in ['🎊', '✨', '🏆', '🎉']):
            html_parts.append(f'<b>{line}</b>')
            continue

        # 告警行
        if any(k in line for k in ['🚨', '⚠️']):
            html_parts.append(f'<b>❗ {line}</b>')
            continue

        # 倒数日
        if '📅' in line and '距' in line:
            html_parts.append(f'<i>{line}</i>')
            continue

        # 等级/成就
        if '等级' in line or '成就' in line:
            html_parts.append(f'<b>{line}</b>')
            continue

        # 普通行
        html_parts.append(line)

    return '\n'.join(html_parts)

def pushplus_push(token, title, content):
    """PushPlus 微信推送（Apple 风格 HTML）"""
    if not token: return False
    try:
        url = "https://www.pushplus.plus/send"
        # 转换为 Apple 风格 HTML
        body_html = _text_to_apple_html(content)
        current_time = now_bjt().strftime('%Y-%m-%d %H:%M')
        full_html = APPLE_HTML_TEMPLATE.format(content=body_html, time=current_time)
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
            else:
                log(f"❌ PushPlus 推送失败: {result.get('msg')}")
        else:
            log(f"❌ PushPlus 推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ PushPlus 推送失败: {e}")
    return False

def serverchan(send_key, title, content):
    """Server酱推送（Markdown 格式）"""
    if not send_key: return False
    try:
        url = f"https://sctapi.ftqq.com/{send_key}.send"
        md = content
        # 分隔线 → 粗体标题 + 分割线
        md = re.sub(r'━━━━━━ (.+?) ━━━━━━', r'**\1**\n---', md)
        # 键值对行 → 粗体标签
        md = re.sub(r'^(\S{1,2})\s*(.+?):\s*(.+)$', r'**\1 \2:** \3', md, flags=re.MULTILINE)
        # 进度条 → 代码块
        md = re.sub(r'^([█░▓]+.+)$', r'```\n\1\n```', md, flags=re.MULTILINE)
        # 趣味内容 → 引用
        md = re.sub(r'^([💕🌈😂🧩📖🍚🌅].+)$', r'> \1', md, flags=re.MULTILINE)
        resp = requests.post(url, data={'title': title, 'desp': md}, timeout=10)
        if resp.status_code == 200:
            log("✅ Server酱推送成功")
            return True
        else:
            log(f"❌ Server酱推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ Server酱推送失败: {e}")
    return False

def dingtalk(token, title, content):
    """钉钉机器人推送（简洁 Markdown）"""
    if not token: return False
    try:
        url = f"https://oapi.dingtalk.com/robot/send?access_token={token}"
        md = content
        # 分隔线 → 粗体标题
        md = re.sub(r'━━━━━━ (.+?) ━━━━━━', r'**\1**', md)
        # 键值对 → 粗体标签
        md = re.sub(r'^(\S{1,2})\s*(.+?):\s*(.+)$', r'**\1 \2:** \3', md, flags=re.MULTILINE)
        # 进度条特殊字符替换
        md = re.sub(r'[█░▓]+[^\n]*', lambda m: m.group(0).replace('█', '■').replace('░', '□').replace('▓', '▣'), md)
        # 趣味内容 → 引用
        md = re.sub(r'^([💕🌈😂🧩📖🍚🌅].+)$', r'> \1', md, flags=re.MULTILINE)
        msg = f"## {title}\n\n{md}"
        data = {"msgtype": "markdown", "markdown": {"title": title, "text": msg}}
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('errcode') == 0:
                log("✅ 钉钉推送成功")
                return True
            else:
                log(f"❌ 钉钉推送失败: {result.get('errmsg')}")
        else:
            log(f"❌ 钉钉推送失败: {resp.status_code}")
    except Exception as e:
        log(f"❌ 钉钉推送失败: {e}")
    return False

def telegram_push(token, chat_id, title, content):
    """Telegram 推送（Apple 风格 HTML）"""
    if not token or not chat_id: return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = _text_to_telegram_html(content)
        msg = f"<b>{title}</b>\n\n{text}"
        data = {"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}
        resp = requests.post(url, json=data, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            if result.get('ok'):
                log("✅ Telegram 推送成功")
                return True
            else:
                log(f"❌ Telegram 推送失败: {result.get('description')}")
                # 降级为纯文本重试
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

def bark_push(key, title, content):
    """Bark 推送（iOS 原生推送）"""
    if not key:
        log("⚠️ Bark: 未配置 BARK_KEY，跳过推送")
        return False

    log(f"📱 Bark 推送开始...")
    log(f"   Key: {key[:6]}...{key[-4:]}" if len(key) > 10 else f"   Key: {key}")

    # Bark API 地址
    api_host = "https://api.day.app"

    # 截取内容前 100 字符作为 body（Bark 有长度限制）
    body = content[:100] + "..." if len(content) > 100 else content

    try:
        url = f"{api_host}/{key}"
        data = {
            "title": title,
            "body": body,
            "group": "GLaDOS",
            "sound": "birdsong",
            "isArchive": 1  # 保存到历史记录
        }
        log(f"   请求地址: {api_host}")
        log(f"   标题: {title}")
        log(f"   内容: {body[:50]}...")

        resp = requests.post(url, json=data, timeout=15)
        log(f"   响应状态: HTTP {resp.status_code}")
        log(f"   响应内容: {resp.text[:200]}")

        if resp.status_code == 200:
            result = resp.json()
            if result.get('code') == 200:
                log("✅ Bark 推送成功!")
                return True
            else:
                log(f"❌ Bark 推送失败: {result.get('message', 'Unknown error')}")
                return False
        else:
            log(f"❌ Bark 推送失败: HTTP {resp.status_code}")
            return False
    except requests.exceptions.SSLError as e:
        log(f"❌ Bark 推送失败: SSL 连接错误 - {e}")
        log("   提示: 可能是网络环境限制，GitHub Actions 上应该可以正常工作")
        return False
    except requests.exceptions.ConnectionError as e:
        log(f"❌ Bark 推送失败: 连接错误 - {e}")
        log("   提示: 无法连接到 Bark API 服务器")
        return False
    except requests.exceptions.Timeout as e:
        log(f"❌ Bark 推送失败: 请求超时 - {e}")
        return False
    except Exception as e:
        log(f"❌ Bark 推送失败: {type(e).__name__}: {e}")
        return False

def send_alert(title, content):
    """发送过期/异常告警（仅推送到钉钉和Server酱）"""
    sc_key = os.environ.get("SEND_KEY")
    ding_token = os.environ.get("DINGTALK_TOKEN")
    if sc_key:
        serverchan(sc_key, title, content)
    if ding_token:
        dingtalk(ding_token, title, content)

def format_dingtalk_message(g, msg, checkin_ok, data, streak, weather_text=None):
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

    # 本次签到获得积分
    earned_text = ""
    if g.earned_points is not None and g.earned_points > 0:
        earned_text = f"🎁 本次获得: +{g.earned_points} 积分"

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

    # 签到价值 + 人民币换算
    try:
        pts = int(g.points)
    except:
        pts = 0
    value_text = calc_value(pts)
    rmb_text = calc_rmb_value(pts)

    # 历史最高积分
    max_pts = get_max_points(data, g.email)
    max_pts_text = f"🏅 历史最高: {max_pts} 积分" if max_pts else ""

    # 智能推荐
    recommendation = get_recommendation(data, g.email, pts, g.plans_list)

    # 积分预测
    prediction = get_points_prediction(data, g.email, pts, g.plans_list)

    # 会员续期预警
    renewal_alert = format_renewal_alert(days) if isinstance(days, int) else ""

    # 本月签到统计
    monthly_stats = format_monthly_stats(data, g.email)

    # 签到热力图
    heatmap = format_heatmap(data, g.email)

    # 积分变化明细
    history_detail = format_points_history_detail(g)

    # 每日签到运势
    fortune = get_daily_fortune()

    # 成就系统
    try:
        streak_count = streak.get("count", 0)
    except:
        streak_count = 0
    new_achievements = check_achievements(data, g.email, pts, streak_count, checkin_ok)
    achievements_text = format_achievements(data, g.email)
    new_achievements_text = format_new_achievements(new_achievements)

    # 签到等级系统
    level_text = get_level(data, g.email)

    # ASCII Art 庆祝
    celebration = get_ascii_celebration(checkin_ok, g.earned_points)

    # 农历日期
    lunar = get_lunar_info()

    # 每日英语名言
    quote_en = get_daily_quote_en()

    # 签到周年纪念
    anniversary = get_anniversary(data, g.email)

    # 假期倒计时
    holiday = get_holiday_countdown()

    # 天气穿衣建议
    clothing = get_clothing_advice(weather_text) if weather_text else ""

    # 健康提示
    health_tip = get_health_tip(weather_text)

    # 签到时间分布
    time_dist = format_time_distribution(data, g.email)

    # 签到率趋势
    rate_trend = format_checkin_rate_trend(data, g.email)

    # 月度目标
    monthly_goal = format_monthly_goal(data, g.email)

    # 签到小游戏
    mini_game = get_mini_game()

    # 签到日记
    mood_note = get_mood_note()

    # 新增内容
    sweet_nothing = get_sweet_nothing()
    rainbow_fart = get_rainbow_fart()
    horoscope = get_zodiac_horoscope()
    daily_joke = get_daily_joke()
    riddle = get_riddle()
    idiom = get_daily_idiom()
    food = get_food_suggestion()
    morning = get_morning_greeting()
    countdown = get_countdown()
    life_index = get_life_index(weather_text)

    # 世界问候语
    world_greeting = get_world_greeting()

    # 下次签到时间
    next_checkin = get_next_checkin()

    # 时间
    now = now_bjt().strftime('%H:%M:%S')

    # 组装消息
    lines = [
        f"{get_greeting()}，这是您的资产简报",
        "",
        f"👤 账号: {mask_email(g.email)}",
        "",
        f"{world_greeting}",
        f"{fortune}",
        f"{mini_game}",
    ]

    # 签到成功庆祝
    if celebration:
        lines.append("")
        lines.append(celebration)

    lines.append("")
    lines.append("━━━━━━ 📊 核心资产报告 ━━━━━━")
    lines.append("")
    lines.append(f"💰 当前积分: {g.points} ({g.points_change})")
    lines.append(f"⏳ 可用天数: {days} 天  {day_status}")
    lines.append(f"📅 到期日期: {expire_date}")

    # 本次签到积分
    if earned_text:
        lines.append(earned_text)

    lines.append(f"{checkin_icon} 签到结果: {msg}")
    lines.append(f"{streak_text}")
    lines.append(f"{value_text}")

    if rmb_text:
        lines.append(rmb_text)

    if max_pts_text:
        lines.append(max_pts_text)

    # 签到等级
    lines.append(f"{level_text}")

    # 成就展示
    if achievements_text:
        lines.append(achievements_text)

    # 新成就解锁通知
    if new_achievements_text:
        lines.append(new_achievements_text)

    # 签到时间分布
    if time_dist:
        lines.append(f"{time_dist}")

    # 签到周年纪念
    if anniversary:
        lines.append("")
        lines.append(anniversary)

    # 续期预警（高优先级，放在核心报告内）
    if renewal_alert:
        lines.append("")
        lines.append(renewal_alert)

    lines.append("")
    lines.append("━━━━━━ 🎁 资产增值路径 ━━━━━━")
    lines.append("")
    lines.append(progress_text)

    if recommendation:
        lines.append("")
        lines.append(recommendation)

    if prediction:
        lines.append("")
        lines.append(prediction)

    # 本月签到统计
    lines.append("")
    lines.append(f"{monthly_stats}")

    # 签到热力图
    lines.append("")
    lines.append(heatmap)

    # 签到率趋势
    if rate_trend:
        lines.append("")
        lines.append(rate_trend)

    # 月度目标
    lines.append("")
    lines.append(monthly_goal)

    # 积分变化明细
    if history_detail:
        lines.append("")
        lines.append(history_detail)

    lines.append("")
    lines.append(f"{trend}")

    # 生活资讯
    life_parts = []
    if lunar:
        life_parts.append(lunar)
    if holiday:
        life_parts.append(holiday)
    if clothing:
        life_parts.append(clothing)
    if health_tip:
        life_parts.append(health_tip)
    if life_index:
        life_parts.append(life_index)
    if countdown:
        life_parts.append(countdown)
    if mood_note:
        life_parts.append(mood_note)
    if life_parts:
        lines.append("")
        lines.append("━━━━━━ 🌈 生活提醒 ━━━━━━")
        lines.append("")
        lines.extend(life_parts)

    # 趣味内容
    fun_parts = []
    if horoscope:
        fun_parts.append(horoscope)
    fun_parts.append(sweet_nothing)
    fun_parts.append(rainbow_fart)
    fun_parts.append(daily_joke)
    fun_parts.append(riddle)
    fun_parts.append(idiom)
    fun_parts.append(food)
    if fun_parts:
        lines.append("")
        lines.append("━━━━━━ 🎭 今日彩蛋 ━━━━━━")
        lines.append("")
        lines.extend(fun_parts)

    lines.append("")
    lines.append(f"{next_checkin}")
    lines.append(f"🕒 更新于: {now}")

    # 周报/月报
    if is_weekly_report_day():
        lines.append("")
        lines.append(format_weekly_report(data, g.email, pts))
    if is_monthly_report_day():
        lines.append("")
        lines.append(format_monthly_report(data, g.email, pts))

    return "\n".join(lines)


def format_points_history_detail(g):
    """格式化积分变化明细（最近5条）"""
    history = getattr(g, 'points_history_detail', [])
    if not history:
        return ""

    lines = ["━━━━━━ 📝 积分变化明细 ━━━━━━"]
    for record in history[:5]:
        change = record.get('change', 0)
        reason = record.get('reason', record.get('type', ''))
        time_str = record.get('time', record.get('date', ''))

        # 格式化变化量
        try:
            change_val = int(float(str(change)))
            change_str = f"+{change_val}" if change_val > 0 else str(change_val)
        except:
            change_str = str(change)

        # 格式化时间
        if 'T' in str(time_str):
            try:
                dt = datetime.fromisoformat(str(time_str).replace('Z', '+00:00'))
                time_str = dt.strftime('%m-%d %H:%M')
            except:
                pass

        # 简化原因
        if not reason:
            reason = "签到"
        reason = str(reason)[:20]

        lines.append(f"  {change_str:>5} | {reason} | {time_str}")

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

    # 预获取天气（所有账号共用）
    weather_text = get_weather()

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

        if checkin_ok:
            success_cnt += 1
            record_checkin_date(data, g.email)  # 记录签到日期

        # 4. 记录数据（积分趋势 + 连续签到）
        try:
            pts = int(g.points)
        except:
            pts = 0
        record_points(data, g.email, pts)
        streak = update_streak(data, g.email, checkin_ok)

        # 5. 统一纯文本格式（传入天气用于穿衣建议）
        results.append(format_dingtalk_message(g, msg, checkin_ok, data, streak, weather_text))

        # 6. 多账号汇总数据
        accounts.append({
            'email': g.email,
            'points': g.points,
            'days': g.left_days,
            'ok': checkin_ok
        })

        # 7. 导出签到日志（CSV）
        export_checkin_log(data, g.email)

    # 保存历史数据（先清理再保存）
    cleanup_old_data(data, keep_days=10)
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
    pp_token = os.environ.get("PUSHPLUS_TOKEN")
    bark_key = os.environ.get("BARK_KEY")

    if (tg_token and tg_chat_id) or sc_key or ding_token or pp_token or bark_key:
        title = f"GLaDOS签到: 成功{success_cnt}/{len(cookies)}"

        # 拼接所有内容
        text_content = "\n\n".join(results)
        if summary:
            text_content += summary

        # 生活资讯尾部
        footer_parts = []
        morning = get_morning_greeting()
        if morning:
            footer_parts.append(morning)
        if weather_text:
            footer_parts.append(weather_text)
        quote = get_quote()
        if quote:
            footer_parts.append(quote)
        quote_en = get_daily_quote_en()
        if quote_en:
            footer_parts.append(quote_en)
        sun_info = get_sun_info()
        if sun_info:
            footer_parts.append(sun_info)
        news = get_daily_news()
        if news:
            footer_parts.append(news)
        crypto = get_crypto_forex()
        if crypto:
            footer_parts.append(crypto)
        movie = get_movie_recommendation()
        if movie:
            footer_parts.append(movie)
        history_today = get_today_in_history()
        if history_today:
            footer_parts.append(history_today)
        server_info = get_server_status()
        if server_info:
            footer_parts.append(server_info)
        if footer_parts:
            text_content += "\n\n━━━━━━ 🌤 生活资讯 ━━━━━━\n\n" + "\n".join(footer_parts)

        # 推送并记录状态
        push_status = []
        if pp_token:
            ok = pushplus_push(pp_token, title, text_content)
            push_status.append(("PushPlus", ok))
        if sc_key:
            ok = serverchan(sc_key, title, text_content)
            push_status.append(("Server酱", ok))
        if tg_token and tg_chat_id:
            ok = telegram_push(tg_token, tg_chat_id, title, text_content)
            push_status.append(("Telegram", ok))
        if ding_token:
            ok = dingtalk(ding_token, title, text_content)
            push_status.append(("钉钉", ok))
        if bark_key:
            ok = bark_push(bark_key, title, text_content)
            push_status.append(("Bark", ok))

        # 推送状态汇总
        if push_status:
            status_parts = [f"{'✅' if ok else '❌'} {name}" for name, ok in push_status]
            log(f"📱 推送状态: {' | '.join(status_parts)}")

if __name__ == '__main__':
    main()
