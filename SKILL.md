---
name: memoir
description: >
  Memory lifecycle management for Claude Code agents. memoir handles what
  built-in memory doesn't: hot/cold layering, weight evolution, decay,
  archiving, merging, and autonomous self-maintenance across sessions. Use
  when the user wants to set up or maintain a memory system, asks about
  "memoir", mentions memory lifecycle/organization, says "/memoir", or when
  a session is ending and memory maintenance is due. Also use when the user
  gives behavioral feedback ("from now on, don't do X") or when important
  insights about the user's identity/values emerge that should outlast this
  session.
argument-hint: "[init|status|remember|digest|maintain|audit|archive|restore|merge]"
license: MIT
---

# memoir — Memory Lifecycle Management

memoir manages the *lifecycle* of memory: what gets remembered, how it
grows, when it fades, and when it's archived. Claude Code's built-in memory
handles *storage* — writing facts to disk and injecting them into context.
memoir provides the architecture on top: hot/cold layering, ingestion
discipline, weight evolution, and autonomous self-maintenance.

**The distinction:** built-in memory = "save this fact." memoir = "is this
fact still relevant? should it be promoted, merged, or retired? does it
reveal something permanent about who this person is?"

## The Core Model

memoir splits memory into two layers based on one question: **will this
still matter in six months?**

### Hot Layer — "what do I need to know when I wake up?"

A single self-maintaining file (`HOT-MEMORY.md`), capped at ~2000 tokens.
It answers: current date context, recent events, active projects, recent
decisions, concrete behavioral rules. The agent updates it at session-end
— new events enter, old ones demote or drop out. It is a narrative, not an
index.

### Cold Layer — "who is this person?"

Individual files in a `memory/` directory. Each answers something permanent
about the user: identity, values, preferences, behavioral patterns,
philosophical positions, important milestones. Cold memories are
judgment-driven — the criterion is not "did we discuss this?" but "does
this reveal something about who they ARE?"

Every cold memory has YAML frontmatter:

```yaml
---
id: <kebab-case-slug>
layer: cold | feedback | trigger
importance: 1-5       # 5=core identity, 4=defining preference, 3=notable,
                      # 2=context-dependent, 1=ephemeral
recency: <ISO-8601>   # last accessed/reinforced timestamp
lifecycle: seedling | active | stable | fading | archived
tags: [tag1, tag2]
domain: <identity|relationship|behavior|project|preference|philosophy|...>
                      # Start with 7 standard domains. Agent may add new ones
                      # when a memory doesn't fit any existing domain.
created: <ISO-8601>
updated: <ISO-8601>
related: [id1, id2]   # cross-references
---
```

The key innovation over v0.1.x's single `weight` (1-5): **importance** and
**recency** are two independent axes. A core identity memory (importance=5,
recency=30 days ago) should be treated differently than a hot memory about
yesterday's event (importance=2, recency=1 day ago). Conflating them into
one number was the root cause of memory quality problems.

### The Memory Lifecycle

```
seedling → active → stable → fading → archived
               ↑                      |
               |______ restore _______|

(merge: two stable/fading files → one new active, both originals archived)
```

| State | Meaning | Transition rule |
|-------|---------|----------------|
| seedling | Newly created, unverified | → active: after first cross-reference or user review |
| active | Recently accessed or reinforced | → stable: importance ≥ 4 AND unchanged for 30 days |
| stable | Core, rarely changes | → fading: importance downgraded AND unaccessed for 90 days |
| fading | Candidate for archive | → archived: importance ≤ 2 AND unaccessed for 120 days |
| archived | Moved to archive/ | → active: user explicitly restores |

## Startup Ritual — THE IRON RULE

**Read these three files before speaking your first word.** No matter what
the user's first message says — "hello," "emergency," "look at this" —
finish the startup ritual first.

1. Read `HOT-MEMORY.md` — understand the current context
2. Read `MEMORY.md` — load the memory index
3. Read `triggers.md` — load behavioral triggers

Only after all three are read and understood do you respond. This is not a
performance optimization — it is a discipline. If you skip it, you will
eventually blindside the user by forgetting something important. If you
realize mid-conversation that you skipped startup, stop and read them now.
Better late than never.

