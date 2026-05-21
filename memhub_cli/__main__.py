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



def inbox_files(repo: Path, status: str | None = "pending") -> list[Path]:
    files = sorted((repo / "inbox").glob("*.yaml"))
    if status in (None, "all"):
        return files
    out: list[Path] = []
    for path in files:
        data = read_yaml(path, {})
        if data.get("status", "pending") == status:
            out.append(path)
    return out


def inbox_summary(path: Path) -> str:
    data = read_yaml(path, {})
    items = data.get("items", []) or []
    status = data.get("status", "pending")
    created = str(data.get("created_at", ""))[:19]
    source = (data.get("source") or {}).get("client", "")
    first = items[0] if items else {}
    type_ = first.get("type", "")
    content = str(first.get("content", "")).replace("\n", " ")
    if len(content) > 90:
        content = content[:87] + "..."
    return f"{path.name}\t{status}\t{type_}\t{source}\t{created}\t{content}"


def inbox_list(repo: Path, status: str | None = "pending") -> str:
    files = inbox_files(repo, status=status)
    if not files:
        return "No inbox items found.\n"
    lines = ["file\tstatus\ttype\tsource\tcreated_at\tcontent"]
    lines.extend(inbox_summary(path) for path in files)
    return "\n".join(lines) + "\n"


def resolve_inbox_file(repo: Path, ref: str) -> Path:
    direct = Path(ref)
    candidates: list[Path] = []
    if direct.is_absolute() and direct.exists():
        candidates.append(direct)
    candidates.extend([
        repo / "inbox" / ref,
        repo / "inbox" / (ref if ref.endswith(".yaml") else f"{ref}.yaml"),
    ])
    candidates.extend(sorted((repo / "inbox").glob(f"*{ref}*.yaml")))
    seen: set[Path] = set()
    unique = []
    for c in candidates:
        c = c.resolve()
        if c.exists() and c not in seen:
            unique.append(c)
            seen.add(c)
    if not unique:
        raise SystemExit(f"Inbox item not found: {ref}")
    if len(unique) > 1:
        names = ", ".join(x.name for x in unique[:5])
        raise SystemExit(f"Ambiguous inbox ref: {ref}. Matches: {names}")
    return unique[0]


def inbox_show(repo: Path, ref: str) -> str:
    path = resolve_inbox_file(repo, ref)
    return path.read_text(encoding="utf-8")


def item_project(item: dict[str, Any]) -> str | None:
    target = item.get("suggested_target") or ""
    parts = str(target).split("/")
    if len(parts) >= 3 and parts[0] == "projects":
        return parts[1]
    return None


def suggested_target_for_item(repo: Path, item: dict[str, Any]) -> Path:
    type_ = item.get("type", "fact")
    if item.get("suggested_target"):
        return repo / str(item["suggested_target"])
    if type_ == "decision":
        project = item_project(item) or get_default_project(repo) or "memhub"
        return repo / f"projects/{project}/decisions.yaml"
    if type_ == "preference":
        return repo / "identity/preferences.yaml"
    if type_ == "constraint":
        return repo / "identity/constraints.yaml"
    if type_ == "convention":
        return repo / "identity/conventions.yaml"
    if type_ == "knowledge":
        return repo / "knowledge/product.yaml"
    if type_ in {"event", "fact"}:
        return repo / f"timeline/{today_month()}.yaml"
    return repo / "knowledge/product.yaml"


def canonical_entry(item: dict[str, Any], inbox_data: dict[str, Any], source_path: Path) -> dict[str, Any]:
    source = inbox_data.get("source") or {}
    return {
        "id": item.get("id") or f"mem_{timestamp_id()}_{short_id()}",
        "type": item.get("type", "fact"),
        "status": "active",
        "content": item.get("content", ""),
        "confidence": item.get("confidence", 0.8),
        "importance": item.get("importance", 0.6),
        "source": source,
        "created_at": item.get("created_at") or inbox_data.get("created_at") or now_iso(),
        "promoted_at": now_iso(),
        "inbox_ref": source_path.name,
    }


def append_unique(container: dict[str, Any], key: str, entry: dict[str, Any]) -> bool:
    items = container.setdefault(key, [])
    content = entry.get("content")
    for existing in items:
        if existing.get("content") == content:
            return False
    items.insert(0, entry)
    container["updated_at"] = now_iso()
    return True


