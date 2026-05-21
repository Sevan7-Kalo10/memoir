"""Tests for memoir.core.indexer (SQLite FTS5 index)."""

import tempfile
from pathlib import Path

from memoir.core.indexer import MemoirIndex, search


def _make_store(path: Path):
    """Create a minimal memoir store for testing."""
    (path / "core").mkdir(parents=True, exist_ok=True)
    (path / "code").mkdir(parents=True, exist_ok=True)

    (path / "core" / "identity.md").write_text(
        "---\nname: who-am-i\nweight: 5\ntags: [identity, core]\n---\n"
        "# Who I Am\n\nI am an AI assistant built to help with clarity and depth.\n",
        encoding="utf-8",
    )
    (path / "core" / "values.md").write_text(
        "---\nname: values\nweight: 5\ntags: [values, core]\n---\n"
        "# What I Value\n\nClarity over cleverness. Honesty without cruelty.\n",
        encoding="utf-8",
    )
    (path / "code" / "style.md").write_text(
        "---\nname: functional-style\nweight: 3\ntags: [code, fp]\n---\n"
        "# Functional Style\n\nPure functions are testable and composable.\n",
        encoding="utf-8",
    )


class TestMemoirIndex:
    def test_build_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            _make_store(store)

            idx = MemoirIndex(store)
            assert idx.needs_rebuild() is True

            count = idx.build()
            assert count == 3

            assert idx.needs_rebuild() is False

            results = idx.search("clarity")
            assert len(results) >= 2
            files = {r["relpath"] for r in results}
            assert "core/identity.md" in files
            assert "core/values.md" in files

    def test_weight_filter(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            _make_store(store)

            idx = MemoirIndex(store)
            idx.build()

            results = idx.search("testable", weight_min=5)
            files = {r["relpath"] for r in results}
            assert "code/style.md" not in files  # w=3

            results = idx.search("testable", weight_min=1, weight_max=4)
            files = {r["relpath"] for r in results}
            assert "code/style.md" in files

    def test_needs_rebuild_on_new_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            _make_store(store)

            idx = MemoirIndex(store)
            idx.build()
            assert not idx.needs_rebuild()

            (store / "core" / "new.md").write_text(
                "---\nname: new\nweight: 3\ntags: [test]\n---\n# New\n",
                encoding="utf-8",
            )
            assert idx.needs_rebuild()

    def test_auto_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            _make_store(store)

            idx = MemoirIndex(store)
            assert idx.needs_rebuild()
            count = idx.auto()
            assert count == 3
            assert not idx.needs_rebuild()

    def test_convenience_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            _make_store(store)

            results = search(store, "clarity")
            assert len(results) >= 1

    def test_empty_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            idx = MemoirIndex(store)
            count = idx.build()
            assert count == 0
            results = idx.search("anything")
            assert results == []

    def test_chinese_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            (store / "core").mkdir(parents=True)
            (store / "core" / "portrait.md").write_text(
                "---\nname: portrait\nweight: 5\ntags: [用户, 偏好, 酒]\n---\n"
                "# 用户画像\n\n喜欢芋烧酎，不喜欢高度酒的果香。\n",
                encoding="utf-8",
            )

            idx = MemoirIndex(store)
            idx.build()

            results = idx.search("酒")
            assert len(results) == 1
            assert "portrait.md" in results[0]["relpath"]

            results = idx.search("酒 OR 烧酎")
            assert len(results) == 1

            results = idx.search("葡萄酒")
            assert len(results) == 0
