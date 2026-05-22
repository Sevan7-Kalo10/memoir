"""SQLite FTS5 index for memoir stores.

Zero extra dependencies — sqlite3 is stdlib.
FTS5 provides full-text search with BM25 ranking.
Supports weight-range filtering and tag intersection queries.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from memoir.core.frontmatter import parse

INDEX_FILENAME = ".memoir_index.db"
INDEX_VERSION = 1


class MemoirIndex:
    def __init__(self, store_path: str | Path):
        self.store_path = Path(store_path)
        self.db_path = self.store_path / INDEX_FILENAME

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def build(self) -> int:
        """Full rebuild. Returns number of files indexed."""
        conn = self._get_conn()
        try:
            conn.execute("DROP TABLE IF EXISTS _files")
            conn.execute("DROP TABLE IF EXISTS _index_meta")

            conn.execute(
                """CREATE VIRTUAL TABLE IF NOT EXISTS _files
                USING fts5(
                    relpath,
                    title,
                    body,
                    tags,
                    description,
                    tokenize='unicode61 remove_diacritics 2'
                )"""
            )

            conn.execute(
                """CREATE TABLE IF NOT EXISTS _files_meta (
                    relpath TEXT PRIMARY KEY,
                    weight INTEGER NOT NULL DEFAULT 3,
                    mtime REAL NOT NULL DEFAULT 0
                )"""
            )

            conn.execute(
                """CREATE TABLE IF NOT EXISTS _index_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )"""
            )

            count = 0
            for md_file in self.store_path.rglob("*.md"):
                if "archive" in md_file.parts:
                    continue
                name = md_file.name
                if name.startswith(("MEMORY", "CLAUDE", "AI_", "README")) or name in ("triggers.md",):
                    continue
                if name == "INDEX.md" and "archive" in str(md_file):
                    continue

                try:
                    rel = str(md_file.relative_to(self.store_path)).replace("\\", "/")
                except ValueError:
                    continue

                try:
                    fm, body = parse(md_file)
                except Exception:
                    continue

                title = fm.get("name", md_file.stem)
                tags_list = fm.get("tags", [])
                if isinstance(tags_list, list):
                    tags_text = " ".join(str(t) for t in tags_list)
                else:
                    tags_text = ""
                description = fm.get("description", "") or ""
                weight = fm.get("weight", 3)
                mtime = md_file.stat().st_mtime

                conn.execute(
                    "INSERT INTO _files(relpath, title, body, tags, description) VALUES(?,?,?,?,?)",
                    (rel, title, body, tags_text, description),
                )
                conn.execute(
                    "INSERT OR REPLACE INTO _files_meta(relpath, weight, mtime) VALUES(?,?,?)",
                    (rel, weight, mtime),
                )
                count += 1

            conn.execute(
                "INSERT OR REPLACE INTO _index_meta(key, value) VALUES(?, ?)",
                ("version", str(INDEX_VERSION)),
            )
            conn.execute(
                "INSERT OR REPLACE INTO _index_meta(key, value) VALUES(?, ?)",
                ("file_count", str(count)),
            )
            conn.commit()
            return count
        finally:
            conn.close()

    def search(
        self,
        query: str,
        *,
        weight_min: int = 1,
        weight_max: int = 5,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """FTS5 search with optional weight/tag filters.

        Returns list of {relpath, title, weight, tags, snippet, score}.
        """
        if not self.db_path.exists():
            return []

        conn = self._get_conn()
        try:
            where_clauses = ["_files MATCH ?"]
            params: list = [query]

            if weight_min > 1 or weight_max < 5:
                where_clauses.append(
                    "_files_meta.weight BETWEEN ? AND ?"
                )
                params.extend([weight_min, weight_max])

            #  JOIN needs the table to exist; skip if not yet built
            try:
                _ = conn.execute("SELECT 1 FROM _files_meta LIMIT 0")
                has_meta = True
            except sqlite3.OperationalError:
                has_meta = False

            if has_meta:
                from_clause = "_files JOIN _files_meta ON _files.relpath = _files_meta.relpath"
            else:
                from_clause = "_files"

            where_sql = " AND ".join(where_clauses)
            params.append(limit)

            sql = (
                f"SELECT _files.relpath, snippet(_files, 2, '<mark>', '</mark>', '…', 64) AS snippet, "
                f"  rank AS score"
                + (", _files_meta.weight" if has_meta else ", 3 AS weight")
                + f" FROM {from_clause}"
                f" WHERE {where_sql}"
                f" ORDER BY rank LIMIT ?"
            )

            rows = conn.execute(sql, params).fetchall()

            results = []
            for row in rows:
                d = {
                    "relpath": row["relpath"],
                    "weight": row["weight"],
                    "snippet": row["snippet"],
                    "score": row["score"],
                    "tags": [],
                }
                results.append(d)

            if tags and results:
                tag_set = set(t.strip().lower() for t in tags)
                for r in results:
                    full_path = self.store_path / r["relpath"]
                    if full_path.exists():
                        try:
                            fm, _ = parse(full_path)
                            r["tags"] = fm.get("tags", [])
                        except Exception:
                            pass
                results = [
                    r for r in results
                    if tag_set & set(str(t).strip().lower() for t in r["tags"])
                ]

            return results[:limit]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    def needs_rebuild(self) -> bool:
        """Check if any .md file is newer than the index."""
        if not self.db_path.exists():
            return True

        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT value FROM _index_meta WHERE key='file_count'"
            ).fetchone()
            indexed_count = int(row["value"]) if row else 0
        except sqlite3.OperationalError:
            return True
        finally:
            conn.close()

        current_count = 0
        latest_mtime = 0
        for md_file in self.store_path.rglob("*.md"):
            if "archive" in md_file.parts:
                continue
            name = md_file.name
            if name.startswith("MEMORY") or name == "triggers.md":
                continue
            current_count += 1
            mtime = md_file.stat().st_mtime
            if mtime > latest_mtime:
                latest_mtime = mtime

        if current_count != indexed_count:
            return True

        db_mtime = self.db_path.stat().st_mtime
        return latest_mtime > db_mtime

    def auto(self) -> int:
        """Build only if needed. Returns file count."""
        if self.needs_rebuild():
            return self.build()
        return self._read_count()

    def _read_count(self) -> int:
        if not self.db_path.exists():
            return 0
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT value FROM _index_meta WHERE key='file_count'"
            ).fetchone()
            return int(row["value"]) if row else 0
        except sqlite3.OperationalError:
            return 0
        finally:
            conn.close()


def search(
    store_path: str | Path,
    query: str,
    *,
    weight_min: int = 1,
    weight_max: int = 5,
    tags: list[str] | None = None,
    limit: int = 20,
    auto_build: bool = True,
) -> list[dict]:
    """Convenience function: one-shot search with auto-index."""
    idx = MemoirIndex(store_path)
    if auto_build:
        idx.auto()
    return idx.search(
        query,
        weight_min=weight_min,
        weight_max=weight_max,
        tags=tags,
        limit=limit,
    )
