"""Memoir CLI — evolution-first memory management for AI agents."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from memoir.config import MemoirConfig
from memoir.core.frontmatter import parse, write, validate
from memoir.core.weight import apply_update, compute_decay, compute_boost, decay_schedule
from memoir.core.archive import archive as archive_file, restore as restore_file, scan_for_archive
from memoir.core.triggers import (
    load_triggers,
    load_domain_triggers,
    match_triggers,
    match_tables,
    cascade,
    TriggerRule,
    TriggerTable,
)
from memoir.core.loader import (
    build_load_plan,
    render_context,
    load_file_list,
)
from memoir.core.indexer import MemoirIndex, search as fts5_search

app = typer.Typer(name="memoir", help="Evolution-first memory framework")
console = Console()

WEIGHT_COLORS = {5: "green", 4: "blue", 3: "yellow", 2: "dark_orange", 1: "red"}


def _load_config(store_dir: str = ".") -> MemoirConfig:
    yaml_path = Path(store_dir) / "memoirs.yaml"
    if not yaml_path.exists():
        console.print("[red]Not a memoir store. Run 'memoir init' first.[/red]")
        raise typer.Exit(1)
    return MemoirConfig.from_yaml(yaml_path)


def _weight_tag(w: int) -> str:
    color = WEIGHT_COLORS.get(w, "white")
    return f"[{color}]w={w}[/{color}]"


# ── init ──────────────────────────────────────────────

@app.command()
def init(
    path: str = typer.Option(".", "--dir", help="Directory to initialize"),
    name: str = typer.Option("my-memoir", "--name", help="Store name"),
):
    """Create a new memoir store."""
    store = Path(path).resolve()
    store.mkdir(parents=True, exist_ok=True)

    if (store / "memoirs.yaml").exists():
        console.print("[yellow]memoirs.yaml already exists. Skipping init.[/yellow]")
        return

    config = MemoirConfig()
    config.to_yaml(store / "memoirs.yaml")

    # Directories
    (store / "core").mkdir(exist_ok=True)
    (store / "archive").mkdir(exist_ok=True)
    (store / "archive" / "INDEX.md").write_text(
        "# Archive Index\n\n(Empty — no memories archived yet.)\n", encoding="utf-8"
    )

    # Core index
    (store / "MEMORY.md").write_text(
        f"# {name}\n\n"
        "## Identity\n"
        "- [Who I Am](core/identity.md) — my core identity #identity\n\n"
        "## Trigger Table\n"
        "| #Concept | Keywords | → Files |\n"
        "|---|---|---|\n"
        "| identity | who am I, self | core/identity.md |\n",
        encoding="utf-8",
    )

    # Domain indexes
    (store / "MEMORY-philosophy.md").write_text(
        "# Philosophy Domain\n\n"
        "## Trigger Table\n"
        "| #Concept | Keywords | → Files |\n"
        "|---|---|---|\n",
        encoding="utf-8",
    )
    (store / "MEMORY-code.md").write_text(
        "# Code Domain\n\n"
        "## Trigger Table\n"
        "| #Concept | Keywords | → Files |\n"
        "|---|---|---|\n",
        encoding="utf-8",
    )

    # Triggers
    (store / "triggers.md").write_text(
        "# Behavior Triggers\n\n", encoding="utf-8"
    )

    # Starter memory
    (store / "core" / "identity.md").write_text(
        "---\n"
        "name: who-am-i\n"
        "weight: 5\n"
        "tags: [identity, core]\n"
        "domain: core\n"
        "description: Core identity\n"
        f"created: {datetime.now(timezone.utc).isoformat()}\n"
        "---\n"
        "# Who I Am\n\n"
        "Write your core identity here. This is weight 5 — it never decays.\n",
        encoding="utf-8",
    )

    console.print(f"[green]Created memoir store at {store}[/green]")
    console.print("  [bold]memoirs.yaml[/bold] — configuration")
    console.print("  [bold]MEMORY.md[/bold] — core index")
    console.print("  [bold]core/identity.md[/bold] — starter memory (w=5)")


# ── create ────────────────────────────────────────────

@app.command()
def create(
    title: str = typer.Option(..., "--title", "-t", help="Memory title"),
    domain: str = typer.Option("core", "--domain", "-d", help="Domain name"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
    weight: int = typer.Option(3, "--weight", "-w", help="Initial weight (1-5)"),
    content: str = typer.Option("", "--content", "-c", help="Memory content (or use $EDITOR)"),
    store_dir: str = typer.Option(".", "--store", help="Store root"),
):
    """Create a new memory. Greps for related files first (continue-prior)."""
    config = _load_config(store_dir)
    store = config.store_path

    # Continue-prior: grep for existing related files
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    related = _grep_related(store, title, tag_list)

    if related:
        console.print("[yellow]Related files found:[/yellow]")
        for r in related:
            console.print(f"  • {r}")
        if not typer.confirm("Continue in existing file instead?"):
            pass  # User wants a new file
        else:
            if len(related) == 1:
                append(related[0], content=content, store_dir=store_dir)
            else:
                choice = typer.prompt("Which file?", default=related[0])
                append(choice, content=content, store_dir=store_dir)
            return

    # Get content
    if not content:
        content = _editor_input(title)

    if not content.strip():
        console.print("[red]Empty content, aborting.[/red]")
        raise typer.Exit(1)

    # Slugify title
    slug = title.lower().replace(" ", "-").replace("/", "-")
    filename = f"{slug}.md"
    filepath = store / domain / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if filepath.exists():
        console.print(f"[yellow]{filename} already exists. Use 'memoir append'.[/yellow]")
        raise typer.Exit(1)

    frontmatter = {
        "name": slug,
        "weight": weight,
        "tags": tag_list,
        "domain": domain,
        "description": title,
        "created": datetime.now(timezone.utc).isoformat(),
    }

    write(filepath, frontmatter, content.strip())
    console.print(f"[green]Created {domain}/{filename} ({_weight_tag(weight)})[/green]")


# ── append ────────────────────────────────────────────

@app.command()
def append(
    filename: str = typer.Argument(..., help="File to append to (e.g. core/identity.md)"),
    content: str = typer.Option("", "--content", "-c", help="Content to append"),
    store_dir: str = typer.Option(".", "--store", help="Store root"),
):
    """Append a timestamped entry to an existing memory file."""
    store = Path(store_dir)
    filepath = store / filename

    if not filepath.exists():
        console.print(f"[red]File not found: {filename}[/red]")
        raise typer.Exit(1)

    if not content:
        content = _editor_input(f"Append to {filename}")

    if not content.strip():
        console.print("[red]Empty content, aborting.[/red]")
        raise typer.Exit(1)

    fm, body = parse(filepath)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {ts}\n{content.strip()}\n"
    write(filepath, fm, body + entry)

    console.print(f"[green]Appended to {filename}[/green]")


# ── search ────────────────────────────────────────────

@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    domain: str = typer.Option("", "--domain", "-d", help="Filter by domain"),
    tags: str = typer.Option("", "--tags", help="Filter by tags (comma-separated)"),
    store_dir: str = typer.Option(".", "--store", help="Store root"),
    max_results: int = typer.Option(20, "--max", "-n", help="Max results"),
):
    """Full-text search across memory files. Uses FTS5 when index is available."""
    config = _load_config(store_dir)
    store = config.store_path

    # Prefer FTS5 if index exists, fall back to grep
    idx = MemoirIndex(store)
    if not idx.needs_rebuild():
        results = idx.search(query, limit=max_results)
        rows = []
        for r in results:
            rows.append({
                "file": r["relpath"],
                "weight": r["weight"],
                "snippet": r["snippet"][:80],
            })
    else:
        tag_str = tags or ""
        rows = _grep_store(store, query, domain, tag_str, max_results)

    if not rows:
        console.print("[dim]No matches found.[/dim]")
        return

    table = Table(title=f"Search: \"{query}\"")
    table.add_column("File", style="cyan")
    table.add_column("Weight")
    table.add_column("Snippet")

    for r in rows:
        table.add_row(r["file"], _weight_tag(r["weight"]), r["snippet"][:80])

    console.print(table)


# ── index ─────────────────────────────────────────────

@app.command()
def index(
    store_dir: str = typer.Option(".", "--store", help="Store root"),
    force: bool = typer.Option(False, "--force", "-f", help="Force rebuild"),
):
    """Build or rebuild the FTS5 search index."""
    config = _load_config(store_dir)
    store = config.store_path

    idx = MemoirIndex(store)
    if force:
        count = idx.build()
        console.print(f"[green]Index rebuilt: {count} files indexed.[/green]")
    elif idx.needs_rebuild():
        with console.status("Building FTS5 index..."):
            count = idx.build()
        console.print(f"[green]Index built: {count} files indexed.[/green]")
    else:
        console.print("[dim]Index is up to date.[/dim]")


@app.command()
def fts5_search(
    query: str = typer.Argument(..., help="Search query"),
    store_dir: str = typer.Option(".", "--store", help="Store root"),
    weight_min: int = typer.Option(1, "--weight-min", help="Minimum weight"),
    weight_max: int = typer.Option(5, "--weight-max", help="Maximum weight"),
    tags: str = typer.Option("", "--tags", help="Filter by tags (comma-separated)"),
    max_results: int = typer.Option(20, "--max", "-n", help="Max results"),
):
    """FTS5 full-text search with weight/tag filters."""
    config = _load_config(store_dir)
    store = config.store_path

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] or None

    idx = MemoirIndex(store)
    idx.auto()

    results = idx.search(
        query,
        weight_min=weight_min,
        weight_max=weight_max,
        tags=tag_list,
        limit=max_results,
    )

    if not results:
        console.print("[dim]No matches found.[/dim]")
        return

    table = Table(title=f"FTS5 Search: \"{query}\"")
    table.add_column("File", style="cyan")
    table.add_column("Weight")
    table.add_column("Snippet")

    for r in results:
        table.add_row(
            r["relpath"],
            _weight_tag(r["weight"]),
            r["snippet"][:80],
        )

    console.print(table)


# ── trigger ───────────────────────────────────────────

@app.command()
def trigger(
    text: str = typer.Argument(..., help="Text to match triggers against"),
    store_dir: str = typer.Option(".", "--store", help="Store root"),
):
    """Debug trigger matching — see what fires when."""
    config = _load_config(store_dir)
    store = config.store_path

    # Load all triggers
    tf = store / config.store.trigger_file
    rules = load_triggers(tf)

    all_tables: list[TriggerTable] = []
    domain_files: dict[str, list[str]] = {}
    for domain in config.domains:
        index_path = store / domain.index
        all_tables.extend(load_domain_triggers(index_path))
        domain_files[domain.name] = load_file_list(index_path)

    # Match
    matched_rules = match_triggers(text, rules)
    matched_tables = match_tables(text, all_tables)

    console.print(f"\n[bold]Input:[/bold] \"{text}\"\n")

    if matched_rules:
        console.print("[bold]Matched Rules (triggers.md):[/bold]")
        for r in matched_rules:
            console.print(f"  {r.phrases[0]} → [cyan]{r.action}[/cyan]")
    else:
        console.print("[dim]No trigger rules matched.[/dim]")

    if matched_tables:
        console.print("\n[bold]Matched Concepts (domain trigger tables):[/bold]")
        for t in matched_tables:
            console.print(f"  [yellow]#{t.concept}[/yellow] → {', '.join(t.target_files)}")
    else:
        console.print("[dim]No domain trigger tables matched.[/dim]")

    # Cascade
    triggered = cascade(matched_rules, matched_tables, index_files=domain_files)
    if triggered:
        console.print("\n[bold]Files that would load:[/bold]")
        for f in triggered:
            console.print(f"  • {f}")


# ── load ──────────────────────────────────────────────

@app.command()
def load(
    topics: str = typer.Option("", "--topics", help="Active topics (comma-separated)"),
    trigger_text: str = typer.Option("", "--trigger", "-t", help="Trigger input text"),
    store_dir: str = typer.Option(".", "--store", help="Store root"),
    render: bool = typer.Option(False, "--render", "-r", help="Render full context"),
):
    """Preview the loading plan for given conversation context."""
    config = _load_config(store_dir)
    store = config.store_path

    active_domains = [t.strip() for t in topics.split(",") if t.strip()]
    text = trigger_text or " ".join(active_domains)

    plan = build_load_plan(
        store, config,
        conversation_text=text,
        active_domains=active_domains,
    )

    table = Table(title="Load Plan")
    table.add_column("Layer", style="bold")
    table.add_column("File")
    table.add_column("Weight")

    for f, w, s in zip(plan.files, plan.weights, plan.sources):
        table.add_row(s, f, _weight_tag(w))

    console.print(table)
    console.print(f"[dim]Total: {len(plan.files)} files, ~{plan.total_tokens_estimate} tokens[/dim]")

    if render:
        console.print("\n" + render_context(plan, store))


# ── maintain ──────────────────────────────────────────

@app.command()
def maintain(
    store_dir: str = typer.Option(".", "--store", help="Store root"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only, no changes"),
):
    """Run weight decay scan and archive eligible files."""
    config = _load_config(store_dir)
    store = config.store_path

    console.print("[bold]Weight Decay Check:[/bold]")
    schedule = decay_schedule(config)
    changes = []

    for md_file in store.rglob("*.md"):
        if "archive" in md_file.parts:
            continue
        if md_file.name.startswith("MEMORY") or md_file.name == config.store.trigger_file:
            continue

        try:
            fm, _ = parse(md_file)
        except Exception:
            continue

        if validate(fm):
            continue

        result = compute_decay(fm, schedule=schedule)
        if result is not None:
            old_w = fm.get("weight", "?")
            rel = str(md_file.relative_to(store)).replace("\\", "/")
            if result == "archive":
                changes.append((rel, old_w, "archive"))
            else:
                changes.append((rel, old_w, result))

    if changes:
        table = Table()
        table.add_column("File")
        table.add_column("From")
        table.add_column("To")
        for rel, old, new in changes:
            table.add_row(rel, _weight_tag(old) if isinstance(old, int) else str(old),
                          _weight_tag(new) if isinstance(new, int) else str(new))
        console.print(table)

        if not dry_run:
            for rel, old, new in changes:
                filepath = store / rel
                if new == "archive":
                    archive_file(
                        filepath,
                        store / config.store.archive_dir,
                        store / config.evolution.archive_index,
                    )
                    console.print(f"[yellow]Archived:[/yellow] {rel}")
                else:
                    apply_update(filepath, new, note="auto-decay")
                    console.print(f"[dim]Weight:[/dim] {rel} {old} → {new}")
    else:
        console.print("[dim]No weight changes needed.[/dim]")

    # Archive scan
    console.print("\n[bold]Archive Scan:[/bold]")
    archive_results = scan_for_archive(store, config, dry_run=dry_run)
    if archive_results:
        for r in archive_results:
            console.print(f"[yellow]Would archive:[/yellow] {r['file']}" if dry_run else
                          f"[yellow]Archived:[/yellow] {r['file']} → {r['archived_to']}")
    else:
        console.print("[dim]No files eligible for archive.[/dim]")


# ── archive ───────────────────────────────────────────

@app.command()
def archive_cmd(
    filename: str = typer.Argument(..., help="File to archive (e.g. core/old.md)"),
    store_dir: str = typer.Option(".", "--store", help="Store root"),
):
    """Manually archive a memory file."""
    config = _load_config(store_dir)
    store = config.store_path

    src = store / filename
    if not src.exists():
        console.print(f"[red]File not found: {filename}[/red]")
        raise typer.Exit(1)

    archive_file(src, store / config.store.archive_dir, store / config.evolution.archive_index)
    console.print(f"[yellow]Archived:[/yellow] {filename}")


@app.command()
def restore(
    filename: str = typer.Argument(..., help="File to restore (just the filename)"),
    domain: str = typer.Option("core", "--domain", "-d", help="Target domain"),
    store_dir: str = typer.Option(".", "--store", help="Store root"),
):
    """Restore a memory from the archive."""
    config = _load_config(store_dir)
    store = config.store_path

    restored = restore_file(
        filename,
        store / config.store.archive_dir,
        store / domain,
        store / config.evolution.archive_index,
    )
    console.print(f"[green]Restored:[/green] {restored} → {domain}/ (w=3)")


@app.command()
def archive_list(
    store_dir: str = typer.Option(".", "--store", help="Store root"),
):
    """List archived memories."""
    config = _load_config(store_dir)
    store = config.store_path

    idx = store / config.evolution.archive_index
    if not idx.exists():
        console.print("[dim]No archive index found.[/dim]")
        return

    content = idx.read_text(encoding="utf-8")
    console.print(Panel(content.strip(), title="Archive Index"))


# ── status ────────────────────────────────────────────

@app.command()
def status(
    store_dir: str = typer.Option(".", "--store", help="Store root"),
):
    """Show store statistics."""
    config = _load_config(store_dir)
    store = config.store_path

    total = 0
    weight_dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    domain_dist: dict[str, int] = {}

    for md_file in store.rglob("*.md"):
        if "archive" in md_file.parts:
            continue
        if md_file.name.startswith("MEMORY") or md_file.name == config.store.trigger_file:
            continue

        try:
            fm, _ = parse(md_file)
        except Exception:
            continue

        total += 1
        w = fm.get("weight", 3)
        weight_dist[w] = weight_dist.get(w, 0) + 1

        d = fm.get("domain", "unknown")
        domain_dist[d] = domain_dist.get(d, 0) + 1

    table = Table(title="Memoir Store Status")
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Total memories", str(total))
    table.add_row("Domains", ", ".join(domain_dist.keys()))

    parts = []
    for w, c in sorted(weight_dist.items()):
        if c > 0:
            color = WEIGHT_COLORS.get(w, "white")
            parts.append(f"[{color}]w={w}: {c}[/{color}]")
    weight_str = "  ".join(parts)
    table.add_row("Weight distribution", weight_str)

    # Archive count
    archive_idx = store / config.evolution.archive_index
    archive_count = 0
    if archive_idx.exists():
        archive_count = sum(
            1 for line in archive_idx.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("- [") and not line.strip().startswith("~~")
        )
    table.add_row("Archived", str(archive_count))

    console.print(table)


# ── helpers ───────────────────────────────────────────

def _editor_input(prompt: str = "") -> str:
    """Open $EDITOR for content input. Falls back to plain input."""
    editor = (
        os.environ.get("EDITOR")
        or os.environ.get("VISUAL")
        or "notepad" if sys.platform == "win32" else "nano"
    )
    tmp = Path.home() / ".memoir_tmp.md"
    tmp.write_text(f"# {prompt}\n\n", encoding="utf-8")

    try:
        subprocess.call([editor, str(tmp)])
    except Exception:
        tmp.unlink(missing_ok=True)
        return typer.edit() or ""

    content = tmp.read_text(encoding="utf-8")
    # Remove the prompt line
    if content.startswith(f"# {prompt}"):
        content = content[len(f"# {prompt}"):].strip()
    tmp.unlink(missing_ok=True)
    return content


def _grep_related(store: Path, title: str, tags: list[str]) -> list[str]:
    """Grep store for files related to the given title/tags."""
    related = []
    keywords = title.lower().split()
    for md_file in store.rglob("*.md"):
        if "archive" in md_file.parts:
            continue
        if md_file.name.startswith("MEMORY") or md_file.name == "triggers.md":
            continue
        try:
            text = md_file.read_text(encoding="utf-8").lower()
        except Exception:
            continue
        score = 0
        for kw in keywords:
            if kw in text:
                score += 1
        for tag in tags:
            if tag in text:
                score += 2
        if score >= 2:
            related.append(str(md_file.relative_to(store)).replace("\\", "/"))
    return related[:5]


def _grep_store(
    store: Path, query: str, domain: str, tags: str, max_results: int
) -> list[dict]:
    """Search memory files for query string."""
    results = []
    query_lower = query.lower()
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
    domain_filter = domain.strip() if domain else ""

    for md_file in store.rglob("*.md"):
        if "archive" in md_file.parts:
            continue
        if md_file.name.startswith("MEMORY") or md_file.name == "triggers.md":
            continue

        try:
            fm, body = parse(md_file)
        except Exception:
            continue

        if domain_filter and fm.get("domain") != domain_filter:
            continue
        if tag_list:
            file_tags = [t.lower() for t in fm.get("tags", [])]
            if not any(t in file_tags for t in tag_list):
                continue

        body_lower = body.lower()
        if query_lower in body_lower:
            idx = body_lower.index(query_lower)
            start = max(0, idx - 40)
            end = min(len(body), idx + len(query) + 40)
            snippet = body[start:end].replace("\n", " ")
            if start > 0:
                snippet = "…" + snippet
            if end < len(body):
                snippet += "…"
            rel = str(md_file.relative_to(store)).replace("\\", "/")
            results.append({
                "file": rel,
                "weight": fm.get("weight", 3),
                "snippet": snippet,
            })

        if len(results) >= max_results:
            break

    return results


def main():
    app()


if __name__ == "__main__":
    main()
