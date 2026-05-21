# Hermes MemHub Skill 使用说明

## 安装到 Hermes

将 `skills/hermes-memhub/` 复制到 Hermes 的 skills 目录，或在 Hermes 支持的 Skill 安装机制中引用本目录。

## 配置仓库路径

```bash
export MEMHUB_REPO=~/memhub-data
```

## 配置 GitHub/Gitee 同步

推荐使用产品化 setup 命令，而不是手动配置 remote：

```bash
# GitHub：适合海外用户/开发者
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --repo-name mymemhub

# Gitee：适合中国大陆用户
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup gitee --repo-name mymemhub

# 如果已经配置好 SSH key，也可以使用 SSH remote
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --auth ssh --remote-method ssh --owner <login> --repo-name mymemhub --no-create
```

Token 可以通过 `--token`、`MEMHUB_GITHUB_TOKEN`、`MEMHUB_GITEE_TOKEN` 或交互输入提供。Token 会保存在本地 `.memhub/secrets.yaml`，并被 `.gitignore` 忽略。

## 首次初始化

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" init --name dateng --role "Product Manager"
```

## 常用命令

```bash
python scripts/memhub.py --repo "$MEMHUB_REPO" context
python scripts/memhub.py --repo "$MEMHUB_REPO" remember "要记住的内容" --type fact --source hermes
python scripts/memhub.py --repo "$MEMHUB_REPO" inbox list
python scripts/memhub.py --repo "$MEMHUB_REPO" inbox show <filename-or-id-fragment>
python scripts/memhub.py --repo "$MEMHUB_REPO" promote --dry-run
python scripts/memhub.py --repo "$MEMHUB_REPO" promote --apply
python scripts/memhub.py --repo "$MEMHUB_REPO" export chatbot
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup github --repo-name mymemhub
python scripts/memhub.py --repo "$MEMHUB_REPO" sync setup gitee --repo-name mymemhub
python scripts/memhub.py --repo "$MEMHUB_REPO" sync status
python scripts/memhub.py --repo "$MEMHUB_REPO" sync
```
