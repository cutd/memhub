# MemHub

MemHub is a serverless, Git-first personal AI memory protocol and reference implementation.

It lets AI agents read and write a shared, human-auditable memory repository using plain YAML/Markdown files.

## Components

- `protocol/` — MemHub Protocol v0.1 draft
- `memhub_cli/` — minimal Python CLI/reference implementation
- `skills/memhub/` — generic MemHub Skill for OpenClaw, Hermes, and other agents
- `examples/memhub-data/` — sample MemHub Repository

## MVP Commands

```bash
python -m memhub_cli init --repo ./my-memhub
python -m memhub_cli context --repo ./my-memhub
python -m memhub_cli remember --repo ./my-memhub "记住这个"
python -m memhub_cli export chatbot --repo ./my-memhub
python -m memhub_cli sync --repo ./my-memhub
```
