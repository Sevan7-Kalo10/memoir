# memoir

English | [中文](README.zh.md)

**Memory lifecycle management for Claude Code and DeepSeek Harness agents.**

Built-in memory answers "should I save this fact?" memoir answers "is this
fact still relevant? should it grow, fade, merge, or retire?"

One repo, two install paths: a Claude Code skill, and a DeepSeek Harness
bundle carrying the same spec.

## Install

### Claude Code

```
/plugin marketplace add Sevan7-Kalo10/memoir
/plugin install memoir
```

The SessionStart hook loads your startup files; the Stop hook reminds you
to run maintenance as the session closes. Point `MEMOIR_STORE` at your
memory directory.

### DeepSeek Harness

```
dsh plugin --profile web add github:Sevan7-Kalo10/memoir
```

That registers `/memoir-status`. The skill itself is discovered from the
filesystem, not from the package manifest (`dsh.skills` has no consumer in
current builds), so link it into a discovery root once:

```
ln -s "$DSH_HOME/profiles/web/node_modules/dsh-memoir" "$DSH_HOME/skills/memoir"
```

```powershell
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.dsh\skills\memoir" `
  -Target "$env:USERPROFILE\.dsh\profiles\web\node_modules\dsh-memoir"
```

Project-scoped alternative: link into `<project>/.dsh/skills/memoir`.

<details>
<summary>Manual install (no plugin system)</summary>

```
git clone https://github.com/Sevan7-Kalo10/memoir.git
```

Copy or symlink the repo directory to `~/.claude/skills/memoir/`.

</details>

## What it does

memoir splits memory into two layers by one question: **will this still
matter in six months?**

- **Hot layer** (`HOT-MEMORY.md`, ~2000 tokens): narrative of recent
  events, active projects, current behavioral rules. Updated at session
  close. Answers "what do I need to know when I wake up?"
- **Cold layer** (`memory/*.md`): permanent insights about the user —
  identity, values, preferences, patterns. The criterion is not "did we
  discuss this?" but "does this reveal who they are?"

Every memory carries two independent axes — **importance** (1-5) and
**recency** — plus a lifecycle state:

```
seedling → active → stable → fading → archived
               ↑                      |
               |______ restore _______|
```

The session-close workflow is the engine: update hot memory, scan the
conversation for permanent insights, run maintenance (decay, merge
proposals, archive candidates), audit gaps, back up. The agent proposes;
the user confirms.

Behavioral corrections ("don't do X", "from now on, Y") become structured
feedback files: incident → root cause → fix → how to apply. Always
importance 5.

## What v2.1 adds

- **`references/spec-migration.md`** — the v0.1.x → v2 frontmatter
  migration this repo had been linking to since 2.0.0 without the file
  existing. Field mapping plus the two gotchas that made old stores
  unmigratable: `metadata.type` is not `layer`, and file mtimes are
  bulk-write artifacts.
- **Wall-clock maintenance trigger** — a last-maintained date stamp beats
  session counting. A store can go months between sessions or have ten in
  a day.
- **DeepSeek Harness bundle** — same specs, one `/memoir-status` command.

## Commands

| Command | Purpose |
|---------|---------|
| `/memoir:init` | Bootstrap a memory directory with guided questions |
| `/memoir:status` | Health check: token budget, staleness, domain counts |
| `/memoir:remember <fact>` | Create a memory with guided frontmatter |
| `/memoir:digest` | Execute the session-close workflow |
| `/memoir:maintain` | Decay, merge, archive proposals |
| `/memoir:audit` | Gap analysis: topics vs stored memories |
| `/memoir:archive <file>` | Move a memory to archive |
| `/memoir:restore <file>` | Restore from archive |
| `/memoir:merge <f1> <f2>` | Merge two related memories |

On DeepSeek Harness the slash commands come from the skill text (the agent
reads SKILL.md); `/memoir-status` is also registered natively by the
bundle.

## Layout

| Path | Purpose |
|------|---------|
| `SKILL.md` | The skill itself: model, workflows, triggers |
| `references/` | Specs loaded on demand: model, ingestion, maintenance, migration, startup ritual |
| `templates/` | Blank hot memory, cold memory, feedback file, triggers |
| `hooks/` | Claude Code SessionStart / Stop hooks |
| `lib/index.js` | DeepSeek Harness bundle: `/memoir-status` |

## Design rationale

Why memoir is a skill and not a Python CLI, what went wrong with v0.1.x,
and where the patterns actually came from: [docs/design-rationale.md](docs/design-rationale.md).
