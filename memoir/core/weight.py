"""Weight lifecycle — the heartbeat of memoir.

Active judgment is PRIMARY. Time decay is AUXILIARY — a safety net
for forgotten memories, not the main driver of weight changes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from memoir.config import MemoirConfig
from memoir.core.frontmatter import parse, write


def decay_schedule(config: MemoirConfig) -> dict[int, tuple[int | None, str | None]]:
    """Return mapping: weight → (days_untouched, action_or_new_weight).

    None days = never decays. String action = "archive".
    Integer to = new weight.
    """
    schedule = {}
    for w_str, rule in config.weight.decay.items():
        w = int(w_str) if isinstance(w_str, str) else w_str
        if rule.days is None:
            schedule[w] = (None, None)
        elif rule.action == "archive":
            schedule[w] = (rule.days, "archive")
        else:
            schedule[w] = (rule.days, rule.to)
    return schedule


def compute_decay(
    frontmatter: dict,
    now: datetime | None = None,
    schedule: dict | None = None,
    config: MemoirConfig | None = None,
) -> int | None | str:
    """Return new weight (or "archive") if decay is needed, None if no change.

    Pure function — does not touch disk.
    """
    if schedule is None and config is not None:
        schedule = decay_schedule(config)
    if schedule is None:
        return None

    now = now or datetime.now(timezone.utc)
    weight = frontmatter.get("weight", 3)
    if weight not in schedule:
        return None

    days_threshold, action = schedule[weight]
    if days_threshold is None:
        return None  # Never decays (w=5)

    last_active_str = frontmatter.get("last_triggered") or frontmatter.get("updated")
    if not last_active_str:
        return None  # No timestamp, can't compute

    try:
        last_active = datetime.fromisoformat(last_active_str)
    except (ValueError, TypeError):
        return None

    if last_active.tzinfo is None and now.tzinfo is not None:
        last_active = last_active.replace(tzinfo=timezone.utc)
    elif last_active.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    days_since = (now - last_active).days
    if days_since >= days_threshold:
        return action if action == "archive" else action

    return None


def compute_boost(frontmatter: dict, config: MemoirConfig) -> int:
    """Return new weight if trigger_count crosses a boost threshold.

    Pure function — does not touch disk.
    """
    count = frontmatter.get("trigger_count", 0)
    current_weight = frontmatter.get("weight", 3)
    cap = config.weight.boost.get("cap", 5)
    thresholds = config.weight.boost.get("thresholds", [5, 15, 30])

    boosts = sum(1 for t in thresholds if count >= t)
    new_weight = min(current_weight + boosts, cap)
    return new_weight


def apply_update(
    filepath: str | Path, new_weight: int, *, note: str = ""
) -> None:
    """Read file, update weight in frontmatter, atomic write."""
    fm, body = parse(filepath)
    old = fm.get("weight", "?")
    fm["weight"] = new_weight
    if note:
        fm.setdefault("weight_log", []).append({
            "from": old,
            "to": new_weight,
            "at": datetime.now(timezone.utc).isoformat(),
            "note": note,
        })
    write(filepath, fm, body)


def mark_triggered(filepath: str | Path) -> None:
    """Increment trigger_count and update last_triggered timestamp."""
    fm, body = parse(filepath)
    fm["last_triggered"] = datetime.now(timezone.utc).isoformat()
    fm["trigger_count"] = fm.get("trigger_count", 0) + 1
    write(filepath, fm, body)
