#!/usr/bin/env python3
"""Hermes MemHub Skill wrapper.

Standalone copy of memhub_cli.__main__ for Hermes/OpenClaw skill installs.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import getpass
import json
import os
import random
import string
import subprocess
import sys
import threading
import time
import webbrowser
import http.server
import urllib.error
import urllib.parse
import urllib.request
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

    gitignore = """# MemHub generated local indexes/caches and secrets\n.memhub/cache/\n.memhub/indexes/\n.memhub/secrets.yaml\n.memhub/secrets/\n*.db\n.DS_Store\n"""
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


# --- Sync providers: GitHub / Gitee -------------------------------------------------

PROVIDERS: dict[str, dict[str, str]] = {
    "github": {
        "display": "GitHub",
        "api_base": "https://api.github.com",
        "web_base": "https://github.com",
        "git_host": "github.com",
        "env_token": "MEMHUB_GITHUB_TOKEN",
        "token_url": "https://github.com/settings/tokens?type=beta",
        "oauth_device_code_url": "https://github.com/login/device/code",
        "oauth_access_token_url": "https://github.com/login/oauth/access_token",
        "env_client_id": "MEMHUB_GITHUB_CLIENT_ID",
    },
    "gitee": {
        "display": "Gitee",
        "api_base": "https://gitee.com/api/v5",
        "web_base": "https://gitee.com",
        "git_host": "gitee.com",
        "env_token": "MEMHUB_GITEE_TOKEN",
        "token_url": "https://gitee.com/profile/personal_access_tokens",
        "oauth_authorize_url": "https://gitee.com/oauth/authorize",
        "oauth_access_token_url": "https://gitee.com/oauth/token",
        "env_client_id": "MEMHUB_GITEE_CLIENT_ID",
        "env_client_secret": "MEMHUB_GITEE_CLIENT_SECRET",
    },
}


def config_path(repo: Path) -> Path:
    return repo / ".memhub/config.yaml"


def secrets_path(repo: Path) -> Path:
    return repo / ".memhub/secrets.yaml"


def load_config(repo: Path) -> dict[str, Any]:
    return read_yaml(config_path(repo), {}) or {}


def save_config(repo: Path, config: dict[str, Any]) -> None:
    config.setdefault("schema_version", SCHEMA_VERSION)
    write_yaml(config_path(repo), config)


def load_secrets(repo: Path) -> dict[str, Any]:
    return read_yaml(secrets_path(repo), {}) or {}


def save_secrets(repo: Path, secrets: dict[str, Any]) -> None:
    path = secrets_path(repo)
    write_yaml(path, secrets)
    try:
        path.chmod(0o600)
    except OSError:
        pass


def ensure_gitignore_secret(repo: Path) -> None:
    path = repo / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    additions = [".memhub/secrets.yaml", ".memhub/secrets/"]
    changed = False
    for item in additions:
        if item not in existing.splitlines():
            existing = existing.rstrip() + ("\n" if existing.strip() else "") + item + "\n"
            changed = True
    if changed:
        write_text(path, existing)


def get_token(repo: Path, provider: str, explicit_token: str | None = None, require: bool = True) -> str | None:
    meta = PROVIDERS[provider]
    if explicit_token:
        return explicit_token
    if os.environ.get(meta["env_token"]):
        return os.environ[meta["env_token"]]
    secrets = load_secrets(repo)
    token = ((secrets.get("sync") or {}).get(provider) or {}).get("token")
    if token:
        return token
    if require:
        raise SystemExit(
            f"Missing {meta['display']} token. Pass --token, set {meta['env_token']}, "
            f"or run `memhub --repo <path> sync setup {provider}`. Token page: {meta['token_url']}"
        )
    return None


def store_token(repo: Path, provider: str, token: str, account: str | None = None) -> None:
    ensure_gitignore_secret(repo)
    secrets = load_secrets(repo)
    sync = secrets.setdefault("sync", {})
    item = sync.setdefault(provider, {})
    item["token"] = token
    if account:
        item["account"] = account
    item["updated_at"] = now_iso()
    save_secrets(repo, secrets)


