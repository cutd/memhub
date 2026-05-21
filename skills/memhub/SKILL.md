---
name: memhub
version: 0.1.0
description: 使用 MemHub Protocol v0.1 读写用户的跨 Agent 统一记忆仓库。当用户要求记住信息、读取个人/项目上下文、生成 chatbot 注入文本、同步 Git 记忆仓库时使用。
tags:
  - memory
  - memhub
  - github
  - gitee
  - sync
  - agent-memory
license: MIT
---

# MemHub Skill

MemHub 是一个无服务端、Git-first 的个人 AI 记忆协议。本 Skill 让 Agent 能够读取、写入和同步符合 MemHub Protocol v0.1 的记忆仓库。

## 触发场景

使用本 Skill 当：

- 用户说“记住这个”、“帮我记一下”、“以后记得”。
- 用户问“我的偏好是什么”、“当前项目上下文是什么”。
- 用户需要把记忆注入到 Gemini/元宝/豆包/Cursor/Claude Code。
- 会话开始时需要读取用户长期记忆。
- 会话结束时需要把关键决策/偏好/事实写入 inbox。

## 环境变量

推荐设置：

```bash
export MEMHUB_REPO=/path/to/memhub-data
```

同步 setup 可选使用：

```bash
# OAuth app 配置
export MEMHUB_GITHUB_CLIENT_ID=...
export MEMHUB_GITEE_CLIENT_ID=...
export MEMHUB_GITEE_CLIENT_SECRET=...

# Token fallback
export MEMHUB_GITHUB_TOKEN=...
export MEMHUB_GITEE_TOKEN=...
```

如果未设置，脚本默认使用当前工作目录下的 `./memhub-data`。

## 命令

本 Skill 提供一个 Python CLI：`scripts/memhub.py`。

```bash
# 初始化仓库
python scripts/memhub.py --repo ~/memhub-data init --name dateng --role "Product Manager"

# 读取上下文
python scripts/memhub.py --repo ~/memhub-data context
python scripts/memhub.py --repo ~/memhub-data context --pack brief

# 写入 inbox
python scripts/memhub.py --repo ~/memhub-data remember "用户偏好结构化直接的回答" --type preference --source agent
python scripts/memhub.py --repo ~/memhub-data remember "MemHub 采用 Git-first 架构" --type decision --project memhub --source agent

# 检查 inbox
python scripts/memhub.py --repo ~/memhub-data inbox list
python scripts/memhub.py --repo ~/memhub-data inbox list --status all
python scripts/memhub.py --repo ~/memhub-data inbox show <filename-or-id-fragment>

# 将 inbox 半自动归档到 canonical memory
python scripts/memhub.py --repo ~/memhub-data promote --dry-run
python scripts/memhub.py --repo ~/memhub-data promote --apply
python scripts/memhub.py --repo ~/memhub-data promote <filename-or-id-fragment> --apply

# 导出给 chatbot 的上下文
python scripts/memhub.py --repo ~/memhub-data export chatbot

# 同步 GitHub/Gitee（默认 OAuth；发布版应内置 GitHub/Gitee OAuth app 配置）
python scripts/memhub.py --repo ~/memhub-data sync setup github --repo-name mymemhub
python scripts/memhub.py --repo ~/memhub-data sync setup gitee --repo-name mymemhub
python scripts/memhub.py --repo ~/memhub-data sync setup github --auth token --repo-name mymemhub
python scripts/memhub.py --repo ~/memhub-data sync setup github --auth ssh --remote-method ssh --owner <login> --repo-name mymemhub --no-create
python scripts/memhub.py --repo ~/memhub-data sync status
python scripts/memhub.py --repo ~/memhub-data sync
```

## Agent 行为协议

### 总原则

- `MEMHUB_REPO` 是用户记忆仓库；不要把用户记忆写入代码仓库。
- GitHub/Gitee remote 只是同步后端；YAML/Markdown 文件仍是可信源数据。
- 自动写入默认进入 `inbox`，不要直接写 canonical memory。
- `sync setup` 会触发授权、创建仓库、修改 remote；**只有用户明确要求配置/切换同步时才执行**。
- OAuth/token/SSH 凭据、authorization code、client secret、access token 都属于敏感信息；不要在回答中复述。

### 对话开始：读取前同步

