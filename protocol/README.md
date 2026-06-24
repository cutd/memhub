# MemHub Protocol v0.1

> Status: Draft · Schema version: `0.1`
>
> MemHub is not an Obsidian replacement. It defines how AI agents should know a
> user through a **Git-first, file-native, serverless** memory repository.

This document is the normative specification for a MemHub Repository: its
directory contract, file schemas, the two-tier memory model, promotion routing,
and sync/credential conventions. The reference implementation lives in
`skills/memhub/scripts/memhub.py` (re-exported by `memhub_cli`).

The key words MUST, SHOULD, and MAY follow RFC 2119.

---

## 1. Principles

1. **Local-first / Git-first.** The YAML/Markdown files in the repository are the
   single source of truth. A hosted Git remote (GitHub/Gitee) is only a sync
   backend; it is never authoritative. Agents MUST be able to operate from the
   local checkout when the remote is unreachable.
2. **Human-auditable.** Every memory is a plain-text entry with provenance.
   Anyone can read, diff, and edit the repository by hand.
3. **Two-tier writes (inbox optional).** MemHub defines two write paths. A
   direct write lands canonical memory immediately and is the default for an
   explicit `remember`. The inbox tier (`inbox/`) is an optional audit buffer
   for low-confidence or batch captures that an agent wants a human to review
   before promotion. Implementations MUST support both; which is the default
   for a given client is a policy choice (the reference CLI direct-writes by
   default, `--inbox` opts into the buffer).
4. **Provenance required.** Every entry carries a `source`, so it is traceable
   to the client/agent that produced it.
5. **Storage, not judgment.** MemHub stores and syncs. The intelligence
   (what to remember, when to promote, conflict resolution) is the agent's job.

---

## 2. Repository layout

A MemHub Repository is a Git repository with this contract:

```
<repo>/
├── .memhub/
│   ├── config.yaml          # repo identity + sync/context/inbox config
│   ├── schema.yaml          # { schema_version, protocol: MemHub }
│   ├── state.yaml           # { schema_version, last_sync_at }
│   ├── templates/           # optional export templates (e.g. context-pack.md.j2)
│   ├── cache/  indexes/     # local-only, git-ignored
│   └── secrets.yaml         # local-only, git-ignored, chmod 600
├── identity/                # who the user is
│   ├── profile.yaml
│   ├── preferences.yaml
│   ├── conventions.yaml
│   └── constraints.yaml
├── projects/                # what the user is working on
│   ├── _active.yaml         # active project list + default project
│   └── <project_id>/
│       ├── context.yaml
│       ├── decisions.yaml
│       ├── tasks.yaml
│       ├── stack.yaml
│       ├── history.yaml
│       └── notes.md
├── knowledge/               # reusable knowledge
│   ├── index.yaml
│   ├── product.yaml
│   └── tech.yaml
├── relations/               # people / orgs / tools
│   ├── people.yaml
│   ├── orgs.yaml
│   └── tools.yaml
├── timeline/                # YYYY-MM.yaml monthly facts/events
├── inbox/                   # capture buffer, one file per capture
├── exports/                 # generated context for external chatbots
└── archive/                 # retired memory (optional)
```

Implementations MUST tolerate missing optional files (treat as empty) and MUST
NOT crash when a directory is absent.

### 2.1 What is committed vs. ignored

Committed: all canonical files, `inbox/`, `exports/`, `.memhub/config.yaml`,
`.memhub/schema.yaml`, `.memhub/state.yaml`, `.gitattributes`.

Git-ignored (MUST): `.memhub/secrets.yaml`, `.memhub/secrets/`,
`.memhub/cache/`, `.memhub/indexes/`, `*.db`, `.DS_Store`.

Secrets MUST never be committed. Tokens, OAuth client secrets, and authorization
codes MUST never appear in committed files or in agent-visible output.

---

## 3. Common conventions

- **`schema_version`** — every file SHOULD carry `schema_version: '0.1'`.
- **Timestamps** — ISO-8601 with offset, second precision
  (e.g. `2026-05-20T17:31:53+08:00`).
- **`updated_at`** — collection files SHOULD update this when their list changes.
- **Encoding** — UTF-8. Non-ASCII content (e.g. Chinese) is expected and MUST be
  preserved (`allow_unicode`).

### 3.1 Canonical memory entry

Most canonical lists hold entries with this shape:

```yaml
- id: mem_<YYYYmmdd_HHMMSS>_<rand6>
  type: decision | preference | constraint | convention | knowledge | fact | event | relation
  status: active            # active | archived | superseded
  content: "<human-readable statement>"
  confidence: 0.0 - 1.0
  importance: 0.0 - 1.0
  source: { client: <agent-name> }
  created_at: <iso8601>
  promoted_at: <iso8601>    # set when promoted from inbox
  inbox_ref: <inbox filename>   # provenance back to the capture
```

`content` is the primary rendered field. Implementations SHOULD fall back to
`key: value`, `name`, `title`, or `description` when `content` is absent, so
hand-authored entries still render.

---

## 4. File schemas

### 4.1 `.memhub/config.yaml`

