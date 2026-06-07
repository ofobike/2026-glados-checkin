# 🎁 每天+20积分，5分钟搞定 GLaDOS 自动签到

<div align="center">

**你不用写代码 · 不用买服务器 · 不用每天登录**

**一次配置，永久自动，每天 9:30 / 21:30 签到**

---

### ✨ 为什么选择本项目？

| 优势                  | 说明                                                |
| --------------------- | --------------------------------------------------- |
| ✅ **2026年验证可用** | 经过实测，确认在2026年4月20日正常工作               |
| ✅ **绝对可用**       | 修复了其他脚本失效的问题（token更新为glados.cloud） |
| ✅ **新手友好**       | 全程图解，不会也能照着做                            |
| ✅ **多渠道推送**     | 支持微信/Telegram/钉钉/Server酱 四大推送渠道       |
| ✅ **作者持续维护**   | 遇到问题提Issue，作者很乐意帮忙                     |

---

### 📱 签到成功预览

![签到成功示例](images/success.jpg)

> **每天签到能获得 +12 ~ +20 积分，累积可兑换会员时长！**

---

### 🚀 3步搞定，永久自动签到

```text
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ① Fork 项目    ──→  点一下右上角 Fork 按钮                 │
│                                                             │
│   ② 配置 Cookie  ──→  浏览器复制一下，贴到 GitHub Secrets    │
│                                                             │
│   ③ 配置 cron    ──→  5分钟填好，永久有效                    │
│                                                             │
│   ✅ 完成！每天自动签到 + 推送通知                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**[👉 点击开始配置](#-快速部署)**

---

[![Auto Checkin](https://github.com/lankerr/2026-glados-checkin/actions/workflows/checkin.yml/badge.svg)](https://github.com/lankerr/2026-glados-checkin/actions)
[![GitHub Stars](https://img.shields.io/github/stars/lankerr/2026-glados-checkin?style=social)](https://github.com/lankerr/2026-glados-checkin)

**⭐ 觉得有用？点个 Star 支持一下！**

</div>

---

## 📑 目录

- [💡 重要说明](#-重要说明)
- [🔥 为什么你需要这个](#-为什么你需要这个)
- [✨ 功能特点](#-功能特点)
- [🛠 配置参数](#-配置参数环境变量)
- [📱 推送渠道说明](#-推送渠道说明)
- [🚀 快速部署](#-快速部署)
- [⭐ 推荐方案：cron-job.org 配置定时](#-推荐方案-cron-joborg-配置定时)
- [💻 本地/独立服务器部署](#-本地独立服务器部署教程)
- [❄️ NixOS 服务配置](#️-nixos-服务配置)
- [📊 推送效果预览](#-推送效果预览)
- [❓ 常见问题](#-常见问题)
- [📂 项目文件](#-项目文件)
- [🤝 需要帮助](#-需要帮助)
- [📝 更新日志](#-更新日志)

---

## 💡 重要说明

> 为了确保定时签到稳定运行，推荐使用 **cron-job.org**（免费服务）来触发签到。
>
> GitHub Actions 的自带定时功能对新仓库不太稳定，可能不会自动触发。
>
> **别担心！** 配置 cron-job.org 只需要额外 5 分钟，一次搞定永久有效。
>
> [👉 跳转查看 cron-job.org 配置教程](#-推荐方案-cron-joborg-配置定时)

---

## 🔥 为什么你需要这个？

> > **⚠️ 重要：如果你使用其他签到脚本失败，显示 "please checkin via [https://glados.cloud](https://glados.cloud)"，请使用本项目！**

GLaDOS 在 2026 年初进行了 API 更新，**绝大多数旧签到脚本已失效**。我们通过抓包分析发现了问题：

| 问题       | 旧脚本                  | 本项目（已修复）           |
| ---------- | ----------------------- | -------------------------- |
| 签到 Token | `glados.one` ❌         | `glados.cloud` ✅          |
| 域名支持   | rocks/network ❌        | cloud ✅                   |
| 签到结果   | "please checkin via..." | "Checkin!" 或 "Repeats" ✅ |

<details>
<summary><b>🔬 技术细节：我们是怎样修复问题的（感兴趣的看）</b></summary>

### 🔬 我们的探索过程

#### 问题现象

- GitHub Actions 可以正常运行
- 推送消息显示 "成功0/1"
- 签到结果始终为 "please checkin via https://glados.cloud"
- 手动点击签到按钮正常，但机器人签到无效

#### 排查步骤

1️⃣ **浏览器抓包分析**

- 使用 Chrome DevTools 抓取真实签到请求
- 对比浏览器请求和 Python 脚本请求的差异

2️⃣ **尝试的方案（失败）**

- ❌ 添加更多 Headers（sec-ch-ua、sec-fetch-\* 等）
- ❌ 使用 requests.Session 保持会话
- ❌ 使用 curl_cffi 模拟浏览器 TLS 指纹
- ❌ 添加代理配置

3️⃣ **最终发现**
通过对比不同 token 值的请求结果：

```python
# 失败 ❌
{'token': 'glados.one'}  → "please checkin via https://glados.cloud"

