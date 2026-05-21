# Changelog

## 0.1.4 (2026-05-21)

- **Auto-update index on create**: `memoir create` now appends entry to domain MEMORY.md automatically
- **Restore weight warning**: `memoir restore` warns that restored files (w=3) are not auto-loaded
- **README rewrite**: honest platform support matrix, known limitations, roadmap, competitor comparison

## 0.1.3 (2026-05-21)

- **CJK token estimation**: `estimate_tokens` now counts CJK characters (~1.5 tokens/char). Chinese text was under-estimated by 6x.
- **Regex pre-compilation**: `TriggerRule` compiles regex once at load time
- **Content caching**: `LoadPlan._content_cache` eliminates duplicate file I/O
- **Integration guide** (`INTEGRATION.md`): manual + automatic Claude Code hooks injection
- 64 tests passing

## 0.1.2 (2026-05-21)

- **FTS5 search index** (`memoir.core.indexer`): full-text search with BM25 ranking, weight-range filtering, and tag intersection. Zero extra dependencies (sqlite3 stdlib).
- **Layer 2.5 FTS5 fallback** in loader: when keyword triggers miss, FTS5 catches semantically related files
- **CLI additions**: `memoir index`, `memoir fts5-search`
- Enhanced `memoir search`: automatically uses FTS5 when index is available
- Fixed: spec incorrectly stated "May 2025" → corrected to May 2026
- 64 tests (7 new for indexer)

## 0.1.0 (2026-05-20)

Initial release.

- Language-agnostic specification (`specs/MEMOIR-SPEC.md`)
- Python reference implementation:
  - `frontmatter` — YAML frontmatter parse/write with atomic ops
  - `weight` — weight lifecycle with active judgment, time decay, and trigger boost
  - `archive` — soft-delete archive with index tracking and restoration
  - `triggers` — trigger cascade engine with 5 match modes
  - `loader` — four-layer loading algorithm with token budget
- CLI (9 commands): init, create, append, search, trigger, load, maintain, archive, status
- Demo memory store with example persona
- 57 tests
