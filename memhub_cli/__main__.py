from __future__ import annotations

import argparse
import datetime as dt
import os
import random
import string
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install with: pip install pyyaml") from exc

SCHEMA_VERSION = "0.1"


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def today_month() -> str:
    return dt.datetime.now().strftime("%Y-%m")


def short_id(n: int = 6) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def timestamp_id() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def read_yaml(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if data is not None else default


def write_yaml(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, width=1000)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def run_git(repo: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def ensure_repo(repo: Path) -> None:
    if not (repo / ".git").exists():
        run_git(repo, ["init"], check=False)


def init_repo(repo: Path, name: str = "user", role: str = "") -> None:
    repo.mkdir(parents=True, exist_ok=True)
    ensure_repo(repo)

    dirs = [
        ".memhub/templates",
        "identity",
        "projects/memhub",
        "knowledge",
        "relations",
        "timeline",
        "inbox",
        "exports",
        "archive",
    ]
    for d in dirs:
        (repo / d).mkdir(parents=True, exist_ok=True)

    config = {
        "schema_version": SCHEMA_VERSION,
        "repo": {"id": "user_main_memhub", "owner": name},
        "sync": {
            "type": "git",
            "remote": None,
            "branch": "main",
            "auto_pull": True,
            "auto_push": True,
            "pull_strategy": "rebase",
            "commit_prefix": "memhub:",
        },
        "inbox": {"auto_archive": False, "auto_archive_confidence_threshold": 0.92},
        "context": {"default_pack": "standard", "standard_token_budget": 2000},
    }
    write_yaml(repo / ".memhub/config.yaml", config)
    write_yaml(repo / ".memhub/schema.yaml", {"schema_version": SCHEMA_VERSION, "protocol": "MemHub"})
    write_yaml(repo / ".memhub/state.yaml", {"schema_version": SCHEMA_VERSION, "last_sync_at": None})

    profile = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_iso(),
        "profile": {
            "id": "user_main",
            "name": name,
            "display_name": name,
            "language": "zh-CN",
            "timezone": "Asia/Shanghai",
            "role": role,
            "company": None,
            "bio": "",
            "tags": [],
        },
        "communication": {
            "default_language": "zh-CN",
            "preferred_style": "direct_structured",
            "verbosity": "medium",
            "likes": ["结构化输出", "直接回答", "能落地的方案"],
            "dislikes": ["空泛表述", "过度道歉", "没有上下文就假装知道"],
        },
    }
    write_yaml(repo / "identity/profile.yaml", profile)

    preferences = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_iso(),
        "preferences": [
            {
                "id": "pref_response_style",
                "type": "preference",
                "status": "active",
                "category": "ai_interaction",
                "key": "response_style",
                "value": "结构化、直接、少废话",
                "content": "用户偏好结构化、直接、少废话的回答风格。",
                "confidence": 0.9,
                "importance": 0.9,
                "source": {"client": "manual"},
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
        ],
    }
    write_yaml(repo / "identity/preferences.yaml", preferences)
    write_yaml(repo / "identity/conventions.yaml", {"schema_version": SCHEMA_VERSION, "updated_at": now_iso(), "conventions": []})
    write_yaml(repo / "identity/constraints.yaml", {"schema_version": SCHEMA_VERSION, "updated_at": now_iso(), "constraints": []})

    active = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": now_iso(),
        "active_projects": [
            {
                "id": "memhub",
                "name": "MemHub",
                "priority": 1,
                "status": "active",
                "default": True,
                "path": "projects/memhub",
                "description": "跨平台 AI 记忆统一产品。",
            }
        ],
    }
    write_yaml(repo / "projects/_active.yaml", active)
    write_yaml(
        repo / "projects/memhub/context.yaml",
        {
            "schema_version": SCHEMA_VERSION,
            "project": {
                "id": "memhub",
                "name": "MemHub",
                "status": "active",
                "description": "无服务端、Git 同步、Agent Memory Protocol。",
                "goals": ["让多个 AI Agent 共享同一份用户记忆。", "不依赖中心化后端。"],
                "constraints": ["Local-first", "Git-first", "Agent-oriented"],
                "current_phase": "mvp",
                "updated_at": now_iso(),
            },
        },
    )
    write_yaml(repo / "projects/memhub/decisions.yaml", {"schema_version": SCHEMA_VERSION, "project_id": "memhub", "updated_at": now_iso(), "decisions": []})
    write_yaml(repo / "projects/memhub/tasks.yaml", {"schema_version": SCHEMA_VERSION, "project_id": "memhub", "updated_at": now_iso(), "tasks": []})
    write_yaml(repo / "projects/memhub/stack.yaml", {"schema_version": SCHEMA_VERSION, "project_id": "memhub", "updated_at": now_iso(), "stack": []})
    write_text(repo / "projects/memhub/notes.md", "# MemHub Notes\n\n")
    write_yaml(repo / "projects/memhub/history.yaml", {"schema_version": SCHEMA_VERSION, "project_id": "memhub", "events": []})

    write_yaml(repo / "knowledge/index.yaml", {"schema_version": SCHEMA_VERSION, "domains": []})
    write_yaml(repo / "knowledge/product.yaml", {"schema_version": SCHEMA_VERSION, "domain": "product", "items": []})
    write_yaml(repo / "knowledge/tech.yaml", {"schema_version": SCHEMA_VERSION, "domain": "tech", "items": []})
    write_yaml(repo / "relations/people.yaml", {"schema_version": SCHEMA_VERSION, "people": []})
    write_yaml(repo / "relations/orgs.yaml", {"schema_version": SCHEMA_VERSION, "orgs": []})
    write_yaml(repo / "relations/tools.yaml", {"schema_version": SCHEMA_VERSION, "tools": []})
    write_yaml(repo / f"timeline/{today_month()}.yaml", {"schema_version": SCHEMA_VERSION, "month": today_month(), "events": []})

    gitignore = """# MemHub generated local indexes/caches\n.memhub/cache/\n.memhub/indexes/\n*.db\n.DS_Store\n"""
    write_text(repo / ".gitignore", gitignore)

    commit_all(repo, "memhub: init repository")


