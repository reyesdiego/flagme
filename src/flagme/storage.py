import os
import sqlite3
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from flagme.models import Flag, ValueType

_SCHEMA = """
CREATE TABLE IF NOT EXISTS flags (
    id            TEXT PRIMARY KEY,
    key           TEXT NOT NULL,
    description   TEXT NOT NULL DEFAULT '',
    environment   TEXT,
    user_id       TEXT,
    starts_at     TEXT,
    ends_at       TEXT,
    value_type    TEXT NOT NULL CHECK (value_type IN ('boolean', 'string')),
    boolean_value INTEGER,
    string_value  TEXT
);
CREATE INDEX IF NOT EXISTS idx_flags_key ON flags(key);
"""


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _parse_iso(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _row_to_flag(row: sqlite3.Row) -> Flag:
    bv: bool | None = None
    if row["boolean_value"] is not None:
        bv = bool(row["boolean_value"])
    return Flag(
        id=UUID(row["id"]),
        key=row["key"],
        description=row["description"],
        environment=row["environment"],
        user_id=row["user_id"],
        starts_at=_parse_iso(row["starts_at"]),
        ends_at=_parse_iso(row["ends_at"]),
        value_type=row["value_type"],
        boolean_value=bv,
        string_value=row["string_value"],
    )


def _flag_params(flag: Flag) -> dict[str, object]:
    return {
        "id": str(flag.id),
        "key": flag.key,
        "description": flag.description,
        "environment": flag.environment,
        "user_id": flag.user_id,
        "starts_at": _iso(flag.starts_at),
        "ends_at": _iso(flag.ends_at),
        "value_type": flag.value_type,
        "boolean_value": (
            None if flag.boolean_value is None else int(flag.boolean_value)
        ),
        "string_value": flag.string_value,
    }


class FlagNotFound(Exception):
    pass


class FlagStorage:
    """Thin wrapper over a sqlite3 connection. One connection per storage instance."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._conn = sqlite3.connect(
            str(db_path),
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def list_flags(
        self, *, environment: str | None = None, user_id: str | None = None
    ) -> list[Flag]:
        sql = "SELECT * FROM flags"
        clauses: list[str] = []
        params: list[object] = []
        if environment is not None:
            clauses.append("(environment = ? OR environment IS NULL)")
            params.append(environment)
        if user_id is not None:
            clauses.append("(user_id = ? OR user_id IS NULL)")
            params.append(user_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY key, environment IS NULL, user_id IS NULL"
        rows = self._conn.execute(sql, params).fetchall()
        return [_row_to_flag(r) for r in rows]

    def get(self, flag_id: UUID) -> Flag:
        row = self._conn.execute(
            "SELECT * FROM flags WHERE id = ?", (str(flag_id),)
        ).fetchone()
        if row is None:
            raise FlagNotFound(str(flag_id))
        return _row_to_flag(row)

    def create(self, flag: Flag) -> Flag:
        self._conn.execute(
            """
            INSERT INTO flags (id, key, description, environment, user_id,
                               starts_at, ends_at, value_type,
                               boolean_value, string_value)
            VALUES (:id, :key, :description, :environment, :user_id,
                    :starts_at, :ends_at, :value_type,
                    :boolean_value, :string_value)
            """,
            _flag_params(flag),
        )
        self._conn.commit()
        return flag

    def update(self, flag: Flag) -> Flag:
        cur = self._conn.execute(
            """
            UPDATE flags
               SET key = :key,
                   description = :description,
                   environment = :environment,
                   user_id = :user_id,
                   starts_at = :starts_at,
                   ends_at = :ends_at,
                   value_type = :value_type,
                   boolean_value = :boolean_value,
                   string_value = :string_value
             WHERE id = :id
            """,
            _flag_params(flag),
        )
        self._conn.commit()
        if cur.rowcount == 0:
            raise FlagNotFound(str(flag.id))
        return flag

    def delete(self, flag_id: UUID) -> None:
        cur = self._conn.execute("DELETE FROM flags WHERE id = ?", (str(flag_id),))
        self._conn.commit()
        if cur.rowcount == 0:
            raise FlagNotFound(str(flag_id))

    def find_match(
        self,
        key: str,
        *,
        environment: str | None,
        user_id: str | None,
        now: datetime,
    ) -> Flag | None:
        """Return the most-specific flag matching the given context, or None.

        Specificity: an exact environment match beats a NULL environment, and
        an exact user_id match beats a NULL user_id. Flags whose time window
        excludes `now` are skipped.
        """
        candidates = [
            f
            for f in self._all_with_key(key)
            if _matches_scope(f, environment=environment, user_id=user_id)
            and _within_window(f, now)
        ]
        if not candidates:
            return None
        return max(candidates, key=_specificity)

    def _all_with_key(self, key: str) -> Iterable[Flag]:
        rows = self._conn.execute(
            "SELECT * FROM flags WHERE key = ?", (key,)
        ).fetchall()
        return [_row_to_flag(r) for r in rows]


def _matches_scope(flag: Flag, *, environment: str | None, user_id: str | None) -> bool:
    if flag.environment is not None and flag.environment != environment:
        return False
    if flag.user_id is not None and flag.user_id != user_id:
        return False
    return True


def _within_window(flag: Flag, now: datetime) -> bool:
    if flag.starts_at is not None and now < _aware(flag.starts_at):
        return False
    if flag.ends_at is not None and now >= _aware(flag.ends_at):
        return False
    return True


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _specificity(flag: Flag) -> int:
    return (2 if flag.environment is not None else 0) + (
        1 if flag.user_id is not None else 0
    )


def evaluate_value(flag: Flag) -> bool | str:
    if flag.value_type == "boolean":
        assert flag.boolean_value is not None
        return flag.boolean_value
    assert flag.string_value is not None
    return flag.string_value


def default_db_path() -> str:
    return os.environ.get("FLAGME_DB", "flagme.db")


__all__ = [
    "FlagNotFound",
    "FlagStorage",
    "ValueType",
    "default_db_path",
    "evaluate_value",
]