def api_json(provider: str, method: str, path: str, token: str, payload: dict[str, Any] | None = None) -> tuple[int, dict[str, Any] | list[Any] | str]:
    meta = PROVIDERS[provider]
    url = meta["api_base"] + path
    data: bytes | None = None
    headers = {"Accept": "application/json", "User-Agent": "MemHub/0.1"}
    if provider == "github":
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
    else:  # gitee uses access_token in JSON/body for broad compatibility
        payload = dict(payload or {})
        payload.setdefault("access_token", token)
        if method.upper() == "GET":
            sep = "&" if "?" in url else "?"
            url = url + sep + urllib.parse.urlencode(payload)
        else:
            data = urllib.parse.urlencode(payload).encode("utf-8")
            headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return resp.status, {}
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body: dict[str, Any] | list[Any] | str = json.loads(raw)
        except json.JSONDecodeError:
            body = raw
        return exc.code, body


def provider_user(provider: str, token: str) -> str:
    status, body = api_json(provider, "GET", "/user", token)
    if status >= 400:
        raise SystemExit(f"{PROVIDERS[provider]['display']} auth failed: HTTP {status}: {body}")
    if not isinstance(body, dict):
        raise SystemExit(f"Unexpected {PROVIDERS[provider]['display']} user response: {body}")
    login = body.get("login") or body.get("username") or body.get("name")
    if not login:
        raise SystemExit(f"Cannot detect {PROVIDERS[provider]['display']} username from response: {body}")
    return str(login)


def repo_exists_or_create(provider: str, token: str, owner: str, repo_name: str, private: bool = True, create: bool = True) -> str:
    meta = PROVIDERS[provider]
    if not create:
        return f"{meta['web_base']}/{owner}/{repo_name}"
    if provider == "github":
        payload = {"name": repo_name, "private": private, "auto_init": False}
        status, body = api_json(provider, "POST", "/user/repos", token, payload)
        if status in (200, 201):
            return str((body if isinstance(body, dict) else {}).get("html_url") or f"{meta['web_base']}/{owner}/{repo_name}")
        if status == 422:
            return f"{meta['web_base']}/{owner}/{repo_name} (already exists or cannot create; continuing)"
        raise SystemExit(f"Failed to create GitHub repo: HTTP {status}: {body}")
    payload = {"name": repo_name, "private": "true" if private else "false", "auto_init": "false"}
    status, body = api_json(provider, "POST", "/user/repos", token, payload)
    if status in (200, 201):
        if isinstance(body, dict):
            return str(body.get("html_url") or body.get("human_name") or f"{meta['web_base']}/{owner}/{repo_name}")
        return f"{meta['web_base']}/{owner}/{repo_name}"
    if status in (400, 409, 422):
        return f"{meta['web_base']}/{owner}/{repo_name} (already exists or cannot create; continuing)"
    raise SystemExit(f"Failed to create Gitee repo: HTTP {status}: {body}")


def remote_url(provider: str, owner: str, repo_name: str, method: str = "https") -> str:
    host = PROVIDERS[provider]["git_host"]
    if method == "ssh":
        return f"git@{host}:{owner}/{repo_name}.git"
    scheme_host = f"https://{host}"
    return f"{scheme_host}/{owner}/{repo_name}.git"


def auth_git_prefix(repo: Path) -> list[str]:
    cfg = load_config(repo)
    sync = cfg.get("sync") or {}
    provider = sync.get("provider")
    method = sync.get("auth_method", "token")
    remote = sync.get("remote") or ""
    if provider not in PROVIDERS or method not in {"token", "oauth"} or not str(remote).startswith("https://"):
        return []
    token = get_token(repo, provider, require=False)
    if not token:
        return []
    account = sync.get("account") or ((load_secrets(repo).get("sync") or {}).get(provider) or {}).get("account") or "x-access-token"
    if provider == "github":
        raw = f"x-access-token:{token}".encode("utf-8")
    else:
        raw = f"{account}:{token}".encode("utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    return ["-c", f"http.extraHeader=Authorization: Basic {encoded}"]


def run_git_auth(repo: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return run_git(repo, [*auth_git_prefix(repo), *args], check=check)



def form_post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any] | str]:
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req_headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded", "User-Agent": "MemHub/0.1"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=data, method="POST", headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return resp.status, {}
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def open_or_print_url(url: str, no_browser: bool = False) -> None:
    print(f"Open this URL in your browser:\n{url}\n", file=sys.stderr)
    if not no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass


