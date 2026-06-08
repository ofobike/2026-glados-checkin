# 🔄 同步上游更新指南

本项目 Fork 自 [lankerr/2026-glados-checkin](https://github.com/lankerr/2026-glados-checkin)，并添加了以下自定义功能：

- ✅ Server酱（微信公众号推送）
- ✅ 钉钉机器人推送
- ✅ cron-job.org 定时触发（移除了 GitHub Actions 自带 schedule）
- ✅ 签到热力图（近30天签到日历）
- ✅ 本月签到统计（签到率进度条）
- ✅ 积分变化明细（最近5条记录）
- ✅ 历史最高积分
- ✅ 会员续期倒计时预警
- ✅ 本次签到获得积分
- ✅ 签到成就系统（13种成就徽章）
- ✅ 每日签到运势
- ✅ 积分预测（预计达成日期）
- ✅ 周报/月报（周日/月末自动推送）
- ✅ 积分换算人民币
- ✅ 天气穿衣建议
- ✅ 假期倒计时
- ✅ 日出日落时间
- ✅ 自定义天气城市（WEATHER_CITY 环境变量）
- ✅ 自定义签到时间（CHECKIN_HOURS 环境变量）
- ✅ 签到日志导出（CSV）
- ✅ 今日头条新闻
- ✅ 加密货币/汇率行情
- ✅ 每日健康提示
- ✅ 每日电影推荐
- ✅ 签到率趋势（近4周）
- ✅ 签到时间分布分析
- ✅ 月度签到目标
- ✅ 签到小游戏
- ✅ 签到日记（MOOD_NOTE 环境变量）
- ✅ 世界问候语
- ✅ 服务器状态信息
- ✅ 历史上的今天
- ✅ 自动清理旧数据（10天）
- ✅ 土味情话
- ✅ 彩虹屁
- ✅ 星座运势（ZODIAC_SIGN 环境变量）
- ✅ 每日段子
- ✅ 脑筋急转弯
- ✅ 每日成语
- ✅ 今天吃什么
- ✅ 早安问候
- ✅ 自定义倒数日（COUNTDOWN_EVENTS 环境变量）
- ✅ 生活指数（紫外线/运动/洗车/穿衣/舒适度）

本文档说明如何安全地同步上游更新，同时保留自定义代码。

---

## 📋 前提条件

已配置上游仓库（本项目已完成）：

```bash
git remote add upstream https://github.com/lankerr/2026-glados-checkin.git
```

验证配置：

```bash
git remote -v
# origin    https://github.com/ofobike/2026-glados-checkin.git (fetch)
# origin    https://github.com/ofobike/2026-glados-checkin.git (push)
# upstream  https://github.com/lankerr/2026-glados-checkin.git (fetch)
# upstream  https://github.com/lankerr/2026-glados-checkin.git (push)
```

---

## 🔍 第一步：查看上游是否有更新

```bash
# 拉取上游最新代码（不会修改你的文件）
git fetch upstream

# 查看上游有哪些新提交
git log --oneline main..upstream/main
```

如果没有输出，说明上游没有新更新，无需操作。

---

## 📊 第二步：对比差异

```bash
# 查看具体改了哪些文件
git diff main upstream/main
```

重点关注 `checkin.py` 和 `glados_checkin/` 包的变化。现在 `checkin.py` 只是兼容入口，主要自定义代码已拆到包内模块。

---

## 🔀 第三步：合并更新

### 方式 A：普通合并（推荐）

```bash
git merge upstream/main
```

如果没有冲突，直接完成。如果有冲突，Git 会提示你手动解决。

### 方式 B：变基合并（保持提交历史整洁）

```bash
git rebase upstream/main
```

---

## ⚠️ 第四步：解决冲突

合并时如果出现冲突，Git 会标记冲突文件。打开冲突文件会看到：

```
<<<<<<< HEAD
你的代码（Server酱、钉钉等）
=======
上游作者的代码
>>>>>>> upstream/main
```

### 冲突解决规则

| 文件 | 处理方式 |
|------|----------|
| `checkin.py` | 保留兼容入口，通常只需要继续调用 `glados_checkin.cli.run()` |
| `glados_checkin/` | 保留你的自定义代码（推送、热力图、统计、Bark、心跳、兑换提醒等），同时谨慎接受上游核心签到逻辑更新 |
| `.github/workflows/checkin.yml` | 保留你的配置（无 schedule + SEND_KEY + DINGTALK_TOKEN） |
| `README.md` | 接受上游更新，或保留你的版本 |
| `SYNC_GUIDE.md` | 保留你的版本（此文件为自定义） |
| 其他文件 | 通常直接接受上游更新 |

### 解决步骤

1. 打开冲突文件，找到 `<<<<<<<` 标记
2. 决定保留哪些代码，删除冲突标记
3. 保存文件
4. 标记冲突已解决：

```bash
git add <冲突文件>
git commit -m "merge: sync upstream changes, keep custom push features"
```

---

## 🚀 第五步：推送到你的仓库

```bash
git push origin main
```

---

## 📝 完整操作示例

```bash
# 1. 拉取上游
git fetch upstream

# 2. 查看更新
git log --oneline main..upstream/main

# 3. 合并
git merge upstream/main

# 4. 如有冲突，手动解决后
git add .
git commit -m "merge: sync upstream changes"

# 5. 推送
git push origin main
```

---

## 💡 小贴士

- **定期检查**：建议每月检查一次上游更新
- **先备份**：合并前可以先创建备份分支：`git backup main`
- **测试验证**：合并后手动 Run workflow 测试签到是否正常
- **不懂就问**：遇到冲突不确定怎么处理，可以提 Issue 或找人帮忙

---

## 🆘 紧急回滚

如果合并后出问题，可以回滚到合并前的状态：

```bash
# 查看提交历史，找到合并前的 commit hash
git log --oneline

# 回滚到指定提交
git reset --hard <commit-hash>

# 强制推送（⚠️ 谨慎使用）
git push origin main --force
```

---

## 📌 自定义代码位置参考

以下是你添加的自定义代码，在合并冲突时需要特别注意保留：

### glados_checkin — 推送渠道

| 位置 | 内容 |
|------|------|
| `glados_checkin/notifiers.py` | PushPlus / Server酱 / 钉钉 / Telegram 推送 |
| `glados_checkin/bark.py` | Bark 摘要、分级、角标、跳转、复制、多设备、事件推送 |
| `glados_checkin/renderers.py` | PushPlus Apple HTML 模板、纯文本→PushPlus/Telegram HTML 转换 |

### glados_checkin/app.py — 数据统计

| 位置 | 内容 |
|------|------|
| `record_checkin_date()` 函数 | 签到日期+时间记录 |
| `record_checkin_time()` 函数 | 签到时间分布记录 |
| `format_heatmap()` 函数 | 签到热力图（30天） |
| `format_monthly_stats()` 函数 | 本月签到统计 |
| `format_checkin_rate_trend()` 函数 | 签到率趋势（4周） |
| `format_time_distribution()` 函数 | 签到时间分布分析 |
| `format_monthly_goal()` 函数 | 月度签到目标 |
| `get_max_points()` 函数 | 历史最高积分 |
| `format_renewal_alert()` 函数 | 会员续期预警 |
| `format_points_history_detail()` 函数 | 积分变化明细 |
| `get_points_prediction()` 函数 | 积分预测 |
| `check_achievements()` 函数 | 签到成就系统 |
| `format_achievements()` 函数 | 成就展示 |
| `format_new_achievements()` 函数 | 新成就通知 |
| `get_level()` 函数 | 签到等级系统 |
| `get_anniversary()` 函数 | 签到周年纪念 |
| `format_weekly_report()` 函数 | 周报生成 |
| `format_monthly_report()` 函数 | 月报生成 |
| `calc_rmb_value()` 函数 | 积分换算人民币 |
| `export_checkin_log()` 函数 | 签到日志导出（CSV） |
| `record_checkin_run()` / `send_heartbeat_check()` 函数 | 签到心跳监控 |
| `send_exchange_alerts()` / `_ready_exchange_plans()` 函数 | 积分可兑换 Bark 提醒 |
| `cleanup_old_data()` 函数 | 自动清理旧数据（10天） |
| `validate_cookie()` 函数 | Cookie 格式检测 |

### glados_checkin/app.py — 生活资讯

| 位置 | 内容 |
|------|------|
| `get_weather()` 函数 | 天气获取 |
| `get_clothing_advice()` 函数 | 天气穿衣建议 |
| `get_life_index()` 函数 | 生活指数（紫外线/运动/洗车/穿衣/舒适度） |
| `get_health_tip()` 函数 | 每日健康提示 |
| `get_holiday_countdown()` 函数 | 假期倒计时 |
| `get_sun_info()` 函数 | 日出日落时间 |
| `get_lunar_info()` 函数 | 农历/节气/节日 |
| `get_daily_news()` 函数 | 今日头条新闻 |
| `get_crypto_forex()` 函数 | 加密货币/汇率 |
| `get_movie_recommendation()` 函数 | 每日电影推荐 |
| `get_today_in_history()` 函数 | 历史上的今天 |
| `get_server_status()` 函数 | 服务器状态 |
| `get_countdown()` 函数 | 自定义倒数日 |
| `_load_countdown_events()` 函数 | 倒数日配置加载 |

### glados_checkin/app.py — 趣味内容

| 位置 | 内容 |
|------|------|
| `get_daily_fortune()` 函数 | 每日签到运势 |
| `get_daily_quote_en()` 函数 | 每日英语名言（Quotable API） |
| `get_ascii_celebration()` 函数 | ASCII Art 庆祝 |
| `get_sweet_nothing()` 函数 | 土味情话 |
| `get_rainbow_fart()` 函数 | 彩虹屁 |
| `get_zodiac_horoscope()` 函数 | 星座运势 |
| `get_daily_joke()` 函数 | 每日段子 |
| `get_riddle()` 函数 | 脑筋急转弯 |
| `get_daily_idiom()` 函数 | 每日成语 |
| `get_food_suggestion()` 函数 | 今天吃什么 |
| `get_morning_greeting()` 函数 | 早安问候 |
| `get_world_greeting()` 函数 | 世界问候语 |
| `get_mini_game()` 函数 | 签到小游戏 |
| `get_mood_note()` 函数 | 签到日记 |

### glados_checkin — 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SEND_KEY` | 无 | Server酱 |
| `DINGTALK_TOKEN` | 无 | 钉钉 |
| `BARK_KEY` | 无 | Bark（iOS 推送） |
| `BARK_SERVER` | `https://api.day.app` | Bark 服务地址 |
| `BARK_GROUP` | `GLaDOS` | Bark 通知分组 |
| `BARK_BADGE_MODE` | `days` | Bark 角标模式 |
| `BARK_BADGE` | 无 | Bark 固定角标 |
| `BARK_LOW_DAYS` | `7` | Bark 到期升级提醒阈值 |
| `BARK_LEVEL_*` / `BARK_SOUND_*` / `BARK_URL_*` | 按结果默认 | Bark 分级、铃声和跳转 |
| `BARK_ICON` / `BARK_IMAGE` | 无 | Bark 图标和配图 |
| `BARK_ACTION` / `BARK_CATEGORY` | 无 | Bark 点击动作和通知分类 |
| `BARK_CALL_ON_EXPIRE` / `BARK_AUTO_COPY` / `BARK_ARCHIVE` | `false` / `false` / `true` | Bark 电话式提醒、自动复制和归档 |
| `BARK_COPY_MODE` / `BARK_COPY_LIMIT` | `summary` / `800` | Bark 长按复制内容，默认限制大小以避免 413 |
| `BARK_TTL` / `BARK_VOLUME` | 无 | Bark 保留时间和 critical 音量 |
| `RUN_MODE` | `checkin` | 运行模式，`heartbeat` 只检查心跳 |
| `HEARTBEAT_GRACE_MINUTES` | `12` | 签到后多少分钟未成功才告警 |
| `HEARTBEAT_BARK_LEVEL` / `HEARTBEAT_BARK_SOUND` / `HEARTBEAT_BARK_URL` | `timeSensitive` / `alarm` / Actions 页 | 心跳 Bark 告警 |
| `EXCHANGE_ALERT_ENABLED` | `true` | 积分可兑换提醒开关 |
| `EXCHANGE_BARK_LEVEL` / `EXCHANGE_BARK_SOUND` / `EXCHANGE_BARK_URL` | `timeSensitive` / `bell` / GLaDOS 页 | 兑换 Bark 提醒 |
| `WEATHER_CITY` | `杭州` | 天气城市 |
| `CHECKIN_HOURS` | `09:30,21:30` | 签到时间 |
| `MONTHLY_GOAL` | `25` | 月度目标 |
| `MOOD_NOTE` | 无 | 签到日记 |
| `ZODIAC_SIGN` | `水瓶座` | 星座 |
| `COUNTDOWN_EVENTS` | `结婚纪念日:11-18` | 倒数日 |
| `PUSH_LEVEL` | `all` | 推送级别 |

### checkin.yml

| 配置 | 说明 |
|------|------|
| `on:` | 仅保留 `workflow_dispatch`（无 schedule） |
| `env:` | 包含 `SEND_KEY`、`DINGTALK_TOKEN`、`TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID` |

### 同步时的关键原则

> ⚠️ **核心原则**：上游更新签到核心逻辑时接受，但**永远保留你的自定义函数和推送代码**。
>
> 具体来说：
> - `GLaDOS` 类的 `checkin()`、`get_status()`、`get_points()` → 接受上游更新
> - `glados_checkin/app.py` 的 `main()` 函数 → 保留你的推送逻辑，只更新签到流程
> - `glados_checkin/bark.py`、`glados_checkin/notifiers.py`、`glados_checkin/renderers.py` → 全部保留
> - `glados_checkin/config.py` 环境变量读取 → 全部保留

---

## 📅 同步历史记录

| 日期 | 上游提交 | 变更内容 | 操作 |
|------|----------|----------|------|
| 2026-06-07 | `9be83a6` chore: keep repository active [skip ci] | 代码精简，删除自定义功能，无核心逻辑改进 | ❌ 跳过 |

---

## 🎯 同步决策规则

**只在以下情况同步上游更新：**

| 场景 | 是否同步 | 说明 |
|------|----------|------|
| `GLaDOS` 类核心方法修改 | ✅ 同步 | `checkin()`、`get_status()`、`get_points()` 有实质改进 |
| 签到 API 或域名变更 | ✅ 同步 | 上游修复了 API 端点或域名问题 |
| 请求头/Cookie 处理优化 | ✅ 同步 | 关键逻辑改进 |
| Bug 修复（影响签到功能） | ✅ 同步 | 修复了签到失败等问题 |
| 代码清理/重构 | ❌ 跳过 | 无实质改进，可能删除我们的自定义功能 |
| 文档更新 | ❌ 跳过 | 不影响功能 |
| 删除功能/精简代码 | ❌ 跳过 | 上游删除的功能我们有更完整版本 |
| GitHub Actions 配置变更 | ❌ 跳过 | 我们用 cron-job.org，不需要上游的 schedule |

**快速判断方法：**
```bash
# 拉取上游
git fetch upstream

# 查看提交信息
git log --oneline main..upstream/main

# 如果提交信息包含以下关键词，大概率需要同步：
# - fix: checkin / API / domain / cookie
# - feat: new checkin method
# - refactor: GLaDOS class (如果核心逻辑有改进)

# 如果提交信息包含以下关键词，直接跳过：
# - chore: cleanup / keep active
# - docs: update README
# - style: formatting
```
