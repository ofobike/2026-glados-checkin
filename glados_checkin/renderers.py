"""Message renderers for notification channels."""

from html import escape
import re


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


def _h(value):
    return escape(str(value), quote=True)


def text_to_apple_html(content):
    """Convert plain report text to Apple-style HTML for PushPlus."""
    lines = content.split('\n')
    html_parts = []
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        m = re.match(r'━━━━━━ (.+?) ━━━━━━', line)
        if m:
            if current_section:
                html_parts.append('</div>')
            section_name = m.group(1).strip()
            icon = section_name.split(' ')[0] if ' ' in section_name else '📊'
            title = ' '.join(section_name.split(' ')[1:]) if ' ' in section_name else section_name
            html_parts.append(
                f'<div class="card"><div class="card-header"><span class="icon">{_h(icon)}</span>'
                f'<div><div class="title">{_h(title)}</div></div></div>'
            )
            current_section = section_name
            continue

        progress_match = re.match(r'([█▓]+[░█▓]*\s*\d+%?)\s*(.*)', line)
        if progress_match:
            bar_text = progress_match.group(1)
            label = progress_match.group(2)
            pct_match = re.search(r'(\d+)%', bar_text)
            pct = pct_match.group(1) if pct_match else '50'
            pct_int = int(pct)
            color = 'green' if pct_int >= 80 else 'blue' if pct_int >= 50 else 'orange'
            html_parts.append('<div class="mb-8">')
            if label:
                html_parts.append(f'<div class="text-sm" style="margin-bottom:4px">{_h(label)}</div>')
            html_parts.append(f'<div class="progress-bar"><div class="progress-fill {color}" style="width:{pct}%"></div></div>')
            html_parts.append(f'<div class="text-xs" style="text-align:right;margin-top:2px">{pct}%</div></div>')
            continue

        kv_match = re.match(r'^(\S{1,2})\s*(.+?):\s*(.+)$', line)
        if kv_match:
            icon = kv_match.group(1)
            label = kv_match.group(2).strip()
            value = kv_match.group(3).strip()
            value_class = ''
            if any(k in value for k in ['✅', '可兑换', '储备充足', '达成', '+']):
                value_class = 'green'
            elif any(k in value for k in ['❌', '紧急', '过期']):
                value_class = 'red'
            elif any(k in value for k in ['⚠️', '即将到期']):
                value_class = 'orange'
            html_parts.append(
                f'<div class="row"><span class="label">{_h(icon)} {_h(label)}</span>'
                f'<span class="value {value_class}">{_h(value)}</span></div>'
            )
            continue

        if any(k in line for k in ['💕', '🌈', '😂', '🧩', '📖', '🍚', '🌅']):
            html_parts.append(f'<div class="fun-card"><div class="fun-text">{_h(line)}</div></div>')
            continue

        if '♈' in line and '运势' in line:
            html_parts.append(f'<div class="fun-card"><div class="fun-title">{_h(line)}</div>')
            continue
        if re.match(r'^\s+(💕|💼|💰|💪|🍀)', line):
            html_parts.append(f'<div class="fun-text" style="margin:4px 0">{_h(line)}</div>')
            continue

        if any(k in line for k in ['🎊', '✨', '🏆', '🎉', '新成就']):
            html_parts.append(f'<div class="alert success">{_h(line)}</div>')
            continue
        if any(k in line for k in ['🚨', '⚠️']) and '到期' in line:
            html_parts.append(f'<div class="alert danger">{_h(line)}</div>')
            continue
        if '等级' in line or '成就' in line:
            html_parts.append(f'<div class="mt-8"><span class="chip gold">{_h(line)}</span></div>')
            continue
        if '💡' in line or '🏖' in line:
            html_parts.append(f'<div class="alert info">{_h(line)}</div>')
            continue

        if '📅' in line and '距' in line and '还有' in line:
            html_parts.append(f'<div class="alert info">{_h(line)}</div>')
            continue
        if '🎉' in line and '今天是' in line:
            html_parts.append(f'<div class="alert success">{_h(line)}</div>')
            continue

        html_parts.append(f'<div class="mt-8">{_h(line)}</div>')

    if current_section:
        html_parts.append('</div>')

    return '\n'.join(html_parts)


def render_pushplus_html(content, current_time):
    """Render the full PushPlus HTML document."""
    return APPLE_HTML_TEMPLATE.format(content=text_to_apple_html(content), time=_h(current_time))


def text_to_telegram_html(content):
    """Convert plain report text to Telegram HTML."""
    lines = content.split('\n')
    html_parts = []

    for line in lines:
        line = line.strip()
        if not line:
            html_parts.append('')
            continue

        m = re.match(r'━━━━━━ (.+?) ━━━━━━', line)
        if m:
            section = m.group(1).strip()
            html_parts.append(f'\n<b>══ {_h(section)} ══</b>')
            continue

        if re.match(r'[█░▓]+', line):
            html_parts.append(f'<code>{_h(line)}</code>')
            continue

        kv_match = re.match(r'^(\S{1,2})\s*(.+?):\s*(.+)$', line)
        if kv_match:
            icon = kv_match.group(1)
            label = kv_match.group(2).strip()
            value = kv_match.group(3).strip()
            html_parts.append(f'{_h(icon)} <b>{_h(label)}:</b>  <i>{_h(value)}</i>')
            continue

        if any(k in line for k in ['💕', '🌈', '😂', '🧩', '📖', '🍚', '🌅']):
            html_parts.append(f'<blockquote>{_h(line)}</blockquote>')
            continue

        if re.match(r'^\s+(💕|💼|💰|💪|🍀)', line):
            html_parts.append(f'  <i>{_h(line.strip())}</i>')
            continue

        if any(k in line for k in ['🎊', '✨', '🏆', '🎉']):
            html_parts.append(f'<b>{_h(line)}</b>')
            continue

        if any(k in line for k in ['🚨', '⚠️']):
            html_parts.append(f'<b>❗ {_h(line)}</b>')
            continue

        if '📅' in line and '距' in line:
            html_parts.append(f'<i>{_h(line)}</i>')
            continue

        if '等级' in line or '成就' in line:
            html_parts.append(f'<b>{_h(line)}</b>')
            continue

        html_parts.append(_h(line))

    return '\n'.join(html_parts)

