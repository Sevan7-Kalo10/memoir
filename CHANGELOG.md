# Changelog

## 0.1.5 (2026-05-22)

### Fixed
- **Windows cmd: `memoir create` no longer crashes.** Replaced `typer.confirm()`/`typer.prompt()` with plain `print()`+`input()` to bypass Rich's Win32 console GBK encoding issue. Added `--auto-append`/`-A` and `--skip-related`/`-S` flags for non-interactive use.
- **Non-memory .md files no longer scanned.** All scanners now skip `CLAUDE*`, `AI_*`, `README*` files. `domain` added to required frontmatter fields + `validate()` check in `status` command.
- **`--version` flag added.** `memoir --version` / `memoir -V` now works.

### Changed
- `--yes`/`-y` → `--auto-append`/`-A`, `--no`/`-n` → `--skip-related`/`-S`. Self-documenting names.
- Continue-prior score threshold back to ≥2 (file filtering is the real fix).

### Known issues
- tags don't auto-generate trigger rules
- Windows cmd Chinese args may truncate (use PowerShell or `-A`/`-S` flags)
- `.exe` output has encoding artifacts on Windows cmd (disk writes are correct)

## 0.1.4 (2026-05-21)

### Fixed
- `memoir create` now auto-updates MEMORY.md index via `_update_index()` helper
- `memoir restore` now warns that w=3 files are NOT auto-loaded, with fix instructions
- README rewritten with honest platform matrix and roadmap

## 0.1.3 (2026-05-21)

- CJK token estimation fix (6x under-estimate), regex pre-compilation, content caching
- INTEGRATION.md: manual + automatic Claude Code hooks
- 64 tests passing

## 0.1.2 (2026-05-21)

- FTS5 search index, Layer 2.5 fallback, `memoir index`/`memoir fts5-search` commands

## 0.1.0 / 0.1.1 (2026-05-20)

Initial release.
