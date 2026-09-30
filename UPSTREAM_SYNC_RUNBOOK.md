# 🔧 Fork 上游同步实战操作手册（fetch / 合并 / 移植 / 推送）

> 本手册是 [SYNC_GUIDE.md](SYNC_GUIDE.md)（同步策略与决策规则）的**配套实战版**。
> SYNC_GUIDE 讲「什么该同步、什么该跳过」；本手册讲「具体怎么一步步做、踩过哪些坑」。
>
> 实战背景：本仓库 `ofobike/2026-glados-checkin` Fork 自 `lankerr/2026-glados-checkin`，
> 本地已把项目**包化**为 `glados_checkin/` 目录。2026-09 上游改了会话机制（新版 `gld:sess`），
> 本手册记录的就是「只把上游核心补丁移植进自己的包、不丢心血、不碰上游」的完整流程。

---

## 0. 前置条件

```bash
# 已配置 upstream（指向你 Fork 的来源仓库）
git remote -v
# origin    https://github.com/ofobike/2026-glados-checkin.git (fetch/push)   # 你自己的
# upstream  https://github.com/lankerr/2026-glados-checkin.git (fetch)        # 上游，仅 fetch
```

> ⚠️ **单向铁律**：永远只对 `origin` 做 push，绝不 `git push upstream`。
> 你通常也没有上游写权限，即使误推也会被 GitHub 403 拒绝。本流程全程不碰上游。

---

## 1. 六步标准流程（可复制粘贴）

### Step 0 ｜ 先铺安全网（备份当前 main）

```bash
# 在 main 上打一个本地备份分支，指向合并前的提交
git checkout main
git branch backup-pre-upstream-merge
# 万一出问题，一条命令回退：
#   git reset --hard backup-pre-upstream-merge
```

### Step 1 ｜ 只读拉取上游（⚠️ 注意本仓库 fetch 不落盘坑）

本仓库有个怪现象：`git fetch upstream` 之后，`upstream/main` 跟踪引用**不会稳定落盘**，
直接用 `git merge upstream/main` 会报「无法解析 upstream/main」。

✅ **正确做法**：只拉取目标分支，然后用 `FETCH_HEAD` 合并。

```bash
# 只拉 main，FETCH_HEAD 即上游 main 的最新提交
git fetch upstream main
git merge FETCH_HEAD --no-edit
echo "MERGE_EXIT=$?"
```

> 如果合并被冲突打断，冲突文件用 `git diff --name-only --diff-filter=U` 查看，
> 解完冲突后 `git add <文件>` 再 `git commit`。（详见 Step 3）

### Step 2 ｜ 合并前先量化「分叉有多大」

```bash
# 左 = 你本地 main 独有提交数；右 = 上游 main 独有提交数
git fetch upstream main
git rev-list --left-right --count main...FETCH_HEAD
# 例：61  69   （你 61 个、上游 69 个）
```

数字越大，冲突概率越高。本仓库那次是 61 vs 69，且从同一点两边各走各的，冲突几乎必然。

### Step 3 ｜ 合并冲突处理（核心：架构分歧）

本仓库特有冲突：**`checkin.py` 是「包化入口 vs 上游单文件」的架构级分歧**。

- 你的版本：`checkin.py` 只有 7 行（`from glados_checkin.cli import run`）
- 上游版本：`checkin.py` 是 500+ 行单文件大杂烩

✅ **处理原则（保留包 + 移植关键补丁）**：

```bash
# 1. 触发合并
git fetch upstream main && git merge FETCH_HEAD --no-edit

# 2. 对「纯入口/配置/文档」类冲突，直接取你自己的版本（--ours）
git checkout --ours checkin.py README.md .github/workflows/checkin.yml .gitignore
git add checkin.py README.md .github/workflows/checkin.yml .gitignore

# 3. 确认冲突清零
git diff --name-only --diff-filter=U   # 应为空
```

> 其余被自动合并的文件（如 `tests/`、`keep-alive.yml`）直接进暂存区，无需处理。

### Step 4 ｜ 把上游关键补丁「移植」进你的包（不丢心血的关键）

上游单文件里你想要的能力，手动搬进你的 `glados_checkin/app.py`，**而不是用上游覆盖你的包**。

本次实际移植的两处（2026-09 新版会话）：

| 补丁 | 落点（glados_checkin/app.py） | 作用 |
|------|-------------------------------|------|
| 新版 `gld:sess` 会话支持 | `CURRENT_SESSION_COOKIES` / `extract_cookie` / `validate_cookie` / `GLaDOS.__init__` | 2026-09 新版接口必需；旧版 `koa:sess` 保留兼容 |
| device-mismatch / 认证失败检测 | `main()` 签到循环 | `code==-2` / `device-mismatch` / `没有权限` 直接提示重新登录，停止无效重试 |