```yaml
schema_version: '0.1'
repo:
  id: user_main_memhub
  owner: <name>
sync:
  type: git
  backend: git
  provider: github | gitee | null
  remote: <url> | null
  repo: <owner>/<name>
  branch: main
  auth_method: oauth | token | ssh
  remote_method: https | ssh
  account: <login>
  auto_pull: true
  auto_push: true
  push_throttle_seconds: 3600
  pull_throttle_seconds: 3600
  pull_strategy: rebase
  commit_prefix: 'memhub:'
inbox:
  auto_archive: false
  auto_archive_confidence_threshold: 0.92
context:
  default_pack: standard
  standard_token_budget: 2000
```

### 4.2 `identity/profile.yaml`

```yaml
profile:
  id, name, display_name, language, timezone, role, company, bio, tags
communication:
  default_language, preferred_style, verbosity, likes[], dislikes[]
```

### 4.3 `identity/preferences.yaml` · `constraints.yaml` · `conventions.yaml`

Each is a collection: `{ schema_version, updated_at, <preferences|constraints|conventions>: [entry] }`.
Entries follow §3.1; preferences additionally MAY carry `category`, `key`, `value`.

### 4.4 `projects/_active.yaml`

```yaml
active_projects:
- id, name, priority, status, default: bool, path, description
```

Exactly one project SHOULD be marked `default: true`; it is the project used by
context packs when none is specified.

### 4.5 `projects/<id>/context.yaml`

```yaml
project:
  id, name, status, description, goals[], constraints[], current_phase, updated_at
```

`decisions.yaml`, `tasks.yaml`, `stack.yaml`, `history.yaml` are collections
keyed by `decisions` / `tasks` / `stack` / `events`. Tasks with status `done`
or `cancelled` are treated as closed and excluded from context packs.

### 4.6 `knowledge/*.yaml`

`{ domain: <name>, items: [entry] }`. `index.yaml` holds `{ domains: [] }`.

### 4.7 `relations/{people,orgs,tools}.yaml`

`{ <people|orgs|tools>: [entry] }`. Entries MAY use relation-specific fields
(`name`, `role`, `relation`, `note`) and/or the generic `content`.

### 4.8 `timeline/YYYY-MM.yaml`

`{ month: YYYY-MM, events: [entry] }`. Events carry a `date` (YYYY-MM-DD).

---

## 5. Inbox (capture tier, optional)

The inbox is an **optional** audit buffer. Agents MAY capture low-confidence or
batch items here for human review instead of direct-writing canonical memory.
Every capture is one file: `inbox/<YYYYmmdd-HHMMSS>-<client>-<rand6>.yaml`.

```yaml
schema_version: '0.1'
inbox_id: inbox_<YYYYmmdd_HHMMSS>_<rand6>
status: pending            # pending | promoted
created_at: <iso8601>
source: { client: <agent-name> }
items:
- id: mem_<...>
  type: <see §3.1>
  scope: project | inbox
  status: pending          # pending | accepted | promoted
  content: "<statement>"
  suggested_target: <repo-relative path> | null
  confidence: 0.0 - 1.0
  importance: 0.0 - 1.0
  created_at: <iso8601>
```

An inbox file MAY contain multiple `items`. A file is marked `promoted` only
when all of its items are promoted.

---

## 6. Writing canonical memory

There are two ways an entry reaches a canonical file.

**Direct write** (default for `remember`): the entry is routed by `type`
(§6.1), deduped (§6.2), and appended immediately, with a local commit. No inbox
file is created; `inbox_ref`/`promoted_at` are omitted.

**Promotion** from the inbox tier is **explicit and two-phase**: a dry-run
preview, then `--apply`. Implementations MUST default to preview and only write
on explicit apply. Both paths share the same routing and dedup rules below.

### 6.1 Routing

If an item has `suggested_target`, it wins. Otherwise route by `type`:

| `type`       | Target |
|--------------|--------|
| `decision`   | `projects/<project>/decisions.yaml` (project from `suggested_target`, else default project) |
| `preference` | `identity/preferences.yaml` |
| `constraint` | `identity/constraints.yaml` |
| `convention` | `identity/conventions.yaml` |
| `knowledge`  | `knowledge/product.yaml` |
| `relation`   | `relations/people.yaml` |
| `fact`, `event` | `timeline/YYYY-MM.yaml` (current month) |
| _(other)_    | `knowledge/product.yaml` |

### 6.2 Apply semantics

- New entries are prepended (most recent first).
- **Dedup**: an entry is skipped if its `content`, after whitespace collapse and
  case-folding, matches an existing entry in the same list.
- On apply, the inbox item's `status` becomes `promoted` and gains
  `promoted_at` and `promoted_to`. The canonical entry records `inbox_ref`.

Auto-promotion (without human review) is OPTIONAL and gated by
`inbox.auto_archive` + `auto_archive_confidence_threshold`. The reference CLI
keeps it off.

---

## 7. Context packs

A context pack is generated Markdown injected into a downstream chatbot. Packs
are derived views over canonical memory; they are not authoritative and MUST be
labeled as user-auditable, not absolute truth.

