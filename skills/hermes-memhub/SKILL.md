---
name: hermes-memhub
description: 使用 MemHub Protocol v0.1 读写用户的跨 Agent 统一记忆仓库。当用户要求记住信息、读取个人/项目上下文、生成 chatbot 注入文本、同步 Git 记忆仓库时使用。
---

# Hermes MemHub Skill

MemHub 是一个无服务端、Git-first 的个人 AI 记忆协议。本 Skill 让 Hermes 能够读取、写入和同步符合 MemHub Protocol v0.1 的记忆仓库。

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
python scripts/memhub.py --repo ~/memhub-data remember "用户偏好结构化直接的回答" --type preference --source hermes
python scripts/memhub.py --repo ~/memhub-data remember "MemHub 采用 Git-first 架构" --type decision --project memhub --source hermes

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

# 同步 GitHub/Gitee
python scripts/memhub.py --repo ~/memhub-data sync setup github --repo-name mymemhub
python scripts/memhub.py --repo ~/memhub-data sync setup gitee --repo-name mymemhub
python scripts/memhub.py --repo ~/memhub-data sync setup github --auth ssh --remote-method ssh --owner <login> --repo-name mymemhub --no-create
python scripts/memhub.py --repo ~/memhub-data sync status
python scripts/memhub.py --repo ~/memhub-data sync
```

## Agent 行为约定

### 对话开始

如果当前任务需要用户长期偏好或项目上下文，应先执行：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" sync
python scripts/memhub.py --repo "$MEMHUB_REPO" context
```

将输出作为可审计上下文，而不是绝对事实。

### 对话中

当用户明确要求记忆时，直接写入 inbox：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" remember "内容" --type fact --source hermes
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

### 对话结束

如果对话中产生了重要决策、偏好或事实，可以写入 inbox，然后执行 sync。

### Canonical 归档

默认不要直接写 canonical memory。需要整理长期记忆时，先预览：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" inbox list
python scripts/memhub.py --repo "$MEMHUB_REPO" promote --dry-run
```

确认归档目标合理后再执行：

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" promote --apply
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

## 重要原则

- MemHub 只负责存取和同步，智能判断由 Agent 完成。
- 写入必须带 source，便于追溯。
- 自动提取默认进入 inbox，而不是直接污染 canonical memory。
- Git 仓库中的 YAML/Markdown 是唯一可信源数据。
