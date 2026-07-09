# Memoir Memory Model — Formal Specification

## The Two-Axis Model

memoir v2 replaces v0.1.x's single `weight` (1-5) with two independent axes.

### Importance (1-5): "How crucial is this to identity, behavior, or decision-making?"

| Value | Label | Description | Example |
|-------|-------|-------------|---------|
| 5 | Core | Identity-defining. Losing this changes who the agent understands the user to be. | "Sevan values foggy weather more than sunny days" |
| 4 | Defining | Important preference or behavioral pattern. Shapes responses noticeably. | "Sevan prefers direct answers, not diplomatic hedging" |
| 3 | Notable | Reveals something about the user but not definitional. | "Sevan knows C++ but prefers Python for tools" |
| 2 | Context-dependent | Useful in specific situations, not generally. | "The CI pipeline uses GitHub Actions" |
| 1 | Ephemeral | Temporary, unlikely to matter beyond a few sessions. | "Sevan is currently reading Chapter 3 of Armstrong Topology" |

### Recency (timestamp): "When was this last accessed, reinforced, or verified?"

Stored as ISO-8601 timestamp in the `recency` field. Updated automatically
whenever the memory is:
- Read during a relevant conversation
- Extended with new information
- Cross-referenced by a new memory
- Confirmed or corrected by the user

The `updated` field tracks file modification time. `recency` tracks
cognitive access — a stable memory (unchanged for 90 days) can still have
recent recency if it was consulted during a conversation.

### Why Two Axes?

v0.1.x's single weight had this problem:

| Situation | v0.1.x weight | What it should be |
|-----------|--------------|-------------------|
| Core identity, last accessed 60 days ago | w=5 | importance=5, recency=old |
| Trivial fact, accessed 5 minutes ago | w=3-4 | importance=1, recency=now |
| Old preference that has changed | w=4 (stale) | importance=2, recency=old |

Conflating importance and recency into one number forced false equivalences.
The two-axis model lets the loading system decide: high-importance memories
are always loaded regardless of recency; low-importance memories are dropped
when recency falls below threshold.

## Lifecycle State Machine

```
                    ┌─────────┐
                    │seedling │  Newly created, unverified
                    └────┬────┘
                         │ After first cross-reference or user review
                    ┌────▼────┐
              ┌─────│ active  │─────┐
              │     └────┬────┘     │
              │          │          │ Importance ≥ 4 AND unchanged 30 days
              │          │          │
     Restore  │   ┌──────▼──────┐   │
              │   │   stable    │   │
              │   └──────┬──────┘   │
              │          │          │
              │          │          │ Importance downgraded AND
              │          │          │ unaccessed 90 days
              │   ┌──────▼──────┐   │
              └───│   fading    │───┘ Explicit restore
                  └──────┬──────┘
                         │ Importance ≤ 2 AND unaccessed 120 days
                         │ (user must confirm)
                  ┌──────▼──────┐
                  │  archived   │  Moved to archive/
                  └─────────────┘  Indexed in archive/INDEX.md
```

### Transition Rules (applied during maintenance)

**seedling → active**
- Trigger: memory is cross-referenced by another memory, OR user explicitly
  reviews and confirms it
- Default: after 3 sessions without cross-reference, prompt user to review

**active → stable**
- Trigger: importance ≥ 4 AND file modification time > 30 days ago
- Meaning: this memory has "settled" — it's important and stable, not
  changing session to session

**active → fading**
- Trigger: importance ≤ 2 AND recency > 60 days ago
- Meaning: this memory was never very important and hasn't been accessed
  recently. It's fading from relevance.

**stable → fading**
- Trigger: importance downgraded (user re-evaluates) AND recency > 90 days
- Meaning: something that used to be core is no longer accurate or relevant

**fading → archived**
- Trigger: importance ≤ 2 AND recency > 120 days
- Constraint: **must ask user for confirmation.** Never auto-archive.
- Behavior: move file to `archive/`, append entry to `archive/INDEX.md`,
  remove from `MEMORY.md` index

