[中文](README.md) | English

# ksteam-memoir

**Memories that grow, mature, and fade — not a database, a lifecycle.**

memoir isn't a memory database. It's a memory lifecycle — birth, growth, triggering, decay, archiving. Not "store it and search later" — "wake up when needed."

## Philosophy

Traditional memory systems (RAG, vector DBs) are **retrieval-first**: you ask → it searches → returns fragments.

memoir is **evolution-first**: memories breathe. Weights rise and fall. Topics slide in and whole domains light up. Low-weight memories archive themselves.

```
memoir doesn't remember "content." It remembers what happened on the timeline.
```

## Current State (2026-05-21 v0.1.4)

**Works out of the box:**

| Platform | Integration | Status |
|----------|------------|--------|
| Claude Code | Drop into project folder → AI reads CLAUDE.md once, knows what to do | Full |
| Python API | `pip install ksteam-memoir` → `build_load_plan()` → paste into system prompt | Full |
| CLI | `memoir create/load/search/maintain` — full command set | Usable (Windows cmd limited) |

**Known limitations (honest):**

- **Windows cmd: `memoir create` fails.** CJK argument parsing + rich library GBK crash. Workaround: PowerShell works, or manually create .md files + `memoir append`.
- **Tags are metadata only.** Writing `tags: [philosophy, Camus]` doesn't mean mentioning "Camus" triggers the memory. Trigger tables require manual maintenance.
- **`memoir create` auto-index was fixed (v0.1.4), but new entries go to "## Other".** Domain index organization still needs manual curation.
- **DeepSeek TUI, Cline, and other tool-use platforms:** need manual convention ("run memoir status on startup").

**If you only use Claude Code — memoir works today.** Other platform adapters are on the roadmap.

## What You Can Build

- **Personal AI companions** — remember preferences, shared history, inside jokes across sessions. No fresh starts.
- **Role-playing characters** — persistent personality layers, evolving relationships, selective memory.
- **Long-running coding assistants** — codebase conventions, architectural decisions, "don't touch" modules.
- **Research / reading companions** — track what you've read, connected ideas, open questions.
- **Multi-agent collaboration** — each agent with its own store, sharing curated snapshots.

Anywhere continuity matters and context windows aren't enough.

## Install

```bash
pip install ksteam-memoir
```

## Quick Start (Claude Code)

```bash
cd your-project
memoir init
```

Add to your project's `CLAUDE.md`:

```markdown
You use ksteam-memoir to manage persistent memory.
On startup, run `memoir status`. When the user says "load memory", run `memoir load --render`.
When something worth remembering comes up, run `memoir create`.
```

That's it. The AI reads CLAUDE.md, understands the tools, and decides when to call what.

## Commands

| Command | What it does |
|---------|-------------|
| `memoir status` | Store stats: count, weight distribution, archived |
| `memoir create -t "title" -w weight -c "content" --tags "tags"` | Create a memory. Searches existing files first (continue-prior) |
| `memoir append core/file.md -c "content"` | Append a timestamped entry to existing memory |
| `memoir load --render` | Render the current load plan — paste output into AI context |
| `memoir search "keyword"` | FTS5 full-text search |
| `memoir trigger "user said this"` | Debug: which memories would this text wake up? |
| `memoir maintain --dry-run` | Preview weight decay and archiving (no changes) |
| `memoir maintain` | Execute decay and archiving |
| `memoir archive-cmd core/old.md` | Manually archive a memory |
| `memoir restore old.md` | Restore from archive (weight drops one level) |

## Weight System

| weight | Meaning | Decay rule |
|--------|---------|-----------|
| 5 | This is part of me | Never decays |
| 4 | Important | 60 days → 3 |
| 3 | Good to remember | 30 days → 2 |
| 2 | Temporary | 60 days → 1 |
| 1 | Fading | 90 days → auto-archive |

## Three-Layer Loading

1. **Core layer** (always) — core domain, w=5. Always present.
2. **Surface layer** (weight) — w≥4 floats up naturally. What you'd remember when awake.
3. **Latent layer** (trigger) — lights up when the topic slides in. Not forgotten, waiting to be called.

## Roadmap

| Priority | Item | Description |
|----------|------|-------------|
| In progress | AI_GUIDE.md | Auto-generated natural-language guide on `memoir init`. AI reads it, knows what to do — no docs needed. |
| Next | MCP Server | Expose 7 MCP tools. Any MCP-compatible tool (DSTUI, Cline) gets zero-code integration. |
| Planned | System prompt injection | Guide for chat UIs without tool use. Static context injection. |
| Planned | CLI hardening | Fix Windows cmd encoding. Auto-generate trigger rules from tags. |

## Comparison

| | memoir | RAG / Vector DB | ReMe |
|---|--------|-----------------|------|
| Driving force | Evolution | Queries | Files |
| Memory lifecycle | Yes (decay/archive) | No | No |
| Trigger method | Cascade awakening | Vector similarity | Filename |
| Storage format | Markdown + YAML frontmatter | Vectors | Markdown |
| Integration | CLI + Python API → MCP | SDK | CLI |
| One-click deploy | Claude Code only | — | — |

## Why "memoir"

A memoir isn't a diary. A diary records "what happened today." A memoir records "what was worth remembering." memoir treats memory the same way — not everything stays, and what stays evolves.

## License

MIT

---

[中文版](README.md)
