# MemHub Skill

MemHub 是一个无服务端、Git-first 的个人 AI 记忆协议。本 Skill 让任意支持 Skill 的 Agent 能够读写、归档和同步用户的跨 Agent 统一记忆仓库。

## 能力

- 读取长期记忆上下文：`context --pack brief|standard|full|project`
- 写入默认 inbox：`remember`
- 检查与展示 inbox：`inbox list/show`
- 半自动归档到 canonical memory：`promote --dry-run/--apply`
- 导出给 chatbot 的上下文：`export chatbot`
- GitHub/Gitee 同步：OAuth、token fallback、SSH fallback

## 安装到任意支持 Skill 的 Agent

将本目录 `skills/memhub/` 复制到对应 skills 目录，或通过 SkillHub/ClawHub 安装。

## 配置仓库路径

```bash
export MEMHUB_REPO=~/memhub-data
```

如果未设置，脚本默认使用当前工作目录下的 `./memhub-data`。

## 首次初始化

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" init --name dateng --role "Product Manager"
```

## 配置 GitHub/Gitee 同步

推荐使用 OAuth setup 命令，而不是手动配置 remote。

### GitHub Device Flow

发布版应内置 OAuth App client id；开发版可通过环境变量、home 目录 `.env`、当前目录 `.env` 或参数传入：

```bash
export MEMHUB_GITHUB_CLIENT_ID=<github-oauth-app-client-id>
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --repo-name mymemhub
```

### Gitee Authorization Code

```bash
export MEMHUB_GITEE_CLIENT_ID=<gitee-oauth-app-client-id>
export MEMHUB_GITEE_CLIENT_SECRET=<gitee-oauth-app-client-secret>
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup gitee --repo-name mymemhub
```

### Fallback

```bash
# Token fallback
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --auth token --repo-name mymemhub

# SSH fallback
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --auth ssh --remote-method ssh --owner <login> --repo-name mymemhub --no-create
```

OAuth/token 会保存在本地 `.memhub/secrets.yaml`，并被 `.gitignore` 忽略。不要把 OAuth app 的 client secret、token 或 authorization code 提交到仓库。

## 常用命令

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" context --pack brief
python scripts/memhub.py --repo "$MEMHUB_REPO" remember "要记住的内容" --type fact --source agent
python scripts/memhub.py --repo "$MEMHUB_REPO" inbox list
python scripts/memhub.py --repo "$MEMHUB_REPO" inbox show <filename-or-id-fragment>
python scripts/memhub.py --repo "$MEMHUB_REPO" promote --dry-run
python scripts/memhub.py --repo "$MEMHUB_REPO" promote --apply
python scripts/memhub.py --repo "$MEMHUB_REPO" export chatbot
python scripts/memhub.py --repo "$MEMHUB_REPO" sync status
python scripts/memhub.py --repo "$MEMHUB_REPO" sync
```

## Agent 使用原则

- 读取前：如果任务依赖长期记忆，先 `sync`，再 `context --pack brief`。
- 写入时：用户明确要求记忆，或形成稳定决策/偏好/事实时，写入 inbox。
- 写入后：如果配置了 remote，执行 `sync`。
- 归档时：先 `promote --dry-run`，确认后再 `promote --apply`，然后 `sync`。
- setup：只有用户明确要求配置或切换同步服务时才执行。
- 失败：同步失败时不要删除本地数据；报告错误并保留本地文件。

## 发布包内容

发布到 SkillHub/ClawHub 时应包含：

```text
SKILL.md
README.md
scripts/memhub.py
templates/context-pack.md.j2
```

不应包含：

```text
__pycache__/
*.pyc
.git/
.memhub/secrets.yaml
用户个人记忆数据
```

## License

MIT-0
