# Changelog

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
