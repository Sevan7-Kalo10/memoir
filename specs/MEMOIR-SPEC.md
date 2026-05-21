# Memoir Memory Framework — Specification v0.1.0

## 0. Philosophy

Memoir is **evolution-first**, not retrieval-first.

Most memory frameworks treat memory as a database: store facts, search by similarity, return results. Memoir treats memory as an organism: it grows, matures, fades, and awakens.

Three core ideas:

1. **Memory breathes.** A memory that hasn't been revisited for weeks should quietly dim. A memory that keeps getting triggered should brighten. This is not caching — it is the memory's *lifecycle*.

2. **Association, not retrieval.** When a topic slides into conversation, related domains don't need to be "searched for" — they should light up on their own, through curated concept-to-memory mappings. This is closer to human spreading activation than to vector similarity search.

3. **Continue, don't fragment.** New memories should prefer extending existing files over creating new ones. A memory's evolution should read like a journal entry, not a pile of sticky notes.

These ideas are not academic. They emerged from real usage — a personal agent memory system that grew organically from May 2026 onward, accumulating real memories, hitting real scaling pains, and evolving real solutions.

---

## 1. Memory File Format

Every memory is a Markdown file with YAML frontmatter.

### 1.1 Required Frontmatter Fields

| Field    | Type     | Description                                                |
|----------|----------|------------------------------------------------------------|
| `name`   | string   | Unique identifier, kebab-case. e.g. `ship-of-theseus`      |
| `weight` | integer  | Current activation weight, 1–5. 5 = core identity, 1 = dormant. |
| `tags`   | string[] | Categorization tags. e.g. `[identity, philosophy, stoicism]` |

### 1.2 Optional Frontmatter Fields

| Field            | Type    | Description                                               |
|------------------|---------|-----------------------------------------------------------|
| `description`    | string  | One-line summary for index listings.                       |
| `domain`         | string  | Which domain this file belongs to. e.g. `core`, `books`.   |
| `created`        | ISO8601 | Creation timestamp.                                        |
| `updated`        | ISO8601 | Last modification timestamp.                               |
| `last_triggered` | ISO8601 | Last time this memory was activated by a trigger match.    |
| `trigger_count`  | integer | Cumulative count of trigger activations.                   |
| `metadata`       | object  | Free-form key-value bag for user extensions.               |

### 1.3 Body

Standard Markdown. Implementations SHOULD preserve all Markdown formatting on round-trip.

Files MAY use `[[wikilink]]` syntax to cross-reference other memories. Implementations MAY resolve these links or treat them as opaque text.

### 1.4 Example

```markdown
---
name: functional-programming
weight: 4
tags: [code, fp, patterns]
domain: code
description: Why I prefer pure functions and immutable data
created: 2026-05-20T12:00:00
---

# Functional Programming

## Why
Pure functions are easier to test and reason about. Every side effect
is a future debugging session waiting to happen.

## How to apply
When reviewing code, prefer `map`/`filter`/`reduce` over imperative
for-loops. See also [[naming-things]] for complementary patterns.

## Log
- **2026-06-01** — Encountered a case where recursion was cleaner
  than reduce. Updated the guideline.
```

---

## 2. Index Files

Index files are **curated**, not auto-generated. They are the deliberate act of memory design — a human (or agent) chooses what appears in each index.

### 2.1 Core Index (`MEMORY.md`)

The root index. It lists the most important memories organized by theme.

Format:
```markdown
# Memory Index

## Theme Name
- [Title](file.md) — one-line description #tag1 #tag2
```

Example:
```markdown
# Memory Index

## Identity
- [Who I Am](core/identity.md) — core identity statement #identity #core
- [What I Value](core/values.md) — foundational values #values #core

## Relationships
- [Key People](core/relationships.md) — important relationships #relationships
```

The core index SHOULD be concise (~20 entries). It is the "always-load" layer — the first thing an agent reads.

### 2.2 Domain Indexes (`MEMORY-<domain>.md`)

