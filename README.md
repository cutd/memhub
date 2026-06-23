# MemHub

MemHub is a serverless, Git-first personal AI memory protocol and reference implementation.

It lets AI agents read and write a shared, human-auditable memory repository using plain YAML/Markdown files.

## Components

- `protocol/` — MemHub Protocol v0.1 specification
- `skills/memhub/scripts/memhub.py` — the single source of truth for the
  implementation (also distributed standalone inside the MemHub Skill)
- `memhub_cli/` — thin wrapper that loads the skill script, so `python -m
  memhub_cli` and the `memhub` console script share one codebase
- `examples/memhub-data/` — sample MemHub Repository

## MVP Commands

```bash
python -m memhub_cli init --repo ./my-memhub
python -m memhub_cli context --repo ./my-memhub
python -m memhub_cli remember --repo ./my-memhub "记住这个"          # 直写 canonical
python -m memhub_cli remember --repo ./my-memhub "待确认" --inbox    # 进 inbox 审计缓冲
python -m memhub_cli search --repo ./my-memhub "关键词"
python -m memhub_cli forget --repo ./my-memhub "关键词" --apply       # 软归档
python -m memhub_cli export chatbot --repo ./my-memhub
python -m memhub_cli sync --repo ./my-memhub
```

`remember` 默认直接写入 canonical 记忆并本地提交（不自动推送）；多条记忆累积后用一次
`sync` 推送。`init`/`sync` 会注册一个结构化 Git merge 驱动，使多设备对同一记忆文件的并发追加
能自动合并而不冲突。