def github_device_flow(client_id: str, scope: str = "repo", no_browser: bool = False) -> str:
    meta = PROVIDERS["github"]
    status, body = form_post_json(meta["oauth_device_code_url"], {"client_id": client_id, "scope": scope})
    if status >= 400 or not isinstance(body, dict):
        raise SystemExit(f"GitHub device flow failed: HTTP {status}: {body}")
    device_code = body.get("device_code")
    user_code = body.get("user_code")
    verification_uri = body.get("verification_uri") or body.get("verification_uri_complete")
    interval = int(body.get("interval") or 5)
    if not device_code or not user_code or not verification_uri:
        raise SystemExit(f"Invalid GitHub device response: {body}")
    print("GitHub authorization required.", file=sys.stderr)
    print(f"User code: {user_code}", file=sys.stderr)
    open_or_print_url(str(verification_uri), no_browser=no_browser)
    while True:
        time.sleep(interval)
        status, token_body = form_post_json(
            meta["oauth_access_token_url"],
            {
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        if status >= 400 or not isinstance(token_body, dict):
            raise SystemExit(f"GitHub token exchange failed: HTTP {status}: {token_body}")
        if token_body.get("access_token"):
            return str(token_body["access_token"])
        error = token_body.get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval += 5
            continue
        raise SystemExit(f"GitHub authorization failed: {token_body}")


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    server_version = "MemHubOAuth/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        self.server.oauth_code = (params.get("code") or [None])[0]  # type: ignore[attr-defined]
        self.server.oauth_error = (params.get("error") or [None])[0]  # type: ignore[attr-defined]
        if self.server.oauth_code:  # type: ignore[attr-defined]
            body = "MemHub authorization complete. You can close this tab."
        else:
            body = "MemHub authorization failed. You can close this tab."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def wait_for_local_oauth_code(port: int, timeout: int = 180) -> tuple[str | None, str]:
    server = http.server.HTTPServer(("127.0.0.1", port), OAuthCallbackHandler)
    server.oauth_code = None  # type: ignore[attr-defined]
    server.oauth_error = None  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    code = getattr(server, "oauth_code", None)
    error = getattr(server, "oauth_error", None)
    server.server_close()
    return code, error or ""


def gitee_oauth_flow(client_id: str, client_secret: str, redirect_uri: str, scope: str = "user_info projects", no_browser: bool = False, callback_port: int = 8765, manual_code: str | None = None) -> str:
    meta = PROVIDERS["gitee"]
    if not redirect_uri:
        redirect_uri = f"http://127.0.0.1:{callback_port}/callback"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
    }
    authorize_url = meta["oauth_authorize_url"] + "?" + urllib.parse.urlencode(params)
    code = manual_code
    if not code:
        open_or_print_url(authorize_url, no_browser=no_browser)
        if redirect_uri.startswith("http://127.0.0.1") or redirect_uri.startswith("http://localhost"):
            print(f"Waiting for OAuth callback on {redirect_uri} ...", file=sys.stderr)
            code, err = wait_for_local_oauth_code(callback_port)
            if err:
                raise SystemExit(f"Gitee authorization failed: {err}")
        if not code:
            if sys.stdin.isatty():
                code = input("Paste Gitee authorization code: ").strip()
            else:
                raise SystemExit("No Gitee authorization code received. Re-run with --manual-code or use an interactive terminal.")
    status, body = form_post_json(
        meta["oauth_access_token_url"],
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "client_secret": client_secret,
        },
    )
    if status >= 400 or not isinstance(body, dict) or not body.get("access_token"):
        raise SystemExit(f"Gitee token exchange failed: HTTP {status}: {body}")
    return str(body["access_token"])


def oauth_token(
    provider: str,
    client_id: str | None = None,
    client_secret: str | None = None,
    scope: str | None = None,
    redirect_uri: str | None = None,
    callback_port: int = 8765,
    no_browser: bool = False,
    manual_code: str | None = None,
) -> str:
    meta = PROVIDERS[provider]
    client_id = client_id or os.environ.get(meta.get("env_client_id", ""))
    if not client_id:
        raise SystemExit(f"Missing {meta['display']} OAuth client id. Pass --client-id or set {meta.get('env_client_id', '')}.")
    if provider == "github":
        return github_device_flow(client_id, scope=scope or "repo", no_browser=no_browser)
    client_secret = client_secret or os.environ.get(meta.get("env_client_secret", ""))
    if not client_secret:
        raise SystemExit(f"Missing Gitee OAuth client secret. Pass --client-secret or set {meta.get('env_client_secret', '')}.")
    return gitee_oauth_flow(
        client_id,
        client_secret,
        redirect_uri=redirect_uri or f"http://127.0.0.1:{callback_port}/callback",
        scope=scope or "user_info projects",
        no_browser=no_browser,
        callback_port=callback_port,
        manual_code=manual_code,
    )