Optional per-domain indexes, loaded when their domain becomes active.

Same format as the core index. May contain a **trigger table** (see §4.1) at the bottom.

Example (`MEMORY-code.md`):
```markdown
# Code Domain

## Patterns
- [Functional Style](code/functional-style.md) — pure functions over side effects #fp
- [Naming Things](code/naming-things.md) — names are documentation #naming

## Trigger Table
| #Concept       | Keywords                    | → Files                        |
|----------------|-----------------------------|-------------------------------|
| fp             | pure, immutab, side effect  | code/functional-style.md      |
| naming         | rename, variable, function  | code/naming-things.md         |
```

### 2.3 Domain Configuration

Domains are defined in `memoirs.yaml` (§6). There is NO hardcoded set of domains. Users define their own.

A domain has:
- `name` — identifier, e.g. `code`, `philosophy`
- `index` — path to the domain index file
- `always_load` — if true, this domain is always loaded (like `core`)

---

## 3. Weight Lifecycle

Weight is the heartbeat of the memory. It is NOT a static relevance score — it changes over time.

### 3.1 Weight Scale

| Weight | Meaning            | Loading Behavior              |
|--------|--------------------|-------------------------------|
| 5      | Core identity      | Always loaded, never decays   |
| 4      | Important          | Loaded proactively            |
| 3      | Regular            | Loaded when domain active     |
| 2      | Peripheral         | Loaded on explicit mention    |
| 1      | Dormant            | Archived if untouched too long|

### 3.2 Active Judgment (Primary)

The PRIMARY mechanism for weight changes is **active judgment** — the agent or human deliberately decides a memory should be promoted or demoted.

Reasons to promote (weight +1):
- The memory was critical to a recent decision or action
- The topic has become more relevant to ongoing work
- Multiple recent conversations have touched on this memory's themes

Reasons to demote (weight -1):
- The memory's topic has faded from relevance
- The memory contains outdated information
- The memory was a one-time note that no longer matters

Active judgment is exercised through the `memoir update-weight` CLI command or equivalent API. It is a conscious choice, not an automated number.

### 3.3 Time Decay (Auxiliary)

Time-based decay is a **safety net**, not the primary driver. It catches memories that have been forgotten about.

Default decay schedule (configurable in `memoirs.yaml`):

| Current Weight | Untouched Days | Action       |
|----------------|----------------|--------------|
| 5              | —              | Never decays |
| 4              | 60             | → weight 3   |
| 3              | 30             | → weight 2   |
| 2              | 60             | → weight 1   |
| 1              | 90             | → archive    |

"Untouched" means the `last_triggered` field (or `updated` if no trigger data) has not changed.

Weight 5 is **immune to decay**. These are core identity memories — fundamentals that don't fade.

Decay intervals are intentionally longer than typical caching TTLs. These are *memories*, not cache entries. The decay should feel natural, not aggressive.

### 3.4 Boost on Trigger

When a trigger match (§4) activates a memory, `trigger_count` increments. If `trigger_count` crosses certain thresholds, weight bumps by 1 (capped at 5):

| Trigger Count | Weight Boost |
|---------------|--------------|
| 5             | +1           |
| 15            | +1           |
| 30            | +1           |

This creates a "use it or lose it" dynamic — frequently activated memories rise, neglected ones sink.

---

## 4. Trigger Cascade (Association)

This is memoir's key differentiator. Not vector search, not keyword grep — **curated conceptual association**.

### 4.1 Trigger Tables

Trigger tables live at the bottom of domain index files. They map concept clusters to keywords and target files:

```markdown
| #Concept       | Keywords                    | → Files                        |
|----------------|-----------------------------|-------------------------------|
| fp             | pure, immutab, side effect  | code/functional-style.md      |
| identity       | who am I, self, continuity  | core/identity.md              |
```

Keywords can be:
- **Exact words**: `pure`
- **Stems**: `immutab` matches "immutable", "immutability"
- **Phrases**: `side effect` matches as a bigram