# 成功 ✅
{'token': 'glados.cloud'} → "Checkin Repeats! Please Try Tomorrow"
```

**问题根源**：GLaDOS 更新了 API，签到 token 必须从 `glados.one` 改为 `glados.cloud`！

</details>

---

> **📢 重要提示**
>
> - GLaDOS 官网已迁移至 **glados.cloud**（不再是 glados.rocks）
> - 本项目专为 2026 积分制度优化，每天自动签到两次
> - 完全免费，使用 GitHub Actions，无需自己的服务器
> - 不会的话可以提 Issue，作者很乐意帮助技术新手！

---

## ✨ 功能特点

| 功能                    | 说明                                    |
| ----------------------- | --------------------------------------- |
| 🎯 **精准积分**         | 获取真实积分数据 + 每日变化量           |
| 🎁 **兑换提示**         | 显示当前可兑换选项及差额，带进度条      |
| ⏰ **每日两次**         | 早上 9:30 + 晚上 21:30 自动签到         |
| 🔄 **失败重试**         | 首次失败自动重试一次                    |
| 📱 **多渠道推送**       | 微信/Telegram/钉钉/Server酱 四选一或组合 |
| 📊 **积分趋势图**       | ASCII 趋势图展示近7天积分变化           |
| 🔥 **连续签到统计**     | 记录连续签到天数和最佳纪录              |
| 💰 **签到价值估算**     | 自动换算积分对应的会员天数和人民币      |
| 🎯 **智能兑换推荐**     | 根据积分增速推荐最优兑换方案            |
| 🔮 **积分预测**         | 预测何时能达到兑换门槛                  |
| 🏆 **签到成就系统**     | 解锁徽章：连续签到、积分里程碑等        |
| 🎰 **每日签到运势**     | 签到后随机生成今日运势                  |
| 🎮 **签到等级系统**     | 青铜→白银→黄金→铂金→钻石→王者 等级进阶 |
| 🎨 **ASCII Art 庆祝**   | 签到成功时显示庆祝图案                  |
| 🗓 **农历/节气/节日**   | 显示今日节气、传统节日、生肖年          |
| 💬 **每日英语名言**     | 每天推送一条编程/人生英语名言           |
| 🎂 **签到周年纪念**     | 里程碑庆祝：100天、1年等                |
| 🗓 **签到热力图**       | 近30天签到日历，一眼看清签到情况        |
| 📅 **本月签到统计**     | 本月签到天数/总天数 + 签到率进度条      |
| 📝 **积分变化明细**     | 展示最近积分变化记录及原因              |
| 🏅 **历史最高积分**     | 追踪积分历史峰值                        |
| 🚨 **续期预警**         | 会员到期前自动提醒续期                  |
| 🎁 **本次签到积分**     | 显示本次签到实际获得的积分数            |
| 📊 **周报/月报**        | 周日/月末自动推送汇总报告              |
| 👗 **天气穿衣建议**     | 根据温度自动推荐穿搭                    |
| 🏖 **假期倒计时**       | 显示距离最近法定节假日的天数            |
| 🌅 **日出日落**         | 显示当日日出日落时间和日照时长          |
| ☀️ **天气 + 每日一句**  | 推送附带天气预报和励志语录              |
| 🍪 **Cookie 过期告警**  | Cookie 失效时自动发送告警通知           |
| ☁️ **2026 API**         | 适配最新 glados.cloud API               |
| 🔄 **智能域名切换**     | 自动尝试 cloud → rocks → network        |
| 📋 **多账号支持**       | 一个配置管理多个 GLaDOS 账号            |
| 🌍 **自定义天气城市**   | 通过环境变量配置天气城市                |
| 🎯 **自定义签到时间**   | 通过环境变量配置签到时间                |
| 📋 **签到日志导出**     | 自动导出签到历史为 CSV 文件             |
| 🔧 **持续维护**         | 发现问题及时修复                        |

---

## 🛠 配置参数 (环境变量)

本项目支持以下环境变量配置：

| 变量名               | 必填  | 说明                                                                       |
| -------------------- | ----- | -------------------------------------------------------------------------- |
| `GLADOS_COOKIE`      | ✅ 是 | GLaDOS 的 Cookie。多个账号请用 `&` 或换行符分隔。                          |
| `PUSHPLUS_TOKEN`     | ❌ 否 | PushPlus 微信推送 Token。                                                  |
| `TELEGRAM_BOT_TOKEN` | ❌ 否 | Telegram 机器人的 Token（例如 `123456:ABC-DEF1234...`）                    |
| `TELEGRAM_CHAT_ID`   | ❌ 否 | 接收推送的 Telegram Chat ID                                                |
| `SEND_KEY`           | ❌ 否 | Server酱推送 Key（免费推送到微信公众号）                                   |
| `DINGTALK_TOKEN`     | ❌ 否 | 钉钉机器人 Webhook 的 access_token                                        |
| `PUSH_LEVEL`         | ❌ 否 | 推送级别：`all` (默认，每次均推送) 或 `fail_only` (仅有账号签到失败时推送) |
| `WEATHER_CITY`       | ❌ 否 | 天气城市，默认 `杭州`。例如 `北京`、`上海`                                |
| `CHECKIN_HOURS`      | ❌ 否 | 自定义签到时间，默认 `09:30,21:30`。多个时间用逗号分隔                    |

> 💡 **推送渠道可自由组合**：你可以同时配置多个推送渠道，签到结果会同时推送到所有已配置的渠道。详见 [推送渠道说明](#-推送渠道说明)。

---

## 📱 推送渠道说明

本项目支持 **4 种推送渠道**，可按需选择一个或多个：

| 渠道        | 平台         | 费用 | 获取方式                                                        | 需要的变量            |
| ----------- | ------------ | ---- | --------------------------------------------------------------- | --------------------- |
| **PushPlus** | 微信         | 免费 | [pushplus.plus](https://www.pushplus.plus) 微信扫码登录获取 Token | `PUSHPLUS_TOKEN`      |
| **Telegram** | Telegram     | 免费 | 通过 @BotFather 创建机器人，获取 Token 和 Chat ID               | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` |
| **Server酱** | 微信公众号   | 免费 | [sct.ftqq.com](https://sct.ftqq.com) 注册获取 SendKey           | `SEND_KEY`            |
| **钉钉**     | 钉钉         | 免费 | 创建钉钉群机器人，获取 Webhook access_token                     | `DINGTALK_TOKEN`      |

> 💡 **推荐**：如果你只选一个，推荐 **PushPlus**（配置最简单）或 **Telegram**（最稳定）。
>
> 所有渠道的推送内容格式一致，包含积分详情、进度条、趋势图、天气和每日一句。

---

## 🚀 快速部署

<details>
<summary><b>📚 给小白的科普：什么是 Fork、Cookie、Secrets？（新手必看）</b></summary>

> 💡 如果你已经熟悉这些概念，可以跳过这部分直接看 [快速部署步骤](#第一步fork-本仓库)

<details>
<summary><b>🍴 什么是 Fork？</b></summary>

**Fork** = 把别人的项目复制一份到你自己的账号下。

就像复印一份文档，原件还在别人那里，你有一份自己的副本可以随便改。Fork 之后这个项目就属于你了，你可以自己配置和使用。

</details>

<details>
<summary><b>🍪 什么是 Cookie？</b></summary>

**Cookie** = 网站记住你是谁的"通行证"。

当你登录 GLaDOS 后，网站会给你的浏览器一个"通行证"（Cookie），下次访问时浏览器出示这个通行证，网站就知道你是谁了。

我们需要把这个通行证告诉签到程序，这样程序就能"假装"是你去签到。

</details>

<details>
<summary><b>🔐 什么是 Secrets？</b></summary>

**Secrets** = 保险箱，用来存放敏感信息。

你的 Cookie 和 Token 都是隐私信息，不能直接写在代码里（否则别人都能看到）。GitHub Secrets 就像一个保险箱，把这些敏感信息锁起来，只有你的程序运行时才能访问。

</details>

<details>
<summary><b>⚙️ 什么是 GitHub Actions？</b></summary>

**GitHub Actions** = 免费的自动化机器人。

它可以按照你设定的时间表（比如每天 9:30）自动运行程序。你不需要自己的服务器，GitHub 会免费帮你跑代码。

</details>

<details>
<summary><b>▶️ 什么是 Run workflow？</b></summary>

**Run workflow** = 手动测试按钮。

| 按钮             | 作用                                               |
| ---------------- | -------------------------------------------------- |
| **Run workflow** | 立即执行一次（不管现在几点），用于测试配置是否正确 |
| **定时任务**     | 每天 9:30 和 21:30 自动执行，不需要手动操作        |

简单说：点 Run workflow 是**测试**，以后会**自动运行**。

</details>
</details>

---

### 第一步：Fork 本仓库

点击页面右上角的 **Fork** 按钮，将项目复制到你的账号下。

---

### 第二步：获取 Cookie 🍪

> ⚠️ **注意**：GLaDOS 官网已迁移到 **[https://glados.cloud](https://glados.cloud)**，请使用新域名！

#### 2.1 安装 Cookie 扩展

在 **Edge 浏览器** 的扩展商店搜索 cookie，安装 **Cookie-Editor** 或类似的 Cookie 管理扩展：

![Cookie-Editor 扩展](images/cookie-extension.png)

> 💡 **提示**：以下任意一个扩展都可以使用，只要能显示 `koa:sess` 和 `koa:sess.sig` 这两个 Cookie 就行！

![可选的 Cookie 扩展](images/cookie-alternative.png)

#### 2.2 登录 GLaDOS 并获取 Cookie

1. 打开 [https://glados.cloud](https://glados.cloud) 并登录
2. 进入 **签到页面**（Console → Checkin）
3. 点击浏览器右上角的 **Cookie-Editor** 扩展图标
4. 找到并复制这两个值：
   - `koa:sess` → 一串很长的字符串
   - `koa:sess.sig` → 一串较短的字符串

![获取 Cookie](images/glados-cookies.png)

#### 2.3 组合 Cookie（重要！）

将两个值按以下格式组合，**注意格式必须完全正确**：

```text
koa:sess=你的长字符串; koa:sess.sig=你的短字符串
```

**正确示例**：

```text
koa:sess=eyJ1c2VySWQiOjEyMzQ1Njc4OTB9; koa:sess.sig=abcdef123456
```

**常见错误**：

- ❌ 缺少分号 `;`
- ❌ 缺少空格（分号后需要一个空格）
- ❌ 值两边多了引号
- ❌ 复制了多余的空格或换行

#### 2.4 验证你的 Cookie 格式

运行以下 Python 代码验证格式是否正确：

```python
# 将你的 Cookie 粘贴到下面的引号中
cookie = "koa:sess=你的长字符串; koa:sess.sig=你的短字符串"

# 验证
if "koa:sess=" in cookie and "koa:sess.sig=" in cookie and "; " in cookie:
    parts = cookie.split("; ")
    if len(parts) == 2 and parts[0].startswith("koa:sess=") and parts[1].startswith("koa:sess.sig="):
        print("✅ Cookie 格式正确！")
    else:
        print("❌ 格式错误，请检查分号和空格")
else:
    print("❌ Cookie 缺少必要的字段")
```

---

### 第三步：配置 GitHub Secrets 🔐

1. 进入你 Fork 的仓库
2. 点击 **Settings**（设置）
3. 左侧菜单找到 **Secrets and variables** → **Actions**
4. 点击右上角 **New repository secret**

![添加 Secret](images/add-secret.png)

添加以下 Secret（至少配置 `GLADOS_COOKIE`，其余为可选推送渠道）：

| Name                 | Value                    | 必需  | 说明                   |
| -------------------- | ------------------------ | ----- | ---------------------- |
| `GLADOS_COOKIE`      | 第二步组合的 Cookie      | ✅ 是 | 签到凭证               |
| `PUSHPLUS_TOKEN`     | 微信推送 Token           | ❌ 否 | PushPlus 微信推送      |
| `SEND_KEY`           | Server酱 SendKey         | ❌ 否 | Server酱 微信公众号推送 |
| `DINGTALK_TOKEN`     | 钉钉 access_token        | ❌ 否 | 钉钉群机器人推送       |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token       | ❌ 否 | Telegram 推送          |
| `TELEGRAM_CHAT_ID`   | Telegram Chat ID         | ❌ 否 | Telegram 推送          |
| `PUSH_LEVEL`         | `all` 或 `fail_only`     | ❌ 否 | 推送级别控制           |

> 💡 至少配置一个推送渠道，否则签到结果只在 Actions 日志中可见。

---

### 第四步：获取推送 Token（可选）📱

<details>
<summary><b>PushPlus 微信推送（推荐）</b></summary>

1. 访问 [https://www.pushplus.plus](https://www.pushplus.plus)
2. 点击右上角 **登录**，使用微信扫码登录

![PushPlus 扫码登录](images/pushplus-checkin.png)

3. 登录后点击 **发送消息** → **一对一消息**
4. 复制页面上显示的 **Token**（类似 `05c3****dd36` 的字符串）

![获取 Token](images/pushplus-token.png)

5. 将 Token 添加到 GitHub Secrets，Name 填 `PUSHPLUS_TOKEN`

</details>

<details>
<summary><b>Telegram 推送</b></summary>

1. 在 Telegram 中搜索 [@BotFather](https://t.me/BotFather)，发送 `/newbot` 创建机器人
2. 获取 Bot Token（格式类似 `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）
3. 搜索 [@userinfobot](https://t.me/userinfobot) 获取你的 Chat ID
4. 将 Token 和 Chat ID 分别添加到 GitHub Secrets 的 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`

</details>

<details>
<summary><b>Server酱推送</b></summary>

1. 访问 [https://sct.ftqq.com](https://sct.ftqq.com) 注册登录
2. 在 **Key** 页面复制你的 SendKey
3. 将 SendKey 添加到 GitHub Secrets，Name 填 `SEND_KEY`

</details>

<details>
<summary><b>钉钉机器人推送</b></summary>

1. 在钉钉群中添加自定义机器人（群设置 → 智能群助手 → 添加机器人 → 自定义）
2. 获取 Webhook 地址中的 `access_token` 参数
3. 将 Token 添加到 GitHub Secrets，Name 填 `DINGTALK_TOKEN`

</details>

---

### 第五步：启用 Actions ⚡

1. 进入你 Fork 仓库的 **Actions** 标签页
2. 如果看到黄色提示，点击 **I understand my workflows, go ahead and enable them**
3. 点击左侧的 **GLaDOS 2026 Checkin**
4. 点击右侧 **Run workflow** 按钮手动测试一次

![启用 Actions](images/workflow.png)

> [!IMPORTANT]
>
> 由于 GitHub Actions 对新仓库的定时任务有限制（[详见说明](#-为什么-github-actions-定时不可靠)），我们推荐使用 **cron-job.org** 这项免费服务来触发签到。

---

## ⭐ 推荐方案：cron-job.org 配置定时

### 配置步骤

#### 第一步：获取 GitHub Personal Access Token

1. 访问 [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. 点击 **Generate new token** → **Generate new token (classic)**
3. 按下图配置：

![GitHub Token 设置](images/github_access_tokens.png)

| 选项           | 值                              |
| -------------- | ------------------------------- |
| **Name**       | `glados-cron`（任意名称）       |
| **Expiration** | 选择 90 天或更久                |
| **勾选权限**   | ✅ **workflow**（在 repo 下方） |

4. 点击底部 **Generate token**
5. **立即复制生成的 token**（格式类似 `ghp_1234567890abcdef...`，只显示一次！）

> 💡 Token 示例：`ghp_NXLTUqT51BFfilsaZNlaVstacNnkZc4PYCNa`

#### 第二步：注册 cron-job.org

1. 访问 [https://cron-job.org](https://cron-job.org) 注册账号（免费）
2. 注册后登录，点击 **Create Cronjob** 创建任务

#### 第三步：创建早签到任务（9:30）

![创建 Cron 任务](images/create_corn_job.png)

按照以下配置填写：

**基本信息**：

| 选项      | 填写                                                                                                   |
| --------- | ------------------------------------------------------------------------------------------------------ |
| **Title** | `GLaDOS 早签到`                                                                                        |
| **URL**   | `https://api.github.com/repos/你的用户名/2026-glados-checkin/actions/workflows/checkin.yml/dispatches` |

> ⚠️ **重要**：把 `你的用户名` 改成你的 GitHub 用户名！比如 `lankerr`

**执行时间**：选择每天 **09:30**（Asia/Shanghai 时区）

**高级配置**（点击 Advanced 展开）：

![高级配置](images/cron_advanced.png)

| 选项               | 值            |
| ------------------ | ------------- |
| **Request method** | POST          |
| **Time zone**      | Asia/Shanghai |

**请求头（Headers）**：点击 "+ 添加" 添加三行：

| Key             | Value                            |
| --------------- | -------------------------------- |
| `Accept`        | `application/vnd.github.v3+json` |
| `Authorization` | `token 你复制的GitHub_Token`     |
| `Content-Type`  | `application/json`               |

> ⚠️ **注意**：Authorization 的值是 `token ` + **空格** + 你的 Token，例如：`token ghp_NXLTUqT51BFfilsaZNlaVstacNnkZc4PYCNa`

**请求体（Request body）**：选择 Raw Body，填入：

```json
{ "ref": "main" }
```

![常用配置预览](images/cron_common.png)

配置完成后点击 **Save** 保存。

#### 第四步：创建晚签到任务（21:30）

复制早签到任务，创建第二个任务：

- Title 改为 `GLaDOS 晚签到`
- 执行时间改为 **21:30**
- 其他配置完全相同

#### 第五步：测试验证

1. 在任务列表点击 **Test run** 测试
2. 成功会显示 **204 No Content** ✅

![测试成功](images/cron_success.png)

3. 到 GitHub 仓库的 **Actions** 页面查看，应该有新的运行记录

---

### 🚨 常见陷阱与错误

| 错误                         | 现象         | 原因                   | 解决方法                                       |
| ---------------------------- | ------------ | ---------------------- | ---------------------------------------------- |
| **401 Unauthorized**         | 认证失败     | Authorization 格式错误 | 必须是 `token ghp_xxx`，注意 `token ` 后有空格 |
| **422 Unprocessable Entity** | 请求无法处理 | Body 缺少 ref 参数     | 改为 `{"ref": "main"}`                         |
| Accept 被截断                | 配置错误     | 输入框显示不全         | 完整值：`application/vnd.github.v3+json`       |
| Token 有空格                 | 认证失败     | Token 被意外截断       | Token 是连续字符串，中间不能有空格             |
| 权限不足                     | 403 错误     | Token 无 workflow 权限 | 重新生成 Token，勾选 workflow 权限             |

> 💡 **小贴士**：遇到 401/422 错误时，先检查上面三行 Headers 是否完全正确！

**🎉 完成！** 以后每天 9:30 和 21:30 会自动签到。

---

## 💻 本地/独立服务器部署教程

如果你有自己的长期运行的电脑（如树莓派、软路由、VPS 等），也可以非常简单地在本地运行：

### 第一步：安装依赖

首先确保你已经安装了 Python 3，然后安装依赖库：

```bash
git clone https://github.com/你的用户名/2026-glados-checkin.git
cd 2026-glados-checkin
pip install -r requirements.txt
```

### 第二步：配置并运行

使用环境变量传递 Cookie 并直接运行 Python 脚本：

```bash
# 必填：配置 Cookie
export GLADOS_COOKIE="koa:sess=xxxxxx; koa:sess.sig=yyyyyy"

# 可选：配置推送渠道（按需选择一个或多个）
export PUSHPLUS_TOKEN="xxx"
export SEND_KEY="xxx"
export DINGTALK_TOKEN="xxx"
export TELEGRAM_BOT_TOKEN="xxx"
export TELEGRAM_CHAT_ID="yyy"

# 可选：推送级别
export PUSH_LEVEL="all"  # 或 "fail_only"

# 执行签到
python3 checkin.py
```

### 第三步：设置定时任务 (Cron)

通过 `crontab -e` 配置每天自动执行（例如每天早上 9:30 和晚上 21:30）：

```bash
# 早签到 9:30
30 9 * * * export GLADOS_COOKIE="koa:sess=xxx..."; cd /path/to/2026-glados-checkin && python3 checkin.py >> glados.log 2>&1

# 晚签到 21:30
30 21 * * * export GLADOS_COOKIE="koa:sess=xxx..."; cd /path/to/2026-glados-checkin && python3 checkin.py >> glados.log 2>&1
```

> 💡 **提示**：如果配置了多个环境变量，建议写一个 shell 脚本来管理，避免 crontab 行过长。

---

## ❄️ NixOS 服务配置

本项目提供了标准的 Nix Flake，你可以直接作为 inputs 引入，系统会自动管理 Python 环境和依赖包。

### 使用方法 (Flakes)

在你的 `flake.nix` 中引入本项目：

```nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    glados-checkin.url = "github:lankerr/2026-glados-checkin"; # 若本地测试可改写为 path:/绝对路径
  };

  outputs = { self, nixpkgs, glados-checkin, ... }: {
    nixosConfigurations.my-server = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        # 引入 glados-checkin 的 NixOS 模块
        glados-checkin.nixosModules.default

        ({ config, pkgs, ... }: {
          # 配置服务
          services.glados-checkin = {
            enable = true;
            cookie = "koa:sess=xxx; koa:sess.sig=yyy";

            # 【可选】消息推送配置（按需配置）
            pushLevel = "all"; # 或 "fail_only"
            pushplusToken = "xxx";
            sendKey = "xxx";          # Server酱
            dingtalkToken = "xxx";    # 钉钉
            telegramBotToken = "yyy";
            telegramChatId = "zzz";
          };
        })
      ];
    };
  };
}
```

部署配置后执行 `sudo nixos-rebuild switch --flake .#my-server`，签到任务即会自动注册为 systemd timers。

---

## 📊 推送效果预览

签到成功后，你会收到类似这样的推送（以 Telegram/微信为例）：

```text
🌇 下午好，这是您的资产简报

👤 182****44@163.com

━━━━━━ 📊 核心资产报告 ━━━━━━

💰 当前积分: 146 (+20)
⏳ 可用天数: 353 天  ✅ 储备充足
📅 到期日期: 2027-05-26
🎁 本次获得: +20 积分
✅ 签到结果: Checkin Repeats! Please Try Tomorrow
🔥 连续签到: 15 天 (最佳: 30 天)
💰 积分价值: 约 29 天会员
🏅 历史最高: 146 积分

━━━━━━ 🎁 资产增值路径 ━━━━━━

████████ [✅ 可兑换 10天]
██████░░ 30天 [积攒中 还差54分]
██░░░░░░ 100天 [积攒中 还差354分]

🎯 最优方案: 200分兑换30天 (性价比0.15)
   预计 2026-06-15 达成 (还需54分, 日均+20分)

📅 本月签到: 6/7 天 [▓▓▓▓▓▓▓▓░░] 85%

🗓 近30天签到日历:
    一  二  三  四  五  六  日
⚫ ⚫ ⚫ ⚫ ⚫ 🟢 ⚫
🟢 🟢 🟢 🟢 🟢 🟢 ⚫
🟢 🟢 🟢 🟢 🟢 🟢 🟢
🟢 🟢 🟢 🟢 🟢 🟢 🟢
🟢 🟢 🟢 🟢
近30天签到: 25/30 天 (83%)

━━━━━━ 📝 积分变化明细 ━━━━━━

   +20 | checkin            | 06-07 09:30
   +20 | checkin            | 06-06 21:30
   +18 | checkin            | 06-06 09:30
   +20 | checkin            | 06-05 21:30
   +15 | checkin            | 06-05 09:30

📈 近7天趋势: +10 +20 +18 +20 +15 +20 (共+103)
█           █
█     █     █
█ █   █ █   █
06-01 06-02 06-03 06-04 06-05 06-06

⏰ 下次签到: 今天 21:30
🕒 更新于: 15:30:00

━━━━━━ 🌤 生活资讯 ━━━━━━

🌤 杭州: Clear +28°C
📖 "世界上只有一种英雄主义，就是看清生活的真相之后依然热爱生活。" —— 罗曼·罗兰《米开朗基罗传》
```

> 💡 实际推送内容会根据你的积分、会员状态和历史数据自动调整。签到热力图和积分明细需要积累几天数据后才会显示。

---

## ⏰ 自动运行时间

| 时间（北京时间） | 说明     |
| ---------------- | -------- |
| **09:30**        | 早间签到 |
| **21:30**        | 晚间签到 |

> 💡 **重要**：请使用 [cron-job.org](#-推荐方案-cron-joborg-配置定时) 配置定时任务。GitHub Actions 的 schedule 功能对新仓库不可靠，可能不会自动触发！

---

## ❓ 常见问题

<details>
<summary><b>Q: 为什么推荐 cron-job.org 而不是直接用 GitHub Actions 定时？</b></summary>

**GitHub Actions 的定时任务（schedule trigger）对新仓库有严格限制**：

| 仓库类型   | 定时任务状态 | 说明                        |
| ---------- | ------------ | --------------------------- |
| 新仓库     | ❌ 不触发    | GitHub 会暂停定时任务执行   |
| 不活跃仓库 | ❌ 不触发    | 长时间没有新活动的仓库      |
| 活跃仓库   | ✅ 正常触发  | 需要持续活跃 1-2 周后才恢复 |

**现象**：

- 手动点击 "Run workflow" 可以正常运行 ✅
- 定时任务不会自动执行 ❌
- Actions 页面没有定时运行记录

**解决方案**：

- **推荐**：使用 cron-job.org（免费、稳定、立即生效）
- **备选**：连续 1-2 周每天手动触发一次 + keep-alive.yml 维护活跃度

相关 GitHub Discussions：

- [Discussion #185355](https://github.com/orgs/community/discussions/185355) - 新仓库定时任务不运行
- [Discussion #185212](https://github.com/orgs/community/discussions/185212) - scheduled workflow 从不触发

[🔝 回到开头了解推荐方案](#-推荐方案-cron-joborg-配置定时)

</details>

<details>
<summary><b>Q: cron-job.org 测试返回 401/422 错误怎么办？</b></summary>

请对照以下检查：

**401 Unauthorized（认证失败）**：

```text
❌ Authorization: ghp_abc123...
✅ Authorization: token ghp_abc123...
```

注意：`token ` 前缀后面必须有一个**空格**！

**422 Unprocessable Entity（请求无法处理）**：

```text
❌ Body: {}
✅ Body: {"ref": "main"}
```

GitHub API 要求必须指定分支名。

**其他检查**：

- Accept 头是否完整：`application/vnd.github.v3+json`
- Token 是否有 `workflow` 权限
- Token 是否过期（检查 Expiration 设置）

[🔝 查看完整陷阱列表](#-常见陷阱与错误)

</details>

<details>
<summary><b>Q: 显示 "please checkin via https://glados.cloud" 怎么办？</b></summary>

这表示你使用的签到脚本已过期！GLaDOS 在 2026 年更新了 API，旧脚本的 token 值 `glados.one` 已失效。

**解决方案**：使用本项目，我们已经修复了这个问题（token 改为 `glados.cloud`）。

</details>

<details>
<summary><b>Q: 显示 "Checkin Repeats! Please Try Tomorrow" 是什么意思？</b></summary>

这表示**今天已经成功签到过了**！这是正常的成功响应，说明签到功能正常工作。

</details>

<details>
<summary><b>Q: Cookie 多久过期？</b></summary>

大约 30 天。过期后重新按第二步获取新 Cookie，更新 Secret 即可。

> 💡 本项目支持 **Cookie 过期自动告警**：如果检测到 Cookie 失效，会通过已配置的推送渠道发送告警通知。

</details>

<details>
<summary><b>Q: 支持多个账号吗？</b></summary>

支持！用英文符号 `&` 分隔多个 Cookie：

```text
cookie1&cookie2&cookie3
```

签到后会收到多账号汇总报告，方便一目了然。

</details>

<details>
<summary><b>Q: 没有收到推送通知怎么办？</b></summary>

1. 检查对应的 Secret 是否配置正确（`PUSHPLUS_TOKEN` / `SEND_KEY` / `DINGTALK_TOKEN` / `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`）
2. 在对应平台测试推送功能是否正常
3. 查看 Actions 运行日志是否有推送错误信息
4. 检查 `PUSH_LEVEL` 设置：如果是 `fail_only`，签到成功时不会推送

</details>

<details>
<summary><b>Q: Actions 运行失败怎么办？</b></summary>

1. 点击失败的运行记录查看详细日志
2. 检查 Cookie 格式是否正确
3. 如果还是不行，欢迎提 Issue！

</details>

<details>
<summary><b>Q: 天气显示的城市不对，怎么改？</b></summary>

默认天气城市为杭州。如需修改，编辑 `checkin.py` 中的 `WEATHER_CITY` 变量即可：

```python
WEATHER_CITY = "你的城市"  # 例如 "北京"、"上海"、"深圳"
```

</details>

---

## ⚠️ 为什么 GitHub Actions 定时不可靠？

### 问题背景

从 2025 年底开始，GitHub 对 **Actions 的定时任务（schedule trigger）** 实施了更严格的限制，影响了大量新仓库和不活跃仓库。

### 根本原因

这是 GitHub 的**资源管理策略**，用于减少闲置资源消耗：

1. **新仓库限制**：刚创建的仓库，定时任务默认不会自动运行
2. **活跃度要求**：仓库需要有持续的活动（commit、issue、PR 等）
3. **恢复周期**：通常需要 1-2 周的活跃期才会恢复定时任务

### 解决方案对比

| 方案                        | 优点                 | 缺点                | 推荐度     |
| --------------------------- | -------------------- | ------------------- | ---------- |
| **cron-job.org**            | 免费、稳定、立即生效 | 需要注册第三方服务  | ⭐⭐⭐⭐⭐ |
| GitHub Actions + keep-alive | 完全在 GitHub 内     | 需等待 1-2 周恢复期 | ⭐⭐       |
| 每天手动触发                | 简单直接             | 无法自动化          | ⭐         |

**因此强烈推荐使用 cron-job.org！** [🔝 查看配置教程](#-推荐方案-cron-joborg-配置定时)

---

## 📂 项目文件

| 文件                    | 说明                                        |
| ----------------------- | ------------------------------------------- |
| `checkin.py`            | 核心签到脚本（签到、数据统计、多渠道推送）  |
| `.github/workflows/checkin.yml` | GitHub Actions 工作流配置          |
| `requirements.txt`      | Python 依赖（仅 requests）                  |
| `flake.nix`             | Nix Flake 配置                              |
| `flake.lock`            | Nix Flake 锁定文件                          |
| `glados-checkin.nix`    | NixOS 服务模块定义                          |
| `SYNC_GUIDE.md`         | Fork 用户同步上游更新指南                   |
| `images/`               | 教程截图                                    |

---

## 🤝 需要帮助？

- 📝 **提 Issue**：遇到问题请提 Issue，作者很乐意帮助技术新手！
- ⭐ **Star**：如果对你有帮助，请点个 Star 支持一下
- 🍴 **Fork**：欢迎 Fork 并贡献代码
- 🔄 **同步更新**：Fork 用户可参考 [SYNC_GUIDE.md](SYNC_GUIDE.md) 同步上游最新代码

---

## 📝 更新日志

### v1.2.0 (2026-06-06) ✨ 功能增强

- ✅ 新增 Server酱推送支持（免费推送到微信公众号）
- ✅ 新增钉钉机器人推送支持
- ✅ 移除 GitHub Actions 自带 schedule，改用 cron-job.org 触发
- ✅ 新增 SYNC_GUIDE.md 同步上游更新指南

### v1.1.0 (2026-01-25) 🔥 重大修复

**问题**：签到始终返回 "please checkin via https://glados.cloud"，导致机器人无法签到。

**原因**：GLaDOS 官方更新了 API，签到 token 必须从 `glados.one` 改为 `glados.cloud`。

**修复**：更新 `checkin.py` 中的 token 参数。

**排查过程**：

1. 使用浏览器 DevTools 抓包分析真实签到请求
2. 对比 Python 脚本与浏览器请求的差异
3. 尝试添加 Headers、模拟 TLS 指纹等方案（均无效）
4. 最终通过测试不同 token 值发现问题根源

> 💡 如果你在使用其他签到项目遇到同样问题，可以参考本项目的修复方案！

### v1.0.0 (2026-01-20)

- 初始版本发布
- 支持 glados.cloud 域名
- PushPlus 微信推送
- GitHub Actions 自动签到

---

## 📝 License

MIT

---

<div align="center">

**Made with ❤️ for GLaDOS users in 2026**

**🔧 本项目经过 2026-04-20 验证，确认可用！**

**⭐ Star 一下，支持作者持续更新！⭐**

</div>
