# Hermes MemHub Skill 使用说明

## 安装到 Hermes

将 `skills/hermes-memhub/` 复制到 Hermes 的 skills 目录，或在 Hermes 支持的 Skill 安装机制中引用本目录。

## 配置仓库路径

```bash
export MEMHUB_REPO=~/memhub-data
```

如果你已经有 Git remote：

```bash
cd ~/memhub-data
git remote add origin git@github.com:<user>/memhub-data.git
git branch -M main
git push -u origin main
```

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
python scripts/memhub.py --repo "$MEMHUB_REPO" sync
```
