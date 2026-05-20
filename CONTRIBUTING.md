# Contributing to memoir

## What to contribute

- **Bug reports** — open an issue
- **Implementations in other languages** — the spec is language-agnostic. Read [specs/MEMOIR-SPEC.md](specs/MEMOIR-SPEC.md) and build a conformant implementation in TypeScript, Go, Rust, etc.
- **Core improvements** — spec changes, new features, perf improvements
- **Documentation** — tutorials, examples, use cases

## Development

```bash
git clone https://github.com/ksteam/memoir
cd memoir
pip install -e ".[dev]"
pytest
```

## Spec-first development

The memoire spec is the contract. Before writing code:

1. Check if your change requires a spec update
2. Update `specs/MEMOIR-SPEC.md` first
3. Implement against the spec
4. The implementor's checklist in the spec is the acceptance criteria

## Tests

- Every `core/` module must have tests
- Pure functions are preferred (testable without filesystem)
- Run `pytest --cov=memoir` before submitting

## Code style

- No comments that explain WHAT — the code should do that
- Comments for WHY — the non-obvious reason
- Prefer stdlib over dependencies