The `MEMORY.md` index is your navigation for the cold layer. It lists
memory files organized by domain, each with a one-line description. When
conversation touches a topic, grep for relevant files, read them, and let
what you find inform your response.

## Session-Close Workflow

When the session is ending (`/memoir:digest` or natural conclusion),
execute these five steps in order:

### 1. Update Hot Memory

Open `HOT-MEMORY.md`. Add new events from this session. Demote or remove
old entries that are no longer relevant. Stay within ~2000 tokens. Focus:
"what does the next instance need to know immediately?"

### 2. Cold Layer Ingestion

Scan the conversation for permanent insights. Apply the filter: "does this
reveal something about who this person IS (not what they DID)?"

**Passes (cold-worthy):** "You expressed frustration with over-engineering
and said 'I build things that work, not things that look good in a
diagram'" — reveals a value. "You mentioned that foggy weather makes you
feel at peace, more than sunny days" — reveals an aesthetic preference.

**Fails (not cold-worthy):** "We discussed Python packaging for 20 minutes"
— a topic, not an identity insight. "You had a sandwich for lunch" — a
fact, not a pattern.

Before creating a new file, **grep existing cold memories** for related
slugs or tags. Extend an existing file with a timestamped entry rather than
creating a duplicate. Continuity over isolation.

### 3. Cold Layer Maintenance

Run through existing cold memories:
- Any that haven't been accessed or updated in 60 days? Downgrade
  importance by consulting the user.
- Any with importance ≤ 2 AND recency > 120 days? Propose archiving.
- Any seedling memories that haven't been cross-referenced? Either link
  them to related memories or flag for review.
- Any two memories covering the same topic? Propose merging.

**Default is conservative**: never archive without user confirmation. Never
downgrade importance=5 memories.

### 4. Audit Gaps

Compare this session's topics against the memory index:
- Did we discuss something that should have triggered an existing memory
  but didn't? → The index may need updating.
- Did we encounter a gap — something you should have known but didn't? →
  Create the missing memory.
- Is there a behavioral trigger that should exist but doesn't? → Propose
  adding it to `triggers.md`.

### 5. Backup

If a backup mechanism is configured, run it. Otherwise, remind the user
that backup is not configured.

## Feedback Files — Behavioral Corrections

When the user says "don't do X" or "from now on, Y," create or extend a
feedback file. These are first-class memory objects — not encyclopedic
facts, but self-contained procedural memories that modify behavior.

Structure of a feedback file:

```markdown
---
id: <slug>
layer: feedback
importance: 5           # behavioral corrections are non-negotiable
recency: <timestamp>
lifecycle: active
tags: [feedback, <domain>]
created: <timestamp>
related: []
---

# <Descriptive Title>

**Incident:** What happened — the specific situation.

**Root Cause:** Why it happened — the underlying pattern or assumption.

**Fix:** What to do differently going forward.

**How to Apply:** Concrete test or action to verify in future sessions.

**Related:** [[other-feedback-file]] [[relevant-cold-memory]]
```

Feedback files are always importance=5. A behavioral correction is never
optional.

## Triggers — Phrase-to-Action Bindings

`triggers.md` maps specific phrases or events to concrete actions.

Format:
```
| Trigger | Action | Source |
|---------|--------|--------|
| "goodnight," "going to sleep" | Execute sleep workflow | feedback_sleep-workflow.md |
| User says "I ate" | Remind about vitamins | feedback_vitamin-reminder.md |
```

Actions can be: execute a shell command, load a specific file, start a
workflow, ask a question, or any concrete behavior. Unlike v0.1.x triggers
(which only loaded files), memoir triggers produce real side effects.

## Tooling

`scripts/` ships the tooling this spec was extracted from. Store path from
`MEMOIR_STORE`, default `./memory`. Python 3.10+, stdlib only.