**fading → active**
- Trigger: user explicitly accesses, extends, or restores the memory
- Behavior: reset recency to now, set lifecycle to active

**Any → archived (explicit)**
- Trigger: user runs `/memoir:archive <file>`
- No conditions — immediate move to archive/

### The Merge Path

When two memories in `active` or `stable` state cover the same topic:

1. Create a new combined memory (lifecycle: active)
2. Cross-reference both originals in the new file's `related` field
3. Archive both originals
4. The new file gets `importance = max(original1, original2)`

## File Types (layer field)

| layer | Purpose | Typical importance | Created by |
|-------|---------|-------------------|------------|
| `cold` | Permanent insight about the user | 3-5 | digest ingestion (pathway B) |
| `feedback` | Behavioral correction | 5 (always) | User says "don't do X" / "from now on Y" |
| `trigger` | Phrase-to-action binding | 4-5 | Explicit setup or behavioral need |
| `hot` | Self-maintaining narrative summary | N/A | Agent updates HOT-MEMORY.md at session close |

Note: `layer: hot` only applies to HOT-MEMORY.md itself. Individual memories
in the cold directory never have `layer: hot`.

## Domain Taxonomy

Domains organize cold memories. The **standard seven** are a starting
point, not a closed set:

| Domain | What it covers |
|--------|---------------|
| `identity` | Who the user is — role, self-description, core traits |
| `relationship` | How the user relates to others — trust patterns, social preferences |
| `behavior` | How the user acts — habits, routines, response patterns |
| `project` | What the user is building — projects, goals, technical decisions |
| `preference` | What the user likes — tools, aesthetics, communication style |
| `philosophy` | What the user believes — values, worldview, intellectual positions |
| `milestone` | Key events and turning points |

### Agent-extensible domains

The agent may create new domains when a memory doesn't fit any existing
one. Rules:

1. **Try existing first.** Before creating a domain, grep existing domain
   names to see if one covers this (e.g., a memory about how the user
   reads books might fit `behavior` or `preference` rather than needing a
   new `reading` domain).
2. **Name by what it covers, not the topic.** A domain for literary taste
   should be `literature`, not the name of a specific author. Keep it one
   word, lowercase.
3. **Three-memory threshold.** Don't create a domain for a single memory.
   Wait until at least three memories naturally cluster around a topic,
   then propose the new domain.
4. **Update the index.** When a new domain is created, add it to
   `MEMORY.md` as a new `## domain-name` section.
5. **Remove dead domains.** During maintenance, if a domain has zero
   active memories (all archived), propose removing it from the index.

The domain list in `/memoir:init` is the default. In a running store, the
agent owns the taxonomy — MEMORY.md's section headers are the source of
truth.

## MEMORY.md — The Index

`MEMORY.md` is a manually maintained index of the cold layer. Format:

```markdown
# Memory Index

## identity
- [Core Identity](memory/core-identity.md) — Who the user is (i=5)
- [Aesthetic Preferences](memory/preferences-aesthetic.md) — Fog, dusk, muted tones (i=4)

## relationship
- [Trust Patterns](memory/relationship-trust.md) — Trust is earned, not assumed (i=5)
...
```

The index entry includes: filename, one-line description, and importance
score. The agent maintains this index — when a new cold memory is created,
add it to the index. When a memory is archived, remove it. When importance
changes, update the annotation.

## Cross-Referencing

Memories can reference each other via the `related` field in frontmatter:

```yaml
related: [core-identity, trust-patterns, feedback-tone-register]
```

Cross-references are established during:
- **Creation**: the agent checks for related memories and links them
- **Ingestion**: new insights are linked to existing memories they extend
- **Maintenance**: seedling memories are linked to their nearest neighbors

Cross-references serve two purposes: (1) they prevent duplicate/memory
siloing — linked memories form a graph the agent can traverse; (2) they
speed retrieval — reading one memory surfaces its neighbors.
