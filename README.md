# memoir v2

**Memory lifecycle management for Claude Code agents.**

memoir manages what Claude Code's built-in memory doesn't: hot/cold
layering, weight evolution, archiving, merging, and autonomous
self-maintenance across sessions.

Built-in memory answers "should I save this fact?" memoir answers "is this
fact still relevant? should it grow, fade, merge, or retire?"

## What went wrong with v0.1.x

v0.1.x (May 2026) was a Python package — `pip install ksteam-memoir`, CLI
commands, FTS5 search, 64 tests. It solved the right problem with the
wrong interface.

**The core mistake:** AI agents don't natively read Python code. They read
natural language. Asking an agent to learn CLI commands (`memoir create`,
`memoir load --render`) is asking it to operate in a foreign language. The
Python package was precise, testable, and well-architected — and it failed
at the one thing that mattered: the agent couldn't use it without being
explicitly trained.

The roadmap from May 2022 confirms this blind spot. v0.1.x's top priority
was "MCP Server + AI_GUIDE.md" — two separate efforts to build a natural
language interface ON TOP of the Python package. We were bolting a second
door onto a house because the first one faced the wrong direction.

## Why a Claude Code skill

A skill IS its natural language interface. The SKILL.md body is the
operational manual — the agent reads it and knows what to do. No CLI to
memorize, no Python to import, no MCP server to configure.

The three-level progressive disclosure mirrors how memory actually works:
- **Level 1** (description, always in context): what triggers the skill
- **Level 2** (SKILL.md body, loaded on trigger): the core model and
  workflows
- **Level 3** (references/, loaded on demand): detailed specs for specific
  tasks

This is what v0.1.x was reaching for with "AI_GUIDE.md" — but as a
first-class architecture, not a documentation afterthought.

## What memoir actually does

### Hot/cold layering

memoir splits memory into two layers based on one question: **will this
still matter in six months?**

- **Hot layer** (`HOT-MEMORY.md`, ~2000 tokens): self-maintaining narrative
  of recent events, active projects, and current behavioral rules. Updated
  at session close. Answers "what do I need to know when I wake up?"
- **Cold layer** (`memory/*.md`): permanent insights about the user —
  identity, values, preferences, behavioral patterns. Judgment-driven: the
  criterion is not "did we discuss this?" but "does this reveal something
  about who they ARE?"

### Two-axis evaluation (importance × recency)

v0.1.x used a single `weight` (1-5) that conflated importance and recency.
A core identity memory untouched for 60 days and a trivial fact accessed 5
minutes ago could both score w=4 — a false equivalence. memoir v2 splits
them:

- **importance** (1-5): how crucial is this to identity, behavior, or
  decision-making?
- **recency** (timestamp): when was this last accessed or reinforced?

### Lifecycle state machine

```
seedling → active → stable → fading → archived
               ↑                      |
               |______ restore _______|
```

Memories aren't static files. They grow, mature, fade, and eventually
retire to the archive. memoir provides the state machine and transition
rules — the agent proposes, the user confirms.

### Ingestion discipline

The session-close workflow is memoir's engine: (1) update hot memory, (2)
scan conversation for permanent insights with a sharp filter ("will this
still matter in 6 months?" AND "does this reveal who they ARE?"), (3) run
maintenance (decay, merge proposals, archive candidates), (4) audit gaps,
(5) backup.

### Feedback files as first-class memory

Behavioral corrections ("don't do X," "from now on, Y") are stored as
structured feedback files: incident → root cause → fix → how to apply.
Always importance=5. Never optional.

## Installation

```
git clone https://github.com/Sevan7-Kalo10/memoir.git
```

Copy or symlink the `memoir/` directory to your Claude Code skills
directory at `~/.claude/skills/memoir/`.

The SessionStart hook loads your startup files automatically. The Stop
hook reminds you to run maintenance. Configure `MEMOIR_STORE` to point to
your memory directory.

## Commands

| Command | Purpose |
|---------|---------|
| `/memoir:init` | Bootstrap memory directory with guided questions |
| `/memoir:status` | Health check: token budget, staleness, domain counts |
| `/memoir:remember <fact>` | Create a memory with guided frontmatter |
| `/memoir:digest` | Execute full session-close workflow |
| `/memoir:maintain` | Run maintenance: decay, merge, archive proposals |
| `/memoir:audit` | Gap analysis: topics vs stored memories |
| `/memoir:archive <file>` | Move a memory to archive |
| `/memoir:restore <file>` | Restore from archive |
| `/memoir:merge <f1> <f2>` | Merge two related memories |

## Relationship to Claude Code's built-in memory

They are complementary, not competing:

- **Built-in memory** handles ad-hoc fact storage — the LLM decides a fact
  is worth saving, writes it, and it's injected into future contexts. It
  has no lifecycle, no decay, no layering.
- **memoir** handles the architecture — what deserves to be permanent vs
  temporary, what should be hot vs cold, when to merge, when to archive.

Built-in memory is a KV store. memoir is a gardener.

## Differences from v0.1.x

| | v0.1.x (Python package) | v2.0 (Claude Code skill) |
|---|---|---|
| Interface | CLI commands + Python API | Natural language (SKILL.md) |
| Deployment | `pip install` | Copy a directory |
| Weight model | Single weight (1-5) | Two-axis: importance × recency |
| Memory layers | 4-tier loading algorithm | Hot/cold layered architecture |
| Ingestion | None (write-only) | Three-pathway ingestion discipline |
| Maintenance | Decay only | Full lifecycle: digest → maintain → audit |
| Triggers | File-loading hints | Phrase-to-action bindings |
| Platform | Claude Code only (hooks-dependent) | Any Claude Code agent |
| Feedback files | Not a concept | First-class memory type |

## The real lineage

memoir v2 didn't come from refactoring v0.1.x. It came from 1.5 months of
actually running a memory system every day — Kalo's memory at
`D:\tool\kalo\memory\`, which grew from a few files to 94 cold memories, 67
philosophy entries, a book index, and a self-maintaining hot layer that
gets updated at every session close.

The patterns that made it into memoir v2 — the iron rule of loading startup
files before speaking, the hot/cold split, the ingestion filter ("will this
matter in 6 months?"), feedback files as behavioral law — were discovered
organically. They're not design decisions. They're scars.

v0.1.x extracted the file format and the CLI. v2 extracts the discipline.
