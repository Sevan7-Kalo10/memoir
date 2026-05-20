"""Trigger cascade engine — the key differentiator of memoir.

Not vector search, not keyword grep — curated conceptual association.
When a topic slides into conversation, related domains light up on their own
through manually curated concept-to-memory mappings.

Match modes: exact (substring), stem (word-stem), phrase (multi-word),
regex (full regex), fuzzy (rapidfuzz ratio >= threshold).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from rapidfuzz import fuzz


@dataclass
class TriggerRule:
    phrases: list[str]
    action: str  # "load-domain:<name>" | "load-file:<path>" | "callback:<name>"
    source_file: str  # [[wikilink]]
    match_mode: str = "stem"  # exact | stem | phrase | regex | fuzzy

    def match(self, text: str, threshold: float = 0.82) -> bool:
        """Return True if this rule matches the given text."""
        text_lower = text.lower()
        for phrase in self.phrases:
            phrase_lower = phrase.lower()
            if self.match_mode == "exact":
                if phrase_lower in text_lower:
                    return True
            elif self.match_mode == "phrase":
                # Phrase must appear as contiguous substring
                if phrase_lower in text_lower:
                    return True
            elif self.match_mode == "regex":
                try:
                    if re.search(phrase, text, re.IGNORECASE):
                        return True
                except re.error:
                    continue
            elif self.match_mode == "fuzzy":
                # Use token_sort_ratio for fuzzy matching against text
                if fuzz.partial_ratio(phrase_lower, text_lower) >= threshold * 100:
                    return True
            else:  # stem (default)
                # Each word in phrase must appear as substring in text
                words = phrase_lower.split()
                if all(w in text_lower for w in words):
                    return True
        return False


@dataclass
class TriggerTable:
    """Represents a trigger table extracted from a domain index file."""
    concept: str
    keywords: list[str]
    target_files: list[str]
    source_index: str = ""


def load_triggers(trigger_file: str | Path) -> list[TriggerRule]:
    """Parse triggers.md into structured TriggerRule objects.

    Format per line:
        trigger_phrase → action → source_memory

    Empty lines and lines starting with # are ignored.
    """
    trigger_file = Path(trigger_file)
    if not trigger_file.exists():
        return []

    rules = []
    for line in trigger_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Parse: phrase → action → source
        parts = [p.strip() for p in line.split("→")]
        if len(parts) < 3:
            continue

        phrase = parts[0]
        action = parts[1]
        source = parts[2].strip("[]")

        # Determine match mode
        mode = "stem"
        if phrase.startswith("/") and phrase.endswith("/"):
            mode = "regex"
            phrase = phrase[1:-1]
        elif phrase.startswith("~"):
            mode = "fuzzy"
            phrase = phrase[1:]
        elif " " in phrase:
            mode = "phrase"

        rules.append(TriggerRule(
            phrases=[phrase],
            action=action,
            source_file=source,
            match_mode=mode,
        ))

    return rules


def load_domain_triggers(index_file: str | Path) -> list[TriggerTable]:
    """Extract trigger tables from a domain index file (MEMORY-<domain>.md).

    Tables are markdown tables with columns: #Concept | Keywords | → Files
    """
    index_file = Path(index_file)
    if not index_file.exists():
        return []

    tables = []
    in_table = False
    headers_found = False

    for line in index_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        # Detect table start: lines with | #Concept | Keywords | → Files |
        if "|" in line and ("concept" in line.lower() or "#concept" in line.lower()):
            in_table = True
            headers_found = False
            continue

        # Skip separator line
        if in_table and "---" in line:
            headers_found = True
            continue

        # Parse table row
        if in_table and headers_found and line.startswith("|"):
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if len(cells) >= 3:
                concept = cells[0].lstrip("#").strip()
                keywords = [kw.strip() for kw in cells[1].replace(",", " ").split() if kw.strip()]
                target_files = [f.strip() for f in cells[2].replace(",", " ").split() if f.strip()]
                tables.append(TriggerTable(
                    concept=concept,
                    keywords=keywords,
                    target_files=target_files,
                    source_index=str(index_file),
                ))

        # Detect table end (empty line after table)
        if in_table and not line:
            in_table = False
            headers_found = False

    return tables


def match_triggers(
    text: str,
    rules: list[TriggerRule],
    *,
    threshold: float = 0.82,
) -> list[TriggerRule]:
    """Run input text against all rules. Returns matched rules."""
    matched = []
    for rule in rules:
        if rule.match(text, threshold=threshold):
            matched.append(rule)
    return matched


def match_tables(
    text: str,
    tables: list[TriggerTable],
) -> list[TriggerTable]:
    """Match input text against trigger tables. Returns matched tables."""
    text_lower = text.lower()
    matched = []
    for table in tables:
        for keyword in table.keywords:
            if keyword.lower() in text_lower:
                matched.append(table)
                break
    return matched


def cascade(
    rules: list[TriggerRule],
    tables: list[TriggerTable],
    *,
    index_files: dict[str, list[str]] | None = None,
) -> list[str]:
    """Resolve triggered rules and tables into a set of file paths to load.

    "load-domain:<name>" → all files in that domain's index
    "load-file:<path>" → specific file
    Other actions (callback, remind) are returned as-is for the caller.
    """
    files: set[str] = set()

    # From trigger rules
    for rule in rules:
        if rule.action.startswith("load-file:"):
            files.add(rule.action.split(":", 1)[1])
        elif rule.action.startswith("load-domain:") and index_files:
            domain = rule.action.split(":", 1)[1]
            for f in index_files.get(domain, []):
                files.add(f)

    # From trigger tables
    for table in tables:
        for f in table.target_files:
            files.add(f)

    return list(files)