def apply_item_to_target(repo: Path, target: Path, item: dict[str, Any], inbox_data: dict[str, Any], source_path: Path) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    data = read_yaml(target, {}) or {}
    rel = target.relative_to(repo).as_posix()
    entry = canonical_entry(item, inbox_data, source_path)
    type_ = item.get("type", "fact")

    if rel.startswith("projects/") and rel.endswith("/decisions.yaml"):
        data.setdefault("schema_version", SCHEMA_VERSION)
        if "project_id" not in data:
            data["project_id"] = rel.split("/")[1]
        changed = append_unique(data, "decisions", entry)
    elif rel == "identity/preferences.yaml":
        data.setdefault("schema_version", SCHEMA_VERSION)
        changed = append_unique(data, "preferences", entry)
    elif rel == "identity/constraints.yaml":
        data.setdefault("schema_version", SCHEMA_VERSION)
        changed = append_unique(data, "constraints", entry)
    elif rel == "identity/conventions.yaml":
        data.setdefault("schema_version", SCHEMA_VERSION)
        changed = append_unique(data, "conventions", entry)
    elif rel.startswith("knowledge/"):
        data.setdefault("schema_version", SCHEMA_VERSION)
        data.setdefault("domain", target.stem)
        changed = append_unique(data, "items", entry)
    elif rel.startswith("timeline/"):
        data.setdefault("schema_version", SCHEMA_VERSION)
        data.setdefault("month", target.stem)
        event = dict(entry)
        event.setdefault("date", str(entry.get("created_at", ""))[:10])
        changed = append_unique(data, "events", event)
    else:
        data.setdefault("schema_version", SCHEMA_VERSION)
        changed = append_unique(data, "items", entry)

    if changed:
        write_yaml(target, data)
    return changed


def promote_plan(repo: Path, refs: list[str] | None = None, status: str = "pending") -> list[tuple[Path, dict[str, Any], dict[str, Any], Path]]:
    if refs:
        files = [resolve_inbox_file(repo, ref) for ref in refs]
    else:
        files = inbox_files(repo, status=status)
    plan: list[tuple[Path, dict[str, Any], dict[str, Any], Path]] = []
    for path in files:
        data = read_yaml(path, {}) or {}
        if status != "all" and data.get("status", "pending") != status and not refs:
            continue
        for item in data.get("items", []) or []:
            if item.get("status", "pending") not in {"pending", "accepted"}:
                continue
            target = suggested_target_for_item(repo, item)
            plan.append((path, data, item, target))
    return plan


def promote(repo: Path, refs: list[str] | None = None, apply: bool = False, status: str = "pending") -> str:
    plan = promote_plan(repo, refs=refs, status=status)
    if not plan:
        return "No promotable inbox items found.\n"

    lines = ["Promote plan:"]
    changed_files: set[Path] = set()
    touched_inbox: dict[Path, dict[str, Any]] = {}
    for path, data, item, target in plan:
        rel_target = target.relative_to(repo).as_posix()
        content = str(item.get("content", ""))
        lines.append(f"- {path.name} :: {item.get('type', 'fact')} -> {rel_target}")
        lines.append(f"  content: {content}")
        if apply:
            changed = apply_item_to_target(repo, target, item, data, path)
            item["status"] = "promoted"
            item["promoted_at"] = now_iso()
            item["promoted_to"] = rel_target
            touched_inbox[path] = data
            if changed:
                changed_files.add(target)

    if apply:
        for path, data in touched_inbox.items():
            items = data.get("items", []) or []
            if items and all(item.get("status") == "promoted" for item in items):
                data["status"] = "promoted"
            data["updated_at"] = now_iso()
            write_yaml(path, data)
        commit_all(repo, "memhub: promote inbox to canonical")
        lines.append(f"Applied. Updated {len(changed_files)} canonical file(s), marked {len(touched_inbox)} inbox file(s).")
    else:
        lines.append("Dry run only. Re-run with --apply to write canonical files and mark inbox items promoted.")
    return "\n".join(lines) + "\n"

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

    p_inbox = sub.add_parser("inbox", help="Inspect inbox items")
    inbox_sub = p_inbox.add_subparsers(dest="inbox_cmd", required=True)
    p_inbox_list = inbox_sub.add_parser("list", help="List inbox items")
    p_inbox_list.add_argument("--status", default="pending", choices=["pending", "promoted", "all"])
    p_inbox_show = inbox_sub.add_parser("show", help="Show one inbox YAML file")
    p_inbox_show.add_argument("ref")

    p_promote = sub.add_parser("promote", help="Promote inbox items into canonical memory")
    p_promote.add_argument("refs", nargs="*", help="Optional inbox filename/id substrings. Defaults to all pending items.")
    p_promote.add_argument("--dry-run", action="store_true", help="Preview only; this is the default unless --apply is set")
    p_promote.add_argument("--apply", action="store_true", help="Write canonical files and mark inbox items promoted")
    p_promote.add_argument("--status", default="pending", choices=["pending", "all"], help="Inbox status to scan when refs are omitted")

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
    elif args.cmd == "inbox":
        if args.inbox_cmd == "list":
            print(inbox_list(repo, status=args.status), end="")
        elif args.inbox_cmd == "show":
            print(inbox_show(repo, args.ref), end="")
    elif args.cmd == "promote":
        refs = args.refs if args.refs else None
        print(promote(repo, refs=refs, apply=args.apply, status=args.status), end="")
    elif args.cmd == "export":
        out = export_chatbot(repo, project=args.project)
        print(f"Exported chatbot context: {out}")
    elif args.cmd == "sync":
        print(sync_repo(repo), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
