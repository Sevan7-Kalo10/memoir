"""Archive and restoration of dormant memories.

Archiving is soft-delete: files move to archive/ with an audit trail.
Nothing is ever destroyed.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from memoir.core.frontmatter import parse, write


def _ensure_archive_index(index_path: str | Path) -> Path:
    index_path = Path(index_path)
    if not index_path.exists():
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text("# Archive Index\n\n", encoding="utf-8")
    return index_path


def archive(
    filepath: str | Path,
    archive_dir: str | Path,
    archive_index: str | Path,
) -> str:
    """Move file to archive_dir, append entry to archive index.

    Handles name collisions with timestamp suffix.
    Returns new path relative to store root.
    """
    filepath = Path(filepath)
    archive_dir = Path(archive_dir)
    archive_index = _ensure_archive_index(archive_index)

    archive_dir.mkdir(parents=True, exist_ok=True)

    # Parse for metadata before moving
    fm, _ = parse(filepath)
    weight = fm.get("weight", 1)
    last_triggered = fm.get("last_triggered", "unknown")

    # Handle collision
    dest = archive_dir / filepath.name
    if dest.exists():
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        dest = archive_dir / f"{filepath.stem}-{ts}{filepath.suffix}"

    shutil.move(str(filepath), str(dest))

    # Append to archive index
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = (
        f"- [{dest.name}]({dest.name})"
        f" — archived {now}, w={weight}, last active {last_triggered}\n"
    )
    with open(archive_index, "a", encoding="utf-8") as f:
        f.write(entry)

    return str(dest)


def restore(
    filename: str,
    archive_dir: str | Path,
    target_dir: str | Path,
    archive_index: str | Path,
) -> str:
    """Move file back from archive to target_dir.

    Strikes through archive index entry (does not delete).
    Resets weight to 3 (neutral re-entry).
    Returns restored file path.
    """
    archive_dir = Path(archive_dir)
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    src = archive_dir / filename
    if not src.exists():
        raise FileNotFoundError(f"Archived file not found: {src}")

    # Reset weight to 3
    fm, body = parse(src)
    fm["weight"] = 3
    fm["restored_at"] = datetime.now(timezone.utc).isoformat()
    write(src, fm, body)

    dest = target_dir / filename
    shutil.move(str(src), str(dest))

    # Strike through in archive index
    _strikethrough_index_entry(archive_index, filename)

    return str(dest)


def _strikethrough_index_entry(index_path: str | Path, filename: str) -> None:
    index_path = Path(index_path)
    if not index_path.exists():
        return
    lines = index_path.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        if filename in line and line.strip().startswith("- ["):
            new_lines.append(f"~~{line}~~")
        else:
            new_lines.append(line)
    index_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def list_archived(archive_index: str | Path) -> list[dict]:
    """Parse archive INDEX.md into structured entries."""
    index_path = Path(archive_index)
    if not index_path.exists():
        return []
    entries = []
    for line in index_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("- [") and not line.startswith("~~"):
            entries.append({"line": line})
    return entries


def scan_for_archive(
    memory_dir: str | Path,
    config,  # MemoirConfig
    *,
    dry_run: bool = False,
) -> list[dict]:
    """Walk memory_dir, find files eligible for archive.

    Criteria: weight=1, last_triggered older than decay threshold,
    no inbound [[wikilink]] from w≥3 files.
    """
    from memoir.core.weight import compute_decay, decay_schedule
    from memoir.core.frontmatter import validate

    memory_dir = Path(memory_dir)
    archive_dir = memory_dir / config.store.archive_dir
    archive_index = memory_dir / config.evolution.archive_index
    schedule = decay_schedule(config)
    results = []

    for md_file in memory_dir.rglob("*.md"):
        if "archive" in md_file.parts:
            continue
        if md_file.name.startswith("MEMORY") or md_file.name == "triggers.md":
            continue

        try:
            fm, _ = parse(md_file)
        except Exception:
            continue

        if validate(fm):
            continue

        result = compute_decay(fm, schedule=schedule)
        if result == "archive":
            if not dry_run:
                new_path = archive(md_file, archive_dir, archive_index)
            else:
                new_path = str(archive_dir / md_file.name)
            results.append({
                "file": str(md_file),
                "archived_to": new_path,
                "weight": fm.get("weight"),
                "last_triggered": fm.get("last_triggered", "unknown"),
            })

    return results
