"""
Infrastructure Layer — SQLite History Storage
Persists QR history items between sessions.
"""
from __future__ import annotations
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.domain.entities.entities import HistoryItemEntity, QRCodeEntity


_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS history (
    id              TEXT PRIMARY KEY,
    url             TEXT NOT NULL,
    fg_color        TEXT NOT NULL,
    bg_color        TEXT NOT NULL,
    error_correction TEXT NOT NULL,
    image_size      INTEGER NOT NULL,
    created_at      TEXT NOT NULL,
    thumbnail_data  BLOB NOT NULL
);
"""

_INSERT_SQL = """
INSERT INTO history
    (id, url, fg_color, bg_color, error_correction, image_size, created_at, thumbnail_data)
VALUES (?,   ?,   ?,        ?,        ?,                ?,          ?,          ?);
"""

_SELECT_ALL_SQL = """
SELECT id, url, fg_color, bg_color, error_correction, image_size, created_at, thumbnail_data
FROM history
ORDER BY created_at DESC
LIMIT 50;
"""

_DELETE_SQL = "DELETE FROM history WHERE id = ?;"


class HistoryRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_SQL)

    def save(self, qr: QRCodeEntity, thumbnail_bytes: bytes) -> str:
        item_id = str(uuid.uuid4())
        s = qr.settings
        with self._connect() as conn:
            conn.execute(_INSERT_SQL, (
                item_id,
                s.url,
                s.fg_color,
                s.bg_color,
                s.error_correction.value,
                s.image_size,
                qr.created_at.isoformat(),
                thumbnail_bytes,
            ))
        return item_id

    def load_all(self) -> list[HistoryItemEntity]:
        with self._connect() as conn:
            rows = conn.execute(_SELECT_ALL_SQL).fetchall()
        items = []
        for row in rows:
            items.append(HistoryItemEntity(
                id=row["id"],
                url=row["url"],
                fg_color=row["fg_color"],
                bg_color=row["bg_color"],
                error_correction=row["error_correction"],
                image_size=row["image_size"],
                created_at=datetime.fromisoformat(row["created_at"]),
                thumbnail_data=bytes(row["thumbnail_data"]),
            ))
        return items

    def delete(self, item_id: str) -> None:
        with self._connect() as conn:
            conn.execute(_DELETE_SQL, (item_id,))

    def clear_all(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM history;")