如果当前任务需要用户长期偏好、项目上下文或跨设备最新记忆，执行：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" sync
python scripts/memhub.py --repo "$MEMHUB_REPO" context --pack brief
```

- 如果 `sync` 成功，再使用 `context` 输出。
- 如果 `sync` 失败，不要丢弃本地数据；可以继续读取本地 `context`，但必须告知用户“远端同步失败，当前上下文可能不是最新”。
- 将 context 作为可审计上下文，不要当成绝对事实；遇到冲突时优先询问用户。

### 对话中：写入 inbox

当用户明确要求记忆，或对话中形成稳定偏好/决策/事实时，写入 inbox：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" remember "内容" --type fact --source agent
```

类型建议：

- `decision`：明确决策
- `preference`：稳定偏好
- `fact`：事实
- `knowledge`：可复用知识/结论
- `event`：重要事件
- `relation`：人物/组织/工具关系
- `constraint`：约束
- `convention`：惯例

写入后，如果仓库配置了 remote，执行：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" sync
```

### 同步 setup：只有用户明确要求时执行

当用户说“配置同步”、“连接 GitHub/Gitee”、“换成 Gitee/GitHub 同步”时，才执行 setup。

#### GitHub OAuth Device Flow

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --repo-name mymemhub
```

- 需要 `MEMHUB_GITHUB_CLIENT_ID` 或 `--client-id`。
- CLI 会输出授权 URL 和 user code；Agent 应把 URL/code 展示给用户，并等待用户完成授权。
- 不要要求用户把 access token 发到聊天里。

#### Gitee OAuth Authorization Code

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup gitee --repo-name mymemhub
```

- 需要 `MEMHUB_GITEE_CLIENT_ID` 和 `MEMHUB_GITEE_CLIENT_SECRET`，或对应参数。
- 默认监听 `127.0.0.1:8765/callback`。
- 如果运行环境无法打开浏览器或接收本地回调，可使用 `--no-browser` 或 `--manual-code`。

#### Token/SSH fallback

仅当用户明确选择高级方式时使用：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --auth token --repo-name mymemhub
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --auth ssh --remote-method ssh --owner <login> --repo-name mymemhub --no-create
```

### 同步失败与冲突处理

- 不要删除本地 `inbox`、canonical 文件或 `.git` 历史。
- 将错误摘要告诉用户，避免泄露 token/header。
- 如果 `git pull --rebase` 冲突，停止自动处理，报告冲突文件，让用户/Agent 单独修复。
- 如果 provider 授权失败，建议用户重新授权或切换 token/SSH fallback。
- 如果远端仓库创建失败但已存在，可以继续配置 remote 并尝试 sync。

### Canonical 归档

默认不要直接写 canonical memory。需要整理长期记忆时，先预览：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" inbox list
python scripts/memhub.py --repo "$MEMHUB_REPO" promote --dry-run
```

确认归档目标合理后再执行：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" promote --apply
python scripts/memhub.py --repo "$MEMHUB_REPO" sync
```

当前最小归档规则：

- `decision` → `projects/<project>/decisions.yaml`
- `preference` → `identity/preferences.yaml`
- `constraint` → `identity/constraints.yaml`
- `convention` → `identity/conventions.yaml`
- `knowledge` → `knowledge/product.yaml`
- `fact` / `event` → `timeline/YYYY-MM.yaml`

不要写入：

- 临时闲聊
- 未确认猜测
- 敏感信息，除非用户明确授权
- 无新增信息的重复内容

### 对话结束

如果对话中产生重要决策、偏好或事实：

1. 写入 inbox。
2. 必要时 `promote --dry-run` 给出归档建议。
3. 只有用户同意或规则非常明确时才 `promote --apply`。
4. 执行 `sync`。

## 发布与安全约束

- 不要把真实 token、client secret、OAuth code 写进 `SKILL.md`、README、示例或提交历史。
- `.memhub/secrets.yaml` 必须保持本地忽略。
- 发布到 SkillHub/ClawHub 的包应包含：`SKILL.md`、`README.md`、`scripts/memhub.py`、`templates/context-pack.md.j2`。
- 发布包不应包含 `__pycache__`、`.pyc`、`.git` 或用户个人记忆数据。

## 重要原则

- MemHub 只负责存取和同步，智能判断由 Agent 完成。
- 写入必须带 source，便于追溯。
- 自动提取默认进入 inbox，而不是直接污染 canonical memory。
- Git 仓库中的 YAML/Markdown 是唯一可信源数据。
