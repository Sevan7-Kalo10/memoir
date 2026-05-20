from datetime import datetime, timezone

from datetime import datetime, timezone
from pathlib import Path

from memoir.core.archive import archive, restore, list_archived, scan_for_archive
from memoir.config import MemoirConfig


def test_archive_moves_file(temp_store):
    src = temp_store / "core" / "identity.md"
    archive_dir = temp_store / "archive"
    archive_index = temp_store / "archive" / "INDEX.md"

    assert src.exists()
    new_path = archive(src, archive_dir, archive_index)
    assert not src.exists()
    assert (archive_dir / "identity.md").exists()
    assert "identity.md" in new_path

    # Check index updated
    content = archive_index.read_text(encoding="utf-8")
    assert "identity.md" in content


def test_archive_handles_collision(temp_store):
    archive_dir = temp_store / "archive"
    archive_index = temp_store / "archive" / "INDEX.md"

    # Pre-create a file with same name in archive
    (archive_dir / "identity.md").write_text("existing", encoding="utf-8")

    src = temp_store / "core" / "identity.md"
    new_path = archive(src, archive_dir, archive_index)

    assert not src.exists()
    assert "identity" in Path(new_path).stem  # Has timestamp suffix


def test_restore_file(temp_store):
    archive_dir = temp_store / "archive"
    archive_index = temp_store / "archive" / "INDEX.md"

    # Archive first
    src = temp_store / "core" / "identity.md"
    original_content = src.read_text(encoding="utf-8")
    archive(src, archive_dir, archive_index)

    # Restore
    restored = restore("identity.md", archive_dir, temp_store / "core", archive_index)
    restored_path = temp_store / "core" / "identity.md"
    assert restored_path.exists()

    # Check weight reset to 3
    from memoir.core.frontmatter import parse
    fm, _ = parse(restored_path)
    assert fm["weight"] == 3
    assert "restored_at" in fm


def test_list_archived(temp_store):
    archive_dir = temp_store / "archive"
    archive_index = temp_store / "archive" / "INDEX.md"

    src = temp_store / "core" / "identity.md"
    archive(src, archive_dir, archive_index)

    entries = list_archived(archive_index)
    assert len(entries) >= 1
    assert any("identity.md" in e["line"] for e in entries)


def test_scan_for_archive_dry_run(temp_store, default_config):
    # Set an old timestamp on the memory to make it eligible
    from memoir.core.frontmatter import parse, write

    src = temp_store / "core" / "identity.md"
    fm, body = parse(src)
    fm["weight"] = 1
    fm["last_triggered"] = "2020-01-01T00:00:00"
    write(src, fm, body)

    default_config.store.path = str(temp_store)
    default_config.store.archive_dir = "archive"
    default_config.evolution.archive_index = "archive/INDEX.md"

    results = scan_for_archive(temp_store, default_config, dry_run=True)
    assert len(results) >= 1
    assert not (temp_store / "archive" / "identity.md").exists()  # dry run


def test_scan_skips_archive_dir(temp_store, default_config):
    default_config.store.path = str(temp_store)
    results = scan_for_archive(temp_store, default_config, dry_run=True)
    # No files should be found for archiving (w=5, not old enough)
    assert len(results) == 0