def setup_git_sync(
    repo: Path,
    provider: str,
    repo_name: str,
    owner: str | None = None,
    token: str | None = None,
    branch: str = "main",
    private: bool = True,
    create_repo: bool = True,
    auth_method: str = "token",
    remote_method: str = "https",
    client_id: str | None = None,
    client_secret: str | None = None,
    scope: str | None = None,
    redirect_uri: str | None = None,
    callback_port: int = 8765,
    no_browser: bool = False,
    manual_code: str | None = None,
) -> str:
    ensure_repo(repo)
    if provider not in PROVIDERS:
        raise SystemExit(f"Unsupported provider: {provider}. Choose: {', '.join(PROVIDERS)}")
    if auth_method == "ssh" and remote_method != "ssh":
        raise SystemExit("--auth ssh requires --remote-method ssh")
    if auth_method in {"token", "oauth"} and remote_method != "https":
        raise SystemExit("--auth token/oauth requires --remote-method https")
    if auth_method in {"token", "oauth"}:
        if auth_method == "oauth":
            token = oauth_token(
                provider,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope,
                redirect_uri=redirect_uri,
                callback_port=callback_port,
                no_browser=no_browser,
                manual_code=manual_code,
            )
        else:
            token = get_token(repo, provider, explicit_token=token, require=False)
            if not token:
                if sys.stdin.isatty():
                    token = getpass.getpass(f"{PROVIDERS[provider]['display']} token: ")
                else:
                    raise SystemExit(f"Token required. Use --token or set {PROVIDERS[provider]['env_token']}.")
        account = provider_user(provider, token)
        owner = owner or account
        store_token(repo, provider, token, account=account)
    else:
        token = None
        account = owner or ""
        if not owner:
            raise SystemExit("--owner is required when --auth ssh is used")

    owner = owner or account
    web_url = repo_exists_or_create(provider, token, owner, repo_name, private=private, create=create_repo) if token else f"{PROVIDERS[provider]['web_base']}/{owner}/{repo_name}"
    remote = remote_url(provider, owner, repo_name, method=remote_method)
    run_git(repo, ["remote", "remove", "origin"], check=False)
    run_git(repo, ["remote", "add", "origin", remote], check=False)
    run_git(repo, ["branch", "-M", branch], check=False)

    cfg = load_config(repo)
    sync_cfg = cfg.setdefault("sync", {})
    sync_cfg.update({
        "backend": "git",
        "type": "git",
        "provider": provider,
        "remote": remote,
        "repo": f"{owner}/{repo_name}",
        "branch": branch,
        "auth_method": auth_method,
        "remote_method": remote_method,
        "auto_pull": True,
        "auto_push": True,
        "pull_strategy": "rebase",
        "commit_prefix": "memhub:",
        "updated_at": now_iso(),
    })
    if account:
        sync_cfg["account"] = account
    save_config(repo, cfg)
    commit_all(repo, f"memhub: configure {provider} sync")
    if auth_method == "oauth":
        credential_line = "OAuth token is stored locally in .memhub/secrets.yaml and ignored by git."
    elif auth_method == "token":
        credential_line = "Token is stored locally in .memhub/secrets.yaml and ignored by git."
    else:
        credential_line = "SSH auth selected; no token stored by MemHub."
    return "\n".join([
        f"Connected {PROVIDERS[provider]['display']} sync.",
        f"Account: {account or owner}",
        f"Repository: {owner}/{repo_name}",
        f"Remote: {remote}",
        f"Repo page: {web_url}",
        credential_line,
    ]) + "\n"