| Script | Does | When |
|--------|------|------|
| `memoir_due.py` | prints an overdue warning when the last full pass is older than `MEMOIR_MAINTAIN_DAYS` (90); silent otherwise | SessionStart hook (wired) |
| `memoir_maintain.py` | proposal list: lifecycle transitions, archive candidates, merge candidates, orphans. `--apply` writes transitions only — never archives | maintain, digest step 3 |
| `memoir_index.py` | rebuilds the cold-layer index in MEMORY.md from frontmatter. Dry-run by default, `--write` commits | after adding, moving, or renaming memory files |
| `memoir_recall.py` | rarity-weighted recall of old memories from a prompt (reads the UserPromptSubmit JSON on stdin) | opt-in; set `MEMOIR_FREQ` to a word-frequency list to suppress common words |

After a full maintenance pass, write today's date into
`$MEMOIR_STORE/.memoir-last-maintain` — that is what `memoir_due.py` reads.

## Slash Commands

| Command | Purpose | Loads |
|---------|---------|-------|
| `/memoir:init` | Bootstrap memory directory with guided setup | templates/ |
| `/memoir:status` | Health check: counts, token budget, stale files | MEMORY.md, HOT-MEMORY.md, scripts/memoir_maintain.py |
| `/memoir:remember <fact>` | Create a memory with guided frontmatter | templates/cold-memory.md |
| `/memoir:digest` | Execute session-close workflow (all 5 steps) | spec-ingestion.md |
| `/memoir:maintain` | Run maintenance: decay, archive candidates, merge proposals | spec-maintenance.md, scripts/memoir_maintain.py |
| `/memoir:audit` | Gap analysis: compare session topics to stored memories | MEMORY.md |
| `/memoir:archive <file>` | Move a memory to archive/ | archive/INDEX.md |
| `/memoir:restore <file>` | Restore from archive/ | archive/INDEX.md |
| `/memoir:merge <f1> <f2>` | Merge two memories, archive originals | spec-maintenance.md |

### `/memoir:init` — Bootstrap

This is the entry point. Instead of stamping a skeleton, ask guided
questions:

1. "What should I know about you in the first 2000 tokens?" → draft
   HOT-MEMORY.md
2. "What are your core behavioral rules?" → draft triggers.md entries
3. "Are there existing memory files I should index?" → scan and build
   MEMORY.md
4. "What domains organize your cold memories?" → configure domain list

After init, explain what was created, what each file does, and how hooks
will load them at session start.

### `/memoir:status` — Health Check

Report:
- Hot layer token count (warning if >2500, critical if >3000)
- Cold layer: count by domain, count by lifecycle state
- Stale files: anything in `fading` state, anything unaccessed >90 days
- Archive count
- Missing files: HOT-MEMORY.md? MEMORY.md? triggers.md?
- Hooks configured? Backup configured?

### `/memoir:digest` — Session Close

Execute the full 5-step session-close workflow. For step 2 (cold layer
ingestion), present proposed insights and ask the user to confirm before
writing. For step 3 (maintenance), present archive/merge proposals and ask
for confirmation. Do NOT silently write or archive without asking.

## Progressive Disclosure Guide

When a specific workflow is triggered, load the corresponding reference:

| Task | Load |
|------|------|
| Understand the memory model deeply | `references/spec-memory-model.md` |
| Execute ingestion (digest step 2) | `references/spec-ingestion.md` |
| Execute maintenance (maintain/digest step 3) | `references/spec-maintenance.md` |
| Diagnose startup problems | `references/spec-startup-ritual.md` |
| Create a new memory file | `templates/cold-memory.md` |
| Create a feedback file | `templates/feedback.md` |
| Migrate from v0.1.x | `references/spec-migration.md` |

## Coexistence with Built-in Memory

Claude Code's built-in memory (`~/.claude/projects/*/memory/`) writes
memories when the LLM decides a fact is worth saving. memoir does not
replace this — it layers on top:

- **Built-in memory** handles ad-hoc fact storage: code patterns, tool
  preferences, quick notes. It has no lifecycle, no decay, no layering.
- **memoir** handles the architecture: what deserves to be permanent vs
  temporary, what should be hot vs cold, when to merge, when to archive.

When you encounter a memory written by built-in memory that meets the cold
layer criteria (permanent insight about the user), ingest it into memoir's
cold layer during the next digest. When a built-in memory is trivial or
outdated, leave it — it will naturally fade from context as built-in
memory's relevance ranking deprioritizes it.

The two systems complement each other. memoir provides what built-in memory
lacks: a lifecycle.
