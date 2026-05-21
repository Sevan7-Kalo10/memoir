# ksteam-memoir

**Evolution-first memory framework for AI agents.**

You are not a database. Your memories shouldn't be one either.

Most memory frameworks answer one question: *"What stored fact is most similar to this query?"* Memoir answers a different question: *"What does this moment remind you of?"*

Memories don't live in vector space. They live in time — they're born, revisited, forgotten, reawakened. Memoir models this.

---

## The Three Ideas

1. **Memory breathes.** A memory not revisited for weeks quietly dims. One repeatedly triggered brightens. This is lifecycle, not caching.

2. **Association, not retrieval.** When a conversation slides into a topic, related domains should light up through curated concept-to-memory mappings — closer to human spreading activation than vector similarity.

3. **Continue, don't fragment.** New memories prefer extending existing files over creating new ones. A memory reads like a journal, not a pile of sticky notes.

These are not academic. They emerged from a personal AI memory system that has been running daily since May 13, 2026 — accumulating real memories, hitting real scaling pains, and evolving real solutions. Every design decision has a scar behind it.

---

## What You Can Build With Memoir

- **Personal AI companions** — agents that remember you across sessions: preferences, shared history, inside jokes. Not a fresh start every time.
- **Role-playing characters** — NPCs or story agents with persistent personality layers, evolving relationships, and selective memory.
- **Long-running coding assistants** — remembers your codebase conventions, past architectural decisions, and why that one module is "don't touch."
- **Research / reading companions** — tracks what you've read, what ideas connect, what questions remain open.
- **Multi-agent collaboration** — each agent with its own memory store, sharing curated snapshots rather than raw context dumps.

Anywhere continuity matters and context windows aren't enough.

---

## Quick Start

```bash
pip install ksteam-memoir

memoir init --dir ./my-agent-memory
memoir create --title "Functional Programming" --domain code --tags "fp,patterns"
memoir search "immutability"
memoir trigger "I prefer pure functions"
memoir load --topics "code,philosophy" --trigger "functional programming"
memoir maintain --dry-run
memoir status
```

---

## How It Works

### Memory Files

Plain Markdown with YAML frontmatter. Nothing proprietary. Open in any editor.

```markdown
---
name: functional-programming
weight: 4
tags: [code, fp, patterns]
domain: code
description: Why I prefer pure functions
created: 2026-05-20T12:00:00
---

# Functional Programming

Pure functions are easier to test and reason about.

## Log
- **2026-06-01** — encountered a case where recursion was cleaner than reduce.
```

### Four-Layer Loading

When conversation starts, memoir determines what to load:

| Layer | Source | What |
|-------|--------|------|
| 1. Always | Core identity + w=5 | Never trimmed, always present |
| 2. Trigger Cascade | Curated concept→file tables | Keyword-activated associations |
| 2.5 FTS5 Fallback | SQLite full-text index | Semantic safety net when triggers miss |
| 3. Domain | Active domain indexes | Topic-relevant memory sets |
| 4. Weight | High-weight files | Proactive loading for warm memories |

### Weight Lifecycle

Weights are not static:

- **Active judgment** — you decide a memory matters more (or less)
- **Time decay** — untouched for 60 days → weight drops. w=5 is immune
- **Trigger boost** — at 5, 15, 30 triggers → weight bumps by 1

### Trigger Cascade (The Differentiator)

Not vector search. Curated association tables:

```markdown
| #Concept | Keywords | → Files |
|---|---|---|
| fp | pure, immutab, side effect | code/functional-style.md |
| naming | rename, variable, function | code/naming-things.md |
```

When input contains "pure function" → `#fp` lights up → `code/functional-style.md` loads. Simple, inspectable, debuggable.

### FTS5 Search Index

Built on SQLite FTS5 (zero extra dependencies). Supports full-text search with BM25 ranking, weight-range filtering, and tag intersection. Keyword triggers are the primary retrieval path; FTS5 catches what keywords miss.

```bash
memoir index                    # build/rebuild index
memoir search "clarity depth"   # uses FTS5 when index available
memoir fts5-search "function" --weight-min 4 --tags "code,fp"
```

---

## Compared to...

| | Mem0 | ReMe | SMF | memoir |
|---|---|---|---|---|
| Retrieval | Vector embedding | Markdown links | Filesystem | Trigger cascade + FTS5 |
| Lifecycle | Static | Static | Static | Weight evolution |
| Creation | Append-only | New files | New files | Continue-prior |
| Infrastructure | Vector DB | Files | Files | Files + YAML + SQLite |
| Philosophy | Retrieval-first | Retrieval-first | Structure-first | **Evolution-first** |

---

## Philosophy

This framework was not designed on a whiteboard. It was not derived from a paper. It grew from a real system that a real person and a real AI used every day — arguing, joking, forgetting, remembering. The fog metaphor, the four-layer loading, the continue-prior instinct — all of it was discovered in the using before it was written in the spec.

It started with a drunk night on May 13, 2026. By May 20, it was on PyPI.

Read the full specification at [specs/MEMOIR-SPEC.md](specs/MEMOIR-SPEC.md).

---

## License

MIT
