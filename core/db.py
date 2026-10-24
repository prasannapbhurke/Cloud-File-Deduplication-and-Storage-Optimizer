import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Any, Optional

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class CursorAdapter:
    """Adapts PostgreSQL cursor to match SQLite cursor behavior (e.g., parameter translation & lastrowid)."""

    def __init__(self, cursor, is_postgres: bool = False):
        self._cursor = cursor
        self.is_postgres = is_postgres
        self.lastrowid = None

    def execute(self, sql: str, params: Optional[tuple] = None):
        if self.is_postgres:
            # Adapt SQLite parameter placeholders '?' to PostgreSQL '%s'
            adapted_sql = sql.replace("?", "%s")
            # Adapt 'INSERT OR IGNORE INTO' to 'INSERT INTO ... ON CONFLICT DO NOTHING'
            if "INSERT OR IGNORE INTO" in adapted_sql.upper():
                adapted_sql = adapted_sql.replace("INSERT OR IGNORE INTO", "INSERT INTO").replace("insert or ignore into", "INSERT INTO")
                if "ON CONFLICT" not in adapted_sql.upper():
                    adapted_sql += " ON CONFLICT DO NOTHING"

            # Adapt boolean comparisons for portability
            adapted_sql = adapted_sql.replace("is_deduplicated = 1", "(is_deduplicated = TRUE OR is_deduplicated::int = 1)")
            adapted_sql = adapted_sql.replace("is_deduplicated = 0", "(is_deduplicated = FALSE OR is_deduplicated::int = 0)")

            # Auto-capture inserted ID if user_files insert
            if "INSERT INTO user_files" in adapted_sql and "RETURNING id" not in adapted_sql:
                adapted_sql += " RETURNING id"
                self._cursor.execute(adapted_sql, params or ())
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row[0] if isinstance(row, (tuple, list)) else row.get("id")
                return self

            self._cursor.execute(adapted_sql, params or ())
            return self
        else:
            if params is not None:
                self._cursor.execute(sql, params)
            else:
                self._cursor.execute(sql)
            self.lastrowid = self._cursor.lastrowid
            return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def __getattr__(self, name: str):
        return getattr(self._cursor, name)


class DatabaseManager:
    """
    Unified Database Manager.
    Automatically connects to Supabase PostgreSQL when DATABASE_URL or SUPABASE_DB_URL is set,
    otherwise smoothly falls back to local SQLite (metadata_catalog.db).
    """

    def __init__(self, db_path: str = "metadata_catalog.db", db_url: Optional[str] = None):
        self.db_path = os.path.abspath(db_path)
        self.db_url = db_url or os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
        self.is_postgres = bool(self.db_url and HAS_PSYCOPG2)

    @contextmanager
    def get_conn(self) -> Generator[Any, None, None]:
        if self.is_postgres:
            try:
                conn = psycopg2.connect(self.db_url, cursor_factory=psycopg2.extras.RealDictCursor)
                try:
                    yield conn
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
                finally:
                    conn.close()
                return
            except Exception as e:
                print(f"[!] Warning: PostgreSQL connection failed ({e}). Falling back to local SQLite.")
                self.is_postgres = False

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def get_cursor(self, conn) -> CursorAdapter:
        is_pg = not isinstance(conn, sqlite3.Connection)
        return CursorAdapter(conn.cursor(), is_postgres=is_pg)