| Pack | Purpose | Includes |
|------|---------|----------|
| `brief` | Minimal injection | user, top preferences, current project + top decisions |
| `standard` | Default | brief + constraints, conventions, open tasks |
| `project` | One project deep | standard, decision/task-heavy for the selected project |
| `full` | Everything | standard + knowledge, relations, recent timeline |

Each section is independently capped per pack. Exports MAY be customized via
`.memhub/templates/context-pack.md.j2` using `{{ name }}`-style placeholders
(`name`, `role`, `style`, `project_context`, `recent_decisions`); when present
the template is used for `export chatbot`, otherwise the built-in renderer.

---

## 8. Sync

Sync is plain Git. The reference flow (`memhub sync`):

1. Commit local changes (`memhub: sync local changes`).
2. If the remote branch exists, `git pull --rebase origin <branch>`.
3. On rebase conflict: **abort the rebase**, leave the working tree clean, do
   **not** push, and report the conflicting state to the user. Implementations
   MUST NOT push a half-resolved or mid-rebase state, and MUST NOT delete local
   inbox, canonical files, or `.git` history on failure.
4. Update `.memhub/state.yaml.last_sync_at`, commit sync state.
5. `git push origin HEAD:<branch>`.

A brand-new remote with no branch yet skips the pull and pushes directly.

### 8.0 Automatic, throttled sync

A manual `sync` runs the flow above immediately. In addition, when a remote is
configured, implementations SHOULD sync automatically so any agent with the
skill installed stays in sync without explicit calls:

- **After a write** (`remember`, `forget --apply`, `promote --apply`): attempt a
  push, throttled by `sync.push_throttle_seconds` (default 3600). Within the
  window the write is committed locally only; the push happens on a later write
  or an explicit `sync`. Local memory is therefore never lost, and the remote is
  not spammed with per-write pushes.
- **Before a read** (`context`): attempt a `pull --rebase`, throttled by
  `sync.pull_throttle_seconds` (default 3600). On failure, fall back to local
  memory and warn that context may be stale.

Auto behavior is gated by `sync.auto_push` / `sync.auto_pull` (default true). The
throttle timestamps live in `.memhub/cache/sync.yaml`, which is **git-ignored and
per-machine** — sync cadence is a local concern and committing it would create
cross-device merge churn. An explicit `sync` always ignores the throttle.

### 8.1 Structured merge driver

Canonical files are append-mostly YAML lists, so two devices that each append
memory would otherwise hit a line-level conflict. MemHub commits a
`.gitattributes` that routes canonical list files through a `merge=memhub`
driver. The driver performs a three-way merge that **unions the known entry
lists** (preferences, constraints, conventions, decisions, tasks, stack, items,
events, people, orgs, tools, active_projects), deduping by entry `id` (falling
back to normalized content), and prefers the newer side for the `updated_at`
bookkeeping scalar. On any parse failure it falls back to a normal conflict so
memory is never silently lost.

Git local config is not cloned, so the driver command must be registered once
per machine (`git config merge.memhub.driver ...`). Implementations SHOULD do
this idempotently on `init` and at the start of every `sync`.

### 8.2 Credentials

Three auth methods:

- **oauth** (default) — GitHub Device Flow (embedded public client id) or Gitee
  Authorization Code via a MemHub OAuth Broker (client_secret stays server-side)
  or developer direct mode. Tokens stored in `.memhub/secrets.yaml`.
- **token** — personal access token, stored in `.memhub/secrets.yaml`.
- **ssh** — SSH remote; MemHub stores no credential.

For HTTPS + token/oauth, the token is injected per-command via
`http.extraHeader: Authorization: Basic <base64(user:token)>` rather than being
written into the remote URL. Credentials MUST NOT be echoed in output.

`sync setup` mutates remotes and triggers authorization; it MUST run only on
explicit user request.

---

## 9. Agent behavior contract (informative)

- **Before reading**: just read `context` — it auto-pulls (throttled) when a
  remote is configured. If the pull fails, it falls back to local memory and
  warns that context may be stale. Run an explicit `sync` first only when you
  need a guaranteed-fresh read.
- **During**: when a stable decision/preference/fact forms, `remember` it
  (direct write by default; `--inbox` to buffer for review). The write
  auto-pushes, throttled; no explicit `sync` is needed per write.
- **Recall / curate**: `search <query>` matches canonical entries by content,
  type, or project. `forget <query>` soft-archives entries (sets
  `status: archived`) so they drop out of context packs but stay auditable and
  reversible in Git history. To correct a memory, `forget` the stale entry and
  `remember` the new one.
- **Archiving**: `promote --dry-run`, confirm, then `promote --apply`. Do not
  promote chit-chat, unconfirmed guesses, or sensitive data without explicit
  consent.
- **At end of session**: run an explicit `sync` to flush any writes still held
  by the push throttle.
- **Never** echo tokens, secrets, or authorization codes.

The normative agent-facing rules live in `skills/memhub/SKILL.md`.

---

## 10. Versioning

This is `schema_version: '0.1'`. Breaking changes to the directory contract or
entry shape bump the schema version; `.memhub/schema.yaml` records the version a
repository was written against.
