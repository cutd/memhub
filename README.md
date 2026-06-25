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
python -m memhub_cli --repo ./my-memhub onboard gitee --repo-name mymemhub  # 首次接入：拉取或建仓
python -m memhub_cli --repo ./my-memhub context
python -m memhub_cli --repo ./my-memhub remember "记住这个"          # 直写 canonical
python -m memhub_cli --repo ./my-memhub remember "待确认" --inbox    # 进 inbox 审计缓冲
python -m memhub_cli --repo ./my-memhub search "关键词"
python -m memhub_cli --repo ./my-memhub forget "关键词" --apply       # 软归档
python -m memhub_cli --repo ./my-memhub export chatbot
python -m memhub_cli --repo ./my-memhub sync
python -m memhub_cli --repo ./my-memhub doctor      # 自检自动同步是否就绪
```

> 首次在新机器/新 agent 接入已有记忆仓库，**用 `onboard`**：它会探测远端，已有记忆则
> 拉取为准（不播种默认数据），远端为空则初始化并推送。单机全新使用也可先 `init`。

`--repo` 是全局参数，须放在子命令之前（也可改用环境变量 `MEMHUB_REPO` 省略它）。

`remember` 默认直接写入 canonical 记忆并本地提交。配置 remote 后，写入会自动推送、
`context` 会自动拉取（均按小时级节流，可在 `.memhub/config.yaml` 调整），装了 skill 的
Agent 无需每次手动 `sync`；显式 `sync` 则忽略节流、立即同步，适合会话收尾兜底。
`init`/`sync` 会注册一个结构化 Git merge 驱动，使多设备对同一记忆文件的并发追加
能自动合并而不冲突。