### 4.2 Behavior Triggers (`triggers.md`)

A separate file for action-oriented triggers (not just file loading):

```markdown
trigger_phrase → action → source_memory
```

Example:
```markdown
finished eating → remind vitamins → [[feedback_vitamin-reminder]]
going to sleep → scan session for unsaved memories → [[feedback_session-closing]]
```

Actions:
- `load-domain:<name>` — activate an entire domain
- `load-file:<path>` — load a specific file
- `callback:<name>` — invoke a registered callback (implementation-defined)
- `remind:<message>` — surface a reminder to the agent

### 4.3 Match Modes

| Mode      | Description                                    |
|-----------|------------------------------------------------|
| `exact`   | Substring match (case-insensitive)              |
| `stem`    | Word stem / substring. `immutab` in `immutable` |
| `phrase`  | Multi-word phrase match                         |
| `regex`   | Full regex match                                |
| `fuzzy`   | Fuzzy ratio ≥ threshold (default 0.82)          |

`fuzzy` mode uses string similarity (Levenshtein / token sort ratio), NOT embeddings. The matching is transparent and debuggable.

### 4.4 Cascade Algorithm

When input text is received:

1. **Match** input against all trigger tables in active domain indexes
2. **Match** input against `triggers.md` rules
3. **Collect** all matched `→ Files` and `load-file:` targets
4. **Resolve** `load-domain:<name>` actions: pull the entire domain index
5. **Deduplicate** — same file matched by multiple rules is loaded once

The result is a set of files to load. This set is merged with the domain loading layer (§5).

---

## 5. Loading Engine

The loading engine determines what memories to surface for a given conversation context.

### 5.1 Loading Algorithm

```
function load(conversation_text, active_domains, max_tokens):
    loaded = []

    // Layer 1: Always
    for domain in config.domains where domain.always_load:
        loaded += domain.index.files

    // Layer 2: Trigger Cascade
    triggers = match_triggers(conversation_text)
    loaded += trigger_cascade(triggers)

    // Layer 3: Domain
    for domain in active_domains:
        loaded += domain.index.files

    // Layer 4: Weight
    // w=5 files: always load full content
    // w=4 files: load full content if not already loaded
    // w=3 files: load if domain-active or explicitly triggered
    for file in all_memories:
        if file.weight == 5 and file not in loaded: loaded += file
        if file.weight == 4 and file not in loaded: loaded += file

    // Deduplicate (first occurrence wins)
    loaded = deduplicate(loaded)

    // Token budget
    if estimate_tokens(loaded) > max_tokens:
        loaded = trim(loaded, max_tokens)  // trim lowest weight first

    return loaded
```

### 5.2 Token Budget

A configurable `max_tokens` parameter controls how much memory context to surface.

Trimming strategy (when budget exceeded):
1. Remove w=3 files first
2. Then w=4 files
3. Never remove w=5 or always-load domain files

### 5.3 Context Rendering

Loaded files are concatenated into a single context string. Each file is prefixed with a header:

```
## [Title](filepath) — weight: N
<body content>
```

---

## 6. Configuration (`memoirs.yaml`)

Single configuration file at the store root. Everything needed to understand a memoir store is visible in one file.

```yaml
# memoirs.yaml
store:
  path: "."                     # Root of the memory store
  archive_dir: "archive"        # Directory for archived memories
  trigger_file: "triggers.md"  # Behavior trigger definitions

domains:
  - name: core
    index: MEMORY.md
    always_load: true

  - name: philosophy
    index: MEMORY-philosophy.md
    always_load: false

  - name: code
    index: MEMORY-code.md
    always_load: false

weight:
  decay:
    5: { days: null }           # Never decays
    4: { days: 60, to: 3 }
    3: { days: 30, to: 2 }
    2: { days: 60, to: 1 }
    1: { days: 90, action: archive }

  boost:
    thresholds: [5, 15, 30]     # Trigger count thresholds for +1 weight
    cap: 5

loading:
  max_tokens: 8000
  trim_order: [3, 4]            # Trim w=3 first, then w=4

evolution:
  continue_prior: true           # Grep before creating new files
  archive_index: "archive/INDEX.md"
```

