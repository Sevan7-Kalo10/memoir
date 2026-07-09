# Memoir Ingestion Discipline

Ingestion is the most operationally critical workflow in memoir. It answers:
after a conversation, what should become permanent memory, and what should
not?

## The Fundamental Criterion

**"Will this still matter in six months?" AND "Does this reveal something
about who this person IS (not what they DID)?"**

Both halves must be true. A fact can be permanent ("the codebase uses
Python 3.14") without being identity-revealing — that's project context,
not cold memory. A fact can be identity-revealing ("I hate marketing
speak") without being permanent — that might be a temporary mood. The AND
means: permanent AND identity-revealing.

## Three Ingestion Pathways

### Pathway A: Hot Layer Update (every session close)

**What to add:**
- New events since the last update (decisions made, projects started,
  milestones reached)
- Context shifts (entered a new phase of work, relationship changed, new
  constraints emerged)
- Active project status (what's in flight, what's blocked)
- Behavioral updates ("from now on, wake me up earlier")

**What to demote or remove:**
- Events older than 7 days that had no follow-up
- Project statuses that have been superseded
- Temporary notes that were resolved
- Anything that the next instance doesn't need to know immediately

**Token budget:** Tight cap at ~2000 tokens. If adding new content would
exceed the budget, remove the least-recent/least-important entries first.
If HOT-MEMORY.md is under 1500 tokens, you have room to expand. If it's
over 2500, you must trim.

**Structure:** Write as a narrative, not a list. "We spent the afternoon
debugging the SNN simulator's g_syn parameter — homeostasis now
auto-tunes it from 5.0 to ~0.42 nS." is better than "SNN: g_syn param
fixed." The narrative carries context; the list is dead data.

### Pathway B: Cold Layer Ingestion (every session close)

This is the hardest and most important step. The agent scans the full
conversation and asks: what permanent insights about this person emerged?

**The filter — ask three questions about each potential insight:**

1. **Identity test:** Does this reveal something about who they ARE
   (beliefs, values, aesthetic preferences, behavioral patterns, ways of
   thinking), not just what they DID?

2. **Permanence test:** Will this still be true and relevant in six
   months?

3. **Specificity test:** Is this specific enough to be useful? (Vague
   insights like "they like good design" are noise. Specific ones like
   "they prefer Swiss-style typography — Helvetica, grid systems, strong
   asymmetry" are signal.)

**Examples of what passes:**
- "You said: 'I build things that work, not things that look good in a
  diagram.'" → Reveals a value: practicality over presentation. (identity
  test: yes, permanence: yes, specificity: yes)
- "You consistently prefer dusk over sunrise, fog over clear skies, muted
  tones over bright colors." → Reveals an aesthetic pattern. (yes, yes,
  yes)
- "When faced with a decision, you tend to list all options on paper
  before choosing — you said 'I need to see them in one place.'" →
  Reveals a thinking style. (yes, yes, yes)

**Examples of what fails:**
- "We discussed the SNN simulator's g_syn parameter." → A topic, not an
  insight. (identity: no — this is what we did, not who you are)
- "You ate a sandwich for lunch." → A fact, not a pattern. (permanence: no)
- "You said Python is better than R for this task." → Context-dependent
  technical judgment. (permanence: no — may change with task)
- "The CI pipeline uses GitHub Actions." → Project context. (identity: no
  — this is codebase info, not user identity)

**Before creating a new file, always grep first:**

```bash
grep -rl "<keyword>" memory/ | grep -v archive/
```

Extend an existing file with a timestamped entry rather than creating a
new one. If a file already covers "aesthetic preferences," add the new
observation as a new paragraph with a `**(YYYY-MM-DD)**` date tag. If the
existing file's insight is contradicted or superseded, note the evolution:
"Previously (June 2026): X. As of July 2026: Y — shift happened because…"

**Continuity is more important than atomicity.** A single file tracing how
a belief evolved over six months is far more valuable than six isolated
files capturing individual snapshots.

### Pathway C: Feedback Creation (on behavioral correction)

When the user explicitly corrects your behavior ("don't do X," "from now
on Y," "why did you Z — that's wrong"), create or update a feedback file.

**Structure:**

```markdown
---
id: <slug>
layer: feedback
importance: 5
...
---

# <Title>

**Incident:** [specific context — what was happening]
**Root Cause:** [why the agent did this — the assumption or pattern]
**Fix:** [what to do differently]
**How to Apply:** [concrete test — "in future, if X happens, do Y instead
of Z"]
**Related:** [[other-feedback]] [[relevant-cold-memory]]
```

**Feedback files are always importance=5.** A behavioral correction is
never optional or "maybe." It is the highest-priority memory.

**When to extend vs create new:**
- Same root cause as an existing feedback file? Extend the existing one
  with a new incident entry.
- Entirely different behavioral pattern? Create a new file.
- Contradicts an earlier correction? Note the evolution explicitly: "This
  supersedes the correction from 2026-06-15 — the user's preference has
  changed because..."

## Ingestion Anti-Patterns

1. **Saving everything.** Not every conversation yields permanent
   insights. Zero cold layer additions is a valid outcome. Over-ingestion
   pollutes the memory store.
2. **Saving only facts.** "We use pytest" is a fact. "You value test
   coverage and get annoyed when tests are skipped" is an insight. Save
   the insight, not the fact.
3. **Creating new files for every observation.** Always search for
   existing files first. A memory that grows organically over time is
   better than five scattered fragments.
4. **Updating hot memory with trivia.** HOT-MEMORY.md is not a diary.
   Every entry should pass the test: "does the next instance need to know
   this immediately?"
5. **Archiving without asking.** Never move a memory to archive/ without
   user confirmation. The agent proposes; the user decides.
