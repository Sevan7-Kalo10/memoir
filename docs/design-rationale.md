# Design rationale

This is why memoir looks the way it does. Users don't need it; it explains
the decisions for anyone changing the specs.

## What went wrong with v0.1.x

v0.1.x (May 2026) was a Python package -- `pip install ksteam-memoir`, CLI
commands, FTS5 search, 64 tests. It solved the right problem with the wrong
interface.

**The core mistake:** AI agents don't natively read Python code. They read
natural language. Asking an agent to learn CLI commands (`memoir create`,
`memoir load --render`) is asking it to operate in a foreign language. The
package was precise and testable and failed at the one thing that mattered:
the agent couldn't use it without being trained.

The v0.1.x roadmap confirms the blind spot. Its top priority was "MCP Server
+ AI_GUIDE.md" -- two separate efforts to build a natural language interface
on top of the Python package. A second door bolted onto a house whose first
door faced the wrong way.

## Why a skill

A skill is its natural language interface. The SKILL.md body is the
operating manual: the agent reads it and knows what to do. No CLI to
memorize, no package to import, no MCP server to configure.

Progressive disclosure mirrors how memory itself works:

- Level 1 (description, always in context): what triggers the skill
- Level 2 (SKILL.md body, loaded on trigger): the core model and workflows
- Level 3 (references/, loaded on demand): detailed specs

That is what "AI_GUIDE.md" was reaching for, built as architecture instead
of a documentation afterthought.

## Why one repo, two harnesses

The valuable part is the judgment rules, not the shell. A DeepSeek Harness
bundle is code -- read files, count dates, print reports -- but the decision
of which memory to retire is still the model's, following the same spec. Two
copies of the spec would drift; two thin shells over one core don't.

## Differences from v0.1.x

| | v0.1.x (Python package) | v2 |
|---|---|---|
| Interface | CLI commands + Python API | Natural language (SKILL.md) |
| Deployment | `pip install` | Plugin marketplace / directory |
| Weight model | Single weight (1-5) | Two axes: importance x recency |
| Memory layers | 4-tier loading algorithm | Hot/cold layered architecture |
| Ingestion | None (write-only) | Three-pathway ingestion discipline |
| Maintenance | Decay only | Lifecycle: digest -> maintain -> audit |
| Feedback files | Not a concept | First-class memory type |

## The real lineage

memoir v2 was not a refactor of v0.1.x. It came from 1.5 months of running a
memory system every day -- the seed store grew from a few files to dozens of
cold memories, a philosophy shelf, a book index, and a hot layer rewritten
at every session close.

The patterns that made it into v2 -- the iron rule of loading startup files
before speaking, the hot/cold split, the ingestion filter, feedback files as
behavioral law -- were discovered by running them, not designed. v0.1.x
extracted the file format; v2 extracts the discipline.