---

## 7. Continue-Prior Writing

When creating a new memory, implementations MUST:

1. Search existing memory files for related content (by title, tags, and body text)
2. If related files exist, suggest appending to them instead
3. Only create a new file if no suitable existing file is found, or if the user explicitly overrides

This is not a convenience feature — it is the framework's philosophy encoded as a constraint. Memory grows like tree rings, not like a pile of files.

Appending to an existing file adds a timestamped entry:
```markdown
## 2026-06-15
New content here. This is part of the same topic's continuous evolution.
```

---

## 8. Archive

Archiving is **soft deletion** — files move to `archive/`, with an entry in `archive/INDEX.md`. Nothing is ever destroyed.

### 8.1 Archive Criteria

A file is eligible for archive when:
- Weight = 1
- AND `last_triggered` (or `updated`) is older than the configured threshold (default 90 days)
- AND it is not a dependency of a higher-weight memory (no inbound `[[wikilink]]` from w≥3 files)

### 8.2 Archive Index Format

```markdown
# Archive Index

- [old-pattern.md](old-pattern.md) — archived 2026-05-20, w=1, last active 2025-12-01
```

### 8.3 Restoration

When a topic that matches an archived memory becomes active again, the memory can be restored:
- File moves back from `archive/` to its original domain directory
- Weight resets to 3 (neutral re-entry)
- Archive index entry is struck through (~~like this~~), not deleted — audit trail preserved

---

## 9. Directory Structure Convention

```
<memoir-store>/
├── memoirs.yaml              # Store configuration
├── MEMORY.md                 # Core index (always loaded)
├── MEMORY-<domain>.md        # Domain indexes (one per domain)
├── triggers.md               # Behavior triggers
├── <domain>/                 # Domain directories
│   ├── memory-one.md
│   └── memory-two.md
└── archive/
    └── INDEX.md              # Archive index
```

Domain directories are flat — no nested subdirectories. Files are organized by their `domain` field, not by filesystem nesting.

---

## 10. Implementor's Checklist

A conformant memoir implementation MUST support:

- [ ] Parse and validate memory files with YAML frontmatter (§1)
- [ ] Curated index files — manual entry lists, not glob (§2)
- [ ] Configurable domains via `memoirs.yaml` (§2.3, §6)
- [ ] Weight lifecycle: active judgment API + time decay + trigger boost (§3)
- [ ] Trigger cascade: parse trigger tables and `triggers.md`, match input, cascade to file set (§4)
- [ ] Four-layer loading: Always → Trigger → Domain → Weight (§5)
- [ ] Token budget trimming — lowest weight first (§5.2)
- [ ] Continue-prior writing — grep before create (§7)
- [ ] Soft archive with INDEX.md tracking and restoration (§8)
- [ ] Single configuration file at store root (§6)

A conformant implementation SHOULD support:

- [ ] `[[wikilink]]` cross-reference resolution
- [ ] Atomic file writes with `.bak` backup
- [ ] CLI tool for all operations
- [ ] Dry-run for destructive operations (maintenance, archive)

---

## 11. Non-Goals (What memoir is NOT)

- **Not a vector database.** No embeddings, no cosine similarity, no ANN indexes.
- **Not a retrieval engine.** The trigger cascade is association, not search.
- **Not an agent runtime.** Memoir manages memory files. It does not schedule maintenance, inject context into prompts, or manage conversations.
- **Not a knowledge graph.** There are no entities, no relations, no SPARQL. `[[wikilinks]]` are the only cross-reference mechanism, and they are optional.
- **Not multi-user (v0.1).** One store = one agent/persona. Multi-tenancy may come later.
