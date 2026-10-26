# Migration — v0.1.x frontmatter → v2

memoir v2 changed the memory file schema. This is the migration procedure.
SKILL.md's progressive-disclosure table has linked here since v2.0.0, but
the file did not exist until 2026-10-05 — so no store had ever been
migrated, and the lifecycle fields were dead (nothing decayed, nothing
archived).

## Why migrate

v0.1.x files carry `name / description / weight / tags / domain /
metadata.type`. v2 replaces the single `weight` with two independent axes
(`importance` + `recency`) and adds a lifecycle state machine. Until the
files carry the v2 keys, `maintain` has nothing to compute on.

## Field mapping

| v0.1.x | v2 | Rule |
|---|---|---|
| `name` | `id` | filename stem with `_` → `-`. The stem is canonical — it stays put when `name` was edited. |
| `weight` (1–5) | `importance` | Copy 1:1. Re-judge later during maintenance, not during migration. |
| `metadata.type` | `layer` | **Do not trust it.** See gotcha 1. |
| `tags` | `tags` | unchanged |
| `domain` | `domain` | remap to the taxonomy (gotcha 4) |
| — | `recency` | latest date in the body; fall back to file mtime |
| — | `lifecycle` | `active` for every migrated file; the first `maintain` computes transitions |
| — | `created` | earliest date in the body; fall back to mtime |
| — | `updated` | latest date in the body; fall back to mtime |
| — | `related` | extract the `[[wikilinks]]` already in the body |
| `description` | `description` | keep it — v2's frontmatter block omits it, but it is real information and a rebuilt index uses it |

## Gotcha 1 — `metadata.type` is not `layer`

Old stores use `metadata.type` loosely: `feedback` gets applied to identity
notes, insights, and frameworks, not only to behavioral corrections.
Mapping `type: feedback → layer: feedback` forces `importance = 5` onto
files whose `weight` was 2. **Use the filename prefix instead**:
`feedback_*` → `layer: feedback`; everything else → `layer: cold`.

## Gotcha 2 — file mtime is often a bulk-write artifact

If the store was seeded in one pass, most files share a creation-month
mtime no matter when their content was written. Prefer dates parsed from
the body. Cap candidate dates at today — a deadline written in the text
(a registration window, an exam date) would otherwise become a false
`updated`.

## Gotcha 3 — a pre-existing `updated` may be stale

A file that already had some v2 keys but kept growing carries an old
`updated`. After migrating, compare each file's `updated` against the
latest date in its body and keep the later one, or `maintain` will read it
as long-stale.

## Gotcha 4 — the old `domain` field is mostly empty

Do not assume it maps cleanly. Infer from the filename prefix and path,
and normalize legacy values (`books` → `literature`, `core` → dissolved).
Standard seven domains: `identity relationship behavior project preference
philosophy milestone`. Add an extended domain only at ≥3 clustered
memories, named by what it covers (`literature`, `existence`, …).

## Order of operations

1. Back up the whole store (directory copy **and** off-machine).
2. Run the migration dry-run and review the complete before/after table.
3. Apply. Verify every body is byte-identical to the original — only the
   frontmatter block changes.
4. Rebuild `MEMORY.md`'s index from the frontmatter so the index sections
   and each file's `domain` agree (the spec's source-of-truth rule).
5. Run `maintain` for the first time. This is what makes the fields live.

## Do not

Do not rewrite memory *bodies* during migration. Format migration is
mechanical; the content of a cold memory is the point of keeping it. If a
file reads as cluttered, that is a maintenance judgement for the owner to
approve, not a migration side effect.