def sync_status(repo: Path) -> str:
    cfg = load_config(repo)
    sync = cfg.get("sync") or {}
    lines = ["MemHub sync status:"]
    lines.append(f"- backend: {sync.get('backend') or sync.get('type') or 'git'}")
    lines.append(f"- provider: {sync.get('provider') or 'custom'}")
    lines.append(f"- repo: {sync.get('repo') or ''}")
    lines.append(f"- branch: {sync.get('branch') or 'main'}")
    lines.append(f"- remote: {sync.get('remote') or run_git(repo, ['remote', 'get-url', 'origin'], check=False).stdout.strip()}")
    token_state = "not needed"
    provider = sync.get("provider")
    if provider in PROVIDERS and sync.get("auth_method") in {"token", "oauth"}:
        token_state = "available" if get_token(repo, provider, require=False) else "missing"
    lines.append(f"- credential: {token_state}")
    lines.append(run_git(repo, ["status", "--short", "--branch"], check=False).stdout.strip())
    return "\n".join(lines).strip() + "\n"

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
    cfg = load_config(repo)
    sync = cfg.get("sync") or {}
    branch = sync.get("branch") or "main"
    remote_names = run_git(repo, ["remote"], check=False).stdout.strip()
    outputs = []
    if remote_names:
        # Commit local changes, pull remote updates, then commit sync state and push everything.
        commit_all(repo, "memhub: sync local changes")
        pull = run_git_auth(repo, ["pull", "--rebase", "origin", branch], check=False)
        outputs.append(pull.stdout + pull.stderr)
        state = read_yaml(repo / ".memhub/state.yaml", {})
        state["last_sync_at"] = now_iso()
        write_yaml(repo / ".memhub/state.yaml", state)
        commit_all(repo, "memhub: update sync state")
        push = run_git_auth(repo, ["push", "-u", "origin", f"HEAD:{branch}"], check=False)
        outputs.append(push.stdout + push.stderr)
    else:
        outputs.append("No git remote configured; local repository only. Run `memhub sync setup github` or `memhub sync setup gitee`.\n")
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

    p_sync = sub.add_parser("sync", help="Configure or run GitHub/Gitee sync")
    sync_sub = p_sync.add_subparsers(dest="sync_cmd")
    p_sync_setup = sync_sub.add_parser("setup", help="Set up hosted Git sync")
    p_sync_setup.add_argument("provider", choices=["github", "gitee"])
    p_sync_setup.add_argument("--repo-name", default="mymemhub", help="Remote repository name")
    p_sync_setup.add_argument("--owner", default=None, help="Owner/login. Defaults to authenticated account")
    p_sync_setup.add_argument("--token", default=None, help="Provider token. Prefer env vars MEMHUB_GITHUB_TOKEN/MEMHUB_GITEE_TOKEN")
    p_sync_setup.add_argument("--branch", default="main")
    p_sync_setup.add_argument("--public", action="store_true", help="Create public repo instead of private")
    p_sync_setup.add_argument("--no-create", action="store_true", help="Do not call provider API to create repo")
    p_sync_setup.add_argument("--auth", default="oauth", choices=["oauth", "token", "ssh"], help="Git auth mode. OAuth uses GitHub Device Flow or Gitee authorization-code flow")
    p_sync_setup.add_argument("--remote-method", default="https", choices=["https", "ssh"], help="Remote URL style")
    p_sync_setup.add_argument("--client-id", default=None, help="OAuth client id. Or set MEMHUB_GITHUB_CLIENT_ID / MEMHUB_GITEE_CLIENT_ID")
    p_sync_setup.add_argument("--client-secret", default=None, help="Gitee OAuth client secret. Or set MEMHUB_GITEE_CLIENT_SECRET")
    p_sync_setup.add_argument("--scope", default=None, help="OAuth scope. Defaults: GitHub repo; Gitee user_info projects")
    p_sync_setup.add_argument("--redirect-uri", default=None, help="Gitee OAuth redirect URI. Defaults to local callback")
    p_sync_setup.add_argument("--callback-port", type=int, default=8765, help="Local callback port for Gitee OAuth")
    p_sync_setup.add_argument("--no-browser", action="store_true", help="Print OAuth URL/code but do not try to open browser")
    p_sync_setup.add_argument("--manual-code", default=None, help="Gitee OAuth authorization code for manual callback flow")
    sync_sub.add_parser("status", help="Show sync config/status")

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
        if getattr(args, "sync_cmd", None) == "setup":
            print(setup_git_sync(
                repo,
                provider=args.provider,
                repo_name=args.repo_name,
                owner=args.owner,
                token=args.token,
                branch=args.branch,
                private=not args.public,
                create_repo=not args.no_create,
                auth_method=args.auth,
                remote_method=args.remote_method,
                client_id=args.client_id,
                client_secret=args.client_secret,
                scope=args.scope,
                redirect_uri=args.redirect_uri,
                callback_port=args.callback_port,
                no_browser=args.no_browser,
                manual_code=args.manual_code,
            ), end="")
        elif getattr(args, "sync_cmd", None) == "status":
            print(sync_status(repo), end="")
        else:
            print(sync_repo(repo), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
