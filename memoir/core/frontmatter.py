"""YAML frontmatter parse/write for memoir memory files.

Handles the gate between memoir's data model and on-disk Markdown files.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ruamel.yaml import YAML

_yaml = YAML()
_yaml.indent(mapping=2, sequence=4, offset=2)
_yaml_safe = YAML(typ="safe")

_REQUIRED_FIELDS = {"name", "weight", "tags", "domain"}


def parse(filepath: str | Path) -> tuple[dict, str]:
    """Parse a memory file into (frontmatter_dict, body_text).

    Files without frontmatter return ({}, full_text).
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Memory file not found: {filepath}")

    text = filepath.read_text(encoding="utf-8")

    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    try:
        fm = _yaml_safe.load(parts[1])
        if not isinstance(fm, dict):
            return {}, text
    except Exception:
        return {}, text

    body = parts[2].lstrip("\n")
    return fm, body


def write(filepath: str | Path, frontmatter: dict, body: str) -> None:
    """Write a memory file with atomic replace + .bak backup."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    frontmatter["updated"] = datetime.now(timezone.utc).isoformat()

    stream = io.StringIO()
    _yaml.dump(frontmatter, stream)
    content = f"---\n{stream.getvalue()}---\n{body}"

    # Atomic write: tmpfile → os.replace
    tmp = filepath.with_suffix(filepath.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")

    # Create .bak if original exists
    if filepath.exists():
        bak = filepath.with_suffix(filepath.suffix + ".bak")
        filepath.replace(bak)

    tmp.replace(filepath)


def extract_tags(frontmatter: dict) -> list[str]:
    """Normalize and deduplicate tags from frontmatter."""
    tags = frontmatter.get("tags", [])
    if not isinstance(tags, list):
        return []
    seen = set()
    result = []
    for t in tags:
        t = str(t).strip().lower()
        if t and t not in seen:
            seen.add(t)
            result.append(t)
    return result


def validate(frontmatter: dict) -> list[str]:
    """Return list of validation errors. Empty list = valid."""
    errors = []
    for field in _REQUIRED_FIELDS:
        if field not in frontmatter:
            errors.append(f"missing required field: {field}")

    weight = frontmatter.get("weight")
    if weight is not None:
        if not isinstance(weight, int) or weight < 1 or weight > 5:
            errors.append(f"weight must be integer 1-5, got: {weight}")

    tags = frontmatter.get("tags")
    if tags is not None and not isinstance(tags, list):
        errors.append(f"tags must be a list, got: {type(tags).__name__}")

    return errors
