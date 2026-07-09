# Memoir Maintenance Workflow

Maintenance keeps the cold layer healthy: pruning what's stale, surfacing
what needs attention, and preventing the memory store from becoming a
digital attic full of boxes no one opens.

## When to Maintain

- **Per-session close:** Quick scan — any obvious archive candidates? Any
  seedling memories that need linking? (Part of the digest workflow,
  step 3.)
- **Weekly (every ~7 sessions):** Full maintenance pass — check all
  lifecycle transitions, propose merges, audit cross-references.
- **On-demand:** `/memoir:maintain` — user explicitly asks.

## The Maintenance Algorithm

### Step 1: Scan

For each cold memory file in `memory/` (excluding `MEMORY.md`,
`triggers.md`, `HOT-MEMORY.md`, and `archive/`):

1. Read the frontmatter
2. Compute:
   - `days_since_update` = now - `updated` timestamp
   - `days_since_access` = now - `recency` timestamp
   - Current lifecycle state

### Step 2: Classify

Apply lifecycle transition rules (from spec-memory-model.md):

| Current state | Condition | Proposed transition |
|--------------|-----------|-------------------|
| seedling | Cross-referenced by ≥1 other memory | → active |
| seedling | Not cross-referenced AND > 3 sessions old | Flag: "Review this seedling?" |
| active | importance ≥ 4 AND days_since_update > 30 | → stable |
| active | importance ≤ 2 AND days_since_access > 60 | → fading |
| stable | importance ≤ 3 AND days_since_access > 90 | → fading |
| fading | importance ≤ 2 AND days_since_access > 120 | → archive (ASK FIRST) |
| fading | importance > 2 AND days_since_access > 90 | Flag: "Still relevant? Downgrade importance?" |

### Step 3: Detect Merge Candidates

For each pair of memories in the same domain:

1. Compute tag overlap (shared tags / total unique tags)
2. Check for explicit cross-references in the `related` field
3. If tag overlap > 50% OR cross-referenced, flag as merge candidate
4. Grep the body text for shared keywords — if keyword overlap > 30%,
   flag as merge candidate

Merge proposals should include:
- Both file names and their one-line descriptions from MEMORY.md
- What the merged file would cover
- A draft combined title and description

### Step 4: Detect Orphans

A memory is an orphan if:
- `related` field is empty OR all referenced files are archived
- No other memory references it (reverse lookup via grep for its `id`)
- AND lifecycle is `seedling` or `fading`

Orphans in `seedling` state: propose deletion or linking. Orphans in
`fading` state: propose archiving.

### Step 5: Present, Don't Execute

Maintenance output is a **proposal list**, not an execution plan:

```
## Memoir Maintenance — 2026-07-10

### Proposed Lifecycle Transitions
- `preferences-music.md`: active → stable (i=4, unchanged 45 days)
- `project-old-website.md`: active → fading (i=2, unaccessed 72 days)

### Proposed Archives (NEEDS CONFIRMATION)
- `temp-debug-notes.md`: fading, i=1, unaccessed 140 days

### Merge Candidates
- `preferences-writing.md` + `preferences-communication.md`
  → `preferences-communication-style.md`
  85% tag overlap, both cover "how Sevan likes to be talked to"

### Orphaned Memories
- `experiment-failed-approach.md`: seedling, no cross-references.
  → Delete or link to a project memory?
```

**The user confirms or rejects each proposal.** Do not execute transitions
or archives without confirmation. This is not a "silently optimize"
workflow — it's a "surface decisions for the memory owner" workflow.

## The "Never" Rules

1. **Never archive without user confirmation.** Even if all criteria are
   met. The agent proposes; the user decides.
2. **Never downgrade an importance=5 memory.** These are core identity
   anchors. If they seem wrong, it means the understanding of the user
   has changed — that's a conversation, not a maintenance operation.
3. **Never delete a memory.** Archive moves it to `archive/` with an index
   entry. Deletion is destruction. The audit trail matters.
4. **Never auto-merge without proposing it first.** Merging two memories
   requires the user to confirm the combined result is accurate.
5. **Never modify a feedback file's fix field.** Feedback files are
   behavioral law. Only the user can amend them.

## Archive Format

Archived files move to `memory/archive/`. The archive index
(`memory/archive/INDEX.md`) records:

```markdown
# Archive Index

| File | Archived | Reason | Restorable |
|------|----------|--------|------------|
| `old-preference-x.md` | 2026-07-10 | Superseded by `preference-y.md` | Yes |
| `temp-notes.md` | 2026-06-15 | Ephemeral, no longer relevant | No |
```

Restoring a file: move it back to `memory/`, set lifecycle to `active`,
reset recency to now, update MEMORY.md index, remove from archive INDEX.md
(or mark as restored with date).

## Token Budget Enforcement

HOT-MEMORY.md has a hard cap of ~2000 tokens. During maintenance, check:

- Current token count (estimate: 1 token ≈ 0.75 words for English, 1
  token ≈ 1.5 characters for CJK)
- If >2500: must trim. Remove least-recent entries first.
- If >2000: should trim. Remove entries older than 14 days with no
  follow-up.
- If <1500: room to expand. Consider if important recent events are
  missing.

Cold layer has no token cap per file, but individual files should stay
focused (one insight per file, <500 words). If a file grows beyond that,
it's probably covering too much — propose splitting.