移植后用 Edit 工具精确到函数级改动，避免整体覆盖。

### Step 5 ｜ 本地验证（不联网、不用真 Cookie）

```bash
# 1. 语法编译
python -m py_compile glados_checkin/app.py && echo SYNTAX_OK

# 2. 无联网烟测（确认新逻辑生效）
python - <<'PY'
from glados_checkin.app import extract_cookie, validate_cookie, CURRENT_SESSION_COOKIES
print(CURRENT_SESSION_COOKIES)                       # ('gld:sess', 'gld:sess.sig')
print(extract_cookie("gld:sess=a; gld:sess.sig=b"))  # 正确识别新版
print(extract_cookie("koa:sess=a; koa:sess.sig=b"))  # 旧版仍兼容
PY
```

确认无误后再提交：

```bash
git add glados_checkin/app.py
git commit -m "Merge upstream/main: sync gld:sess session support + device-mismatch detection"
```

### Step 6 ｜ 推送到你自己的 origin（PAT 方式）

⚠️ **推送前必读坑**：如果本次合并包含 `.github/workflows/*.yml` 的改动，
**普通 PAT 会被 GitHub 拒绝**（`refusing ... without workflow scope`）。
所以需要给令牌 `workflow` 权限（细粒度令牌勾 `Workflows: Read and write`）。

```bash
# 用临时令牌推送，推完立刻还原 remote，令牌不落盘
TOKEN="github_pat_xxxx"   # 细粒度令牌，务必勾 Workflows 权限
git remote set-url origin "https://${TOKEN}@github.com/ofobike/2026-glados-checkin.git"
git push origin main
git remote set-url origin "https://github.com/ofobike/2026-glados-checkin.git"   # 还原

# 推送后对齐本地跟踪引用（沙箱里 fetch 不刷新时可手动更新）
git fetch origin
git status -sb   # 应 ahead 0
```

> 🔒 **令牌安全**：令牌等同你账号写权限，用完即焚——推完去 GitHub 删掉（Revoke）。
> 不要写进任何 memory / 项目文件，不要在群里粘贴。

---

## 2. 踩坑清单（都是实战踩过的）

| # | 坑 | 现象 | 解决 |
|---|----|------|------|
| 1 | `git fetch upstream` 不落盘远程跟踪分支 | `git merge upstream/main` 报「无法解析 upstream/main」 | 改用 `git fetch upstream main` + `git merge FETCH_HEAD` |
| 2 | 架构级冲突（包化 vs 单文件） | `checkin.py` 从开头到结尾整段冲突 | 对入口/配置/文档取 `--ours`；关键补丁手动移植进包 |
| 3 | 推包含 workflow 改动的合并被拒 | `remote rejected ... without workflow scope` | 令牌加 `workflow` 权限（细粒度勾 Workflows: RW） |
| 4 | 沙箱非交互环境读不到凭据 | `git push` 静默失败，`/dev/tty: No such device` | 用带令牌的临时 `remote set-url` 推送并立即还原 |
| 5 | 推送成功但 `status` 仍显示 ahead | 沙箱 `origin/main` 跟踪引用没刷新 | `git fetch origin`；必要时 `update-ref`/`ls-remote` 确认远端真实值 |
| 6 | 改完代码但 Secret 还是旧 Cookie | 签到仍报「没有权限」 | 去仓库 Secrets 把 `GLADOS_COOKIE` 换成完整 `gld:sess=...; gld:sess.sig=...` |

---

## 3. 验证同步真正生效

推送后**必须实测一次**，光看 commit 不算完：

1. 打开 `https://github.com/ofobike/2026-glados-checkin/actions`
2. 左侧选 **GLaDOS 2026 Checkin** → **Run workflow**（手动触发）
3. 日志出现 `当前积分: xx (+xx)` 且签到结果为
   `Today's observation logged. Return tomorrow...` → 成功
4. **不再出现** `没有权限` / `device-mismatch` / `Unauthorized`

> 若仍报「没有权限」：说明 Secret 里的 Cookie 不是完整新版 `gld:sess`，
> 回到 glados.cloud 用 Cookie-Editor 重新复制整段。

---

## 4. 紧急回滚

```bash
# 方案 A：回到备份分支（最安全）
git checkout backup-pre-upstream-merge
# 确认无误后，如需让 main 退回：
git checkout main
git reset --hard backup-pre-upstream-merge
git push origin main --force-with-lease

# 方案 B：直接 reset 到合并前提交
git log --oneline          # 找到合并前 commit
git reset --hard <commit>
git push origin main --force-with-lease
```

> ⚠️ `--force-with-lease` 比 `--force` 安全，会拒绝「远端有你不知道的新提交」的强推。
> 回滚前先确认没有别人往你仓库推过东西。
