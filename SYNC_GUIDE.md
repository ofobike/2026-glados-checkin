# 🔄 同步上游更新指南

本项目 Fork 自 [lankerr/2026-glados-checkin](https://github.com/lankerr/2026-glados-checkin)，并添加了以下自定义功能：

- ✅ Server酱（微信公众号推送）
- ✅ 钉钉机器人推送
- ✅ cron-job.org 定时触发（移除了 GitHub Actions 自带 schedule）

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

重点关注 `checkin.py` 的变化，因为我们的自定义代码也在这个文件里。

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
| `checkin.py` | 保留你的自定义代码（Server酱、钉钉），同时接受上游的核心签到逻辑更新 |
| `.github/workflows/checkin.yml` | 保留你的配置（无 schedule + SEND_KEY + DINGTALK_TOKEN） |
| `README.md` | 接受上游更新，或保留你的版本 |
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

### checkin.py

| 位置 | 内容 |
|------|------|
| `serverchan()` 函数 | Server酱推送逻辑 |
| `dingtalk()` 函数 | 钉钉推送逻辑 |
| 环境变量读取 | `SEND_KEY`、`DINGTALK_TOKEN` |
| 推送触发逻辑 | `if sc_key:` 和 `if ding_token:` |

### checkin.yml

| 配置 | 说明 |
|------|------|
| `on:` | 仅保留 `workflow_dispatch`（无 schedule） |
| `env:` | 包含 `SEND_KEY` 和 `DINGTALK_TOKEN` |
