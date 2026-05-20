"""Four-layer loading engine.

Determines what memories to surface for a given conversation context.

Layer 1: Always — core domain files + w=5
Layer 2: Trigger Cascade — matched trigger rules → files
Layer 3: Domain — active domain index files
Layer 4: Weight — w=4 files loaded proactively, w=3 on domain match

Token budget trimming: remove w=3 first, then w=4. Never trim w=5 or always-load.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from memoir.config import MemoirConfig
from memoir.core.frontmatter import parse
from memoir.core.triggers import (
    TriggerRule,
    TriggerTable,
    load_triggers,
    load_domain_triggers,
    match_triggers,
    match_tables,
    cascade,
)


@dataclass
class LoadPlan:
    files: list[str] = field(default_factory=list)
    weights: list[int] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)  # "always", "trigger", "domain", "weight"
    total_tokens_estimate: int = 0


def _norm(path: str) -> str:
    """Normalize path to forward slashes for deduplication."""
    return path.replace("\\", "/")


def load_file_list(index_file: str | Path) -> list[str]:
    """Parse an index file and return the list of referenced .md files.

    Lines like: - [Title](path/file.md) — description #tags
    """
    index_file = Path(index_file)
    if not index_file.exists():
        return []

    files = []
    for line in index_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "](" not in line:
            continue
        start = line.index("](") + 2
        end = line.index(")", start)
        path = _norm(line[start:end])
        if path.endswith(".md"):
            files.append(path)

    return files


def estimate_tokens(text: str) -> int:
    """Rough token estimate: words * 1.3. Conservative."""
    words = len(text.split())
    return int(words * 1.3)


def build_load_plan(
    store_path: str | Path,
    config: MemoirConfig,
    *,
    conversation_text: str = "",
    active_domains: list[str] | None = None,
    max_tokens: int | None = None,
) -> LoadPlan:
    """Build a four-layer loading plan for the given context.

    Args:
        store_path: Root of the memoir store
        config: MemoirConfig instance
        conversation_text: Recent conversation to match triggers against
        active_domains: Domains currently active (beyond always_load)
        max_tokens: Override config's max_tokens

    Returns:
        LoadPlan with deduplicated file list and token estimate
    """
    store_path = Path(store_path)
    max_tokens = max_tokens or config.loading.max_tokens
    active_domains = active_domains or []

    plan = LoadPlan()
    seen: set[str] = set()

    def add_file(path: str, source: str, weight: int = 3):
        if path not in seen:
            seen.add(path)
            plan.files.append(path)
            plan.weights.append(weight)
            plan.sources.append(source)

    # Parse triggers upfront
    trigger_file = store_path / config.store.trigger_file
    trigger_rules = load_triggers(trigger_file)
    matched_rules = match_triggers(conversation_text, trigger_rules) if conversation_text else []

    # Collect all domain trigger tables
    all_tables: list[TriggerTable] = []
    for domain in config.domains:
        index_path = store_path / domain.index
        all_tables.extend(load_domain_triggers(index_path))
    matched_tables = match_tables(conversation_text, all_tables) if conversation_text else []

    # Build domain file lookup for cascade
    domain_files: dict[str, list[str]] = {}
    for domain in config.domains:
        index_path = store_path / domain.index
        domain_files[domain.name] = load_file_list(index_path)

    triggered_files = cascade(matched_rules, matched_tables, index_files=domain_files)

    # ── Layer 1: Always ──
    for domain in config.always_load_domains:
        index_path = store_path / domain.index
        for f in load_file_list(index_path):
            add_file(f, "always", weight=5)

    # ── Layer 2: Trigger Cascade ──
    for f in triggered_files:
        add_file(f, "trigger", weight=4)

    # ── Layer 3: Domain ──
    for domain_name in active_domains:
        domain = config.get_domain(domain_name)
        if domain:
            index_path = store_path / domain.index
            for f in load_file_list(index_path):
                add_file(f, "domain", weight=3)

    # ── Layer 4: Weight ──
    for md_file in store_path.rglob("*.md"):
        if "archive" in md_file.parts:
            continue
        if md_file.name.startswith("MEMORY") or md_file.name == config.store.trigger_file:
            continue

        try:
            rel = _norm(str(md_file.relative_to(store_path)))
        except ValueError:
            continue

        if rel in seen:
            continue

        try:
            fm, _ = parse(md_file)
        except Exception:
            continue

        w = fm.get("weight", 3)
        if w >= 4:
            add_file(rel, "weight", weight=w)

    # ── Token budget ──
    plan.total_tokens_estimate = 0
    for f in plan.files:
        filepath = store_path / f
        if filepath.exists():
            plan.total_tokens_estimate += estimate_tokens(
                filepath.read_text(encoding="utf-8")
            )

    if plan.total_tokens_estimate > max_tokens:
        trim_order = config.loading.trim_order
        # Remove files by weight, lowest trim_order first
        for trim_weight in trim_order:
            if plan.total_tokens_estimate <= max_tokens:
                break
            _trim_weight(plan, store_path, trim_weight)

    return plan


def _trim_weight(plan: LoadPlan, store_path: Path, weight: int) -> None:
    """Remove files of given weight from the plan to reduce tokens."""
    i = 0
    while i < len(plan.files) and plan.total_tokens_estimate > 0:
        if plan.weights[i] == weight and plan.sources[i] != "always":
            filepath = store_path / plan.files[i]
            if filepath.exists():
                plan.total_tokens_estimate -= estimate_tokens(
                    filepath.read_text(encoding="utf-8")
                )
            plan.files.pop(i)
            plan.weights.pop(i)
            plan.sources.pop(i)
        else:
            i += 1


def render_context(plan: LoadPlan, store_path: str | Path) -> str:
    """Concatenate all files in the load plan into a single context string.

    Each file prefixed with a header: ## [Title](filepath) — weight: N
    """
    store_path = Path(store_path)
    parts = []

    for f, weight in zip(plan.files, plan.weights):
        filepath = store_path / f
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        parts.append(f"## [{f}]({f}) — weight: {weight}\n\n{content}")

    return "\n\n---\n\n".join(parts)