def get_default_project(repo: Path) -> str | None:
    active = read_yaml(repo / "projects/_active.yaml", {})
    for p in active.get("active_projects", []):
        if p.get("default"):
            return p.get("id")
    if active.get("active_projects"):
        return active["active_projects"][0].get("id")
    return None


def build_context(repo: Path, project: str | None = None, pack: str = "standard") -> str:
    profile = read_yaml(repo / "identity/profile.yaml", {})
    prefs = read_yaml(repo / "identity/preferences.yaml", {})
    project_id = project or get_default_project(repo)

    lines: list[str] = []
    lines.append("# MemHub Context Pack")
    lines.append("")
    lines.append("<!-- Auto-generated by MemHub. Treat as user-auditable memory, not absolute truth. -->")
    lines.append("")

    p = profile.get("profile", {})
    c = profile.get("communication", {})
    lines.append("## User")
    lines.append(f"- Name: {p.get('name') or ''}")
    if p.get("role"):
        lines.append(f"- Role: {p.get('role')}")
    if p.get("company"):
        lines.append(f"- Company: {p.get('company')}")
    if p.get("bio"):
        lines.append(f"- Bio: {p.get('bio')}")
    lines.append(f"- Default language: {c.get('default_language', 'zh-CN')}")
    lines.append(f"- Communication style: {c.get('preferred_style', 'direct_structured')}")
    if c.get("likes"):
        lines.append("- Likes: " + ", ".join(c.get("likes", [])))
    if c.get("dislikes"):
        lines.append("- Dislikes: " + ", ".join(c.get("dislikes", [])))
    lines.append("")

    pref_items = prefs.get("preferences", [])
    active_prefs = [x for x in pref_items if x.get("status", "active") == "active"]
    active_prefs.sort(key=lambda x: x.get("importance", 0), reverse=True)
    if active_prefs:
        lines.append("## Important Preferences")
        for item in active_prefs[:8 if pack != "brief" else 3]:
            lines.append(f"- {item.get('content') or item.get('key') + ': ' + str(item.get('value'))}")
        lines.append("")

    if project_id:
        ctx = read_yaml(repo / f"projects/{project_id}/context.yaml", {})
        decisions = read_yaml(repo / f"projects/{project_id}/decisions.yaml", {})
        proj = ctx.get("project", {})
        lines.append(f"## Current Project: {proj.get('name', project_id)}")
        if proj.get("description"):
            lines.append(f"- Description: {proj.get('description')}")
        if proj.get("current_phase"):
            lines.append(f"- Phase: {proj.get('current_phase')}")
        if proj.get("goals"):
            lines.append("- Goals:")
            for g in proj.get("goals", [])[:5]:
                lines.append(f"  - {g}")
        if proj.get("constraints"):
            lines.append("- Constraints:")
            for con in proj.get("constraints", [])[:5]:
                lines.append(f"  - {con}")
        decs = decisions.get("decisions", [])
        if decs:
            lines.append("")
            lines.append("### Recent Decisions")
            for d in decs[:8 if pack != "brief" else 3]:
                lines.append(f"- [{d.get('created_at', '')[:10]}] {d.get('content')}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def remember(repo: Path, content: str, type_: str = "fact", source_client: str = "manual", project: str | None = None) -> Path:
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    sid = short_id()
    item_id = f"mem_{timestamp_id()}_{sid}"
    file = repo / "inbox" / f"{ts}-{source_client}-{sid}.yaml"
    item = {
        "schema_version": SCHEMA_VERSION,
        "inbox_id": f"inbox_{timestamp_id()}_{sid}",
        "status": "pending",
        "created_at": now_iso(),
        "source": {"client": source_client},
        "items": [
            {
                "id": item_id,
                "type": type_,
                "scope": "project" if project else "inbox",
                "status": "pending",
                "content": content,
                "suggested_target": f"projects/{project}/decisions.yaml" if type_ == "decision" and project else None,
                "confidence": 0.8,
                "importance": 0.6,
                "created_at": now_iso(),
            }
        ],
    }
    write_yaml(file, item)
    commit_all(repo, f"memhub: add inbox/{type_}: {content[:50]}")
    return file


def export_chatbot(repo: Path, project: str | None = None) -> Path:
    content = build_context(repo, project=project, pack="brief")
    out = repo / "exports/chatbot.md"
    header = f"<!-- Auto-generated by MemHub. Generated at: {now_iso()} -->\n\n"
    write_text(out, header + content)
    commit_all(repo, "memhub: export chatbot context")
    return out


def commit_all(repo: Path, message: str) -> None:
    ensure_repo(repo)
    run_git(repo, ["add", "."], check=False)
    status = run_git(repo, ["status", "--porcelain"], check=False)
    if status.stdout.strip():
        # Avoid failure if git user isn't configured globally.
        run_git(repo, ["-c", "user.name=MemHub", "-c", "user.email=memhub@example.local", "commit", "-m", message], check=False)


def sync_repo(repo: Path) -> str:
    ensure_repo(repo)
    remote = run_git(repo, ["remote"], check=False).stdout.strip()
    outputs = []
    if remote:
        pull = run_git(repo, ["pull", "--rebase"], check=False)
        outputs.append(pull.stdout + pull.stderr)
        push = run_git(repo, ["push"], check=False)
        outputs.append(push.stdout + push.stderr)
    else:
        outputs.append("No git remote configured; local repository only.\n")
    state = read_yaml(repo / ".memhub/state.yaml", {})
    state["last_sync_at"] = now_iso()
    write_yaml(repo / ".memhub/state.yaml", state)
    commit_all(repo, "memhub: update sync state")
    return "".join(outputs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="memhub", description="MemHub Protocol v0.1 reference CLI")
    parser.add_argument("--repo", default=os.environ.get("MEMHUB_REPO", "./memhub-data"), help="MemHub repository path")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize a MemHub repository")
    p_init.add_argument("--name", default="user")
    p_init.add_argument("--role", default="")

    p_context = sub.add_parser("context", help="Print context pack")
    p_context.add_argument("--project", default=None)
    p_context.add_argument("--pack", default="standard", choices=["brief", "standard", "full", "project"])

    p_rem = sub.add_parser("remember", help="Write a memory into inbox")
    p_rem.add_argument("content")
    p_rem.add_argument("--type", default="fact")
    p_rem.add_argument("--source", default="manual")
    p_rem.add_argument("--project", default=None)

    p_export = sub.add_parser("export", help="Export context")
    p_export.add_argument("target", choices=["chatbot"])
    p_export.add_argument("--project", default=None)

    sub.add_parser("sync", help="Git pull/push")

    args = parser.parse_args(argv)
    repo = Path(args.repo).expanduser().resolve()

    if args.cmd == "init":
        init_repo(repo, name=args.name, role=args.role)
        print(f"Initialized MemHub repository: {repo}")
    elif args.cmd == "context":
        print(build_context(repo, project=args.project, pack=args.pack), end="")
    elif args.cmd == "remember":
        file = remember(repo, args.content, type_=args.type, source_client=args.source, project=args.project)
        print(f"Wrote inbox item: {file}")
    elif args.cmd == "export":
        out = export_chatbot(repo, project=args.project)
        print(f"Exported chatbot context: {out}")
    elif args.cmd == "sync":
        print(sync_repo(repo), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
