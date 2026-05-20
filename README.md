# ksteam-memoir

**Evolution-first memory framework for AI agents.**

Most memory frameworks treat memory as a database: store facts, search by similarity, return results. Memoir treats memory as an organism: it grows, matures, fades, and awakens.

## The Three Ideas

1. **Memory breathes.** A memory not revisited for weeks quietly dims. A memory repeatedly triggered brightens. This is lifecycle, not caching.

2. **Association, not retrieval.** When a topic enters the conversation, related domains don't need to be "searched for" — they light up through curated concept-to-memory mappings. Closer to human spreading activation than vector similarity.

3. **Continue, don't fragment.** New memories prefer extending existing files over creating new ones. A memory reads like a journal entry, not a pile of sticky notes.

## Quick Start

```bash
# Install
pip install ksteam-memoir

# Create a store
memoir init --dir ./my-agent-memory

# Create a memory (automatically greps for related files first)
memoir create --title "Functional Programming" --domain code --tags "fp,patterns"

# Append to existing memory
memoir append code/functional-style.md --content "Today I learned about monads..."

# Search
memoir search "immutability"

# See what triggers fire for a given text
memoir trigger "I prefer pure functions"

# Preview what would load for a conversation
memoir load --topics "code,philosophy" --trigger "functional programming"

# Run maintenance (weight decay + archive scan)
memoir maintain --dry-run
memoir maintain

# Store stats
memoir status
```

## How It Works

### Memory Files
Plain Markdown files with YAML frontmatter:

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
When a conversation starts, memoir determines what to load:

1. **Always** — core identity files (weight 5, always-load domains)
2. **Trigger Cascade** — curated concept-to-file mappings that fire on keyword match
3. **Domain** — domain indexes activated by conversation topics
4. **Weight** — high-weight files loaded proactively

### Weight Lifecycle
Weights are not static. They change:

- **Active judgment** — you (or your agent) decide a memory should be promoted or demoted
- **Time decay** — safety net: untouched for 60 days → weight drops. w=5 is immune
- **Trigger boost** — each time a memory is triggered, its counter increments. At thresholds (5, 15, 30) weight bumps by 1

### Trigger Cascade (The Key Differentiator)
Not vector search. Curated association tables:

```markdown
| #Concept | Keywords | → Files |
|---|---|---|
| fp | pure, immutab, side effect | code/functional-style.md |
| naming | rename, variable, function | code/naming-things.md |
```

When input contains "pure function" → `#fp` lights up → `code/functional-style.md` loads.

### Continue-Prior Writing
`memoir create` greps existing files for related topics before creating a new one. New file creation is opt-in, not default. Memory grows like tree rings.

## Philosophy

This framework was not designed on a whiteboard. It grew from a personal agent memory system that ran daily from May 2025 onward — accumulating real memories, hitting real scaling pains, and evolving real solutions. Every design decision has a scar behind it.

Read the full spec at [specs/MEMOIR-SPEC.md](specs/MEMOIR-SPEC.md).

## Compared to...

| | Mem0 | ReMe | SMF | memoir |
|---|---|---|---|---|
| Retrieval | Vector embedding | Markdown links | Filesystem | Trigger cascade |
| Lifecycle | Static | Static | Static | Weight evolution |
| Creation | Append-only | New files | New files | Continue-prior |
| Infrastructure | Vector DB | Files | Files | Files + YAML |
| Philosophy | Retrieval-first | Retrieval-first | Structure-first | **Evolution-first** |

## License

MIT
