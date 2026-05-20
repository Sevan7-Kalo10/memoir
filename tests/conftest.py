from pathlib import Path

import pytest

from memoir.config import MemoirConfig


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_store(tmp_path):
    """Create a minimal memoir store structure in a temp directory."""
    store = tmp_path / "store"
    store.mkdir()

    # Create memoirs.yaml
    config = MemoirConfig()
    config.store.path = str(store)
    config.to_yaml(store / "memoirs.yaml")

    # Create directories
    (store / "core").mkdir()
    (store / "archive").mkdir()

    # Create core index
    (store / "MEMORY.md").write_text(
        "# Memory Index\n\n"
        "## Identity\n"
        "- [Who I Am](core/identity.md) — core identity #identity\n",
        encoding="utf-8",
    )

    # Create a trigger file
    (store / "triggers.md").write_text(
        "# Triggers\n\n"
        "finished eating → remind vitamins → [[core/identity]]\n",
        encoding="utf-8",
    )

    # Create archive index
    (store / "archive" / "INDEX.md").write_text(
        "# Archive Index\n\n", encoding="utf-8"
    )

    # Create a sample memory file
    (store / "core" / "identity.md").write_text(
        "---\n"
        "name: who-am-i\n"
        "weight: 5\n"
        "tags: [identity, core]\n"
        "domain: core\n"
        "---\n"
        "# Who Am I\n\n"
        "I am an AI assistant who values clarity and depth.\n",
        encoding="utf-8",
    )

    return store


@pytest.fixture
def sample_memory(tmp_path):
    """Create a single memory file and return its path."""
    mem = tmp_path / "test.md"
    mem.write_text(
        "---\n"
        "name: test-memory\n"
        "weight: 4\n"
        "tags: [test, unit]\n"
        "domain: core\n"
        "created: 2026-01-15T12:00:00\n"
        "---\n"
        "# Test Memory\n\n"
        "This is a test.\n",
        encoding="utf-8",
    )
    return mem


@pytest.fixture
def default_config():
    return MemoirConfig()
