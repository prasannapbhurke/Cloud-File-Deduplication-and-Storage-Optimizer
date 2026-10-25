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
    Guarantees table existence on both engines so 'no such table' never occurs.
    """

    def __init__(self, db_path: str = "metadata_catalog.db", db_url: Optional[str] = None):
        self.db_path = os.path.abspath(db_path)
        self.db_url = db_url or os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
        self.is_postgres = bool(self.db_url and HAS_PSYCOPG2)
        # Pre-initialize SQLite schema so fallback is always instant and safe
        self._init_sqlite_if_needed()

    def _init_sqlite_if_needed(self):
        """Ensures local SQLite file and all tables exist."""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            try:
                conn.execute("PRAGMA foreign_keys = ON")
                self.ensure_sqlite_schema(conn)
            finally:
                conn.close()
        except Exception as e:
            print(f"[!] Warning: Could not pre-initialize SQLite catalog ({e})")

    @staticmethod
    def ensure_sqlite_schema(conn: sqlite3.Connection):
        """Creates required SQLite tables and handles schema migrations."""
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_hash TEXT PRIMARY KEY,
                size_bytes INTEGER NOT NULL,
                ref_count INTEGER NOT NULL DEFAULT 1,
                first_uploaded_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                user_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_hash TEXT NOT NULL,
                total_chunks INTEGER NOT NULL DEFAULT 1,
                dedup_chunks INTEGER NOT NULL DEFAULT 0,
                new_chunks INTEGER NOT NULL DEFAULT 1,
                upload_timestamp TEXT NOT NULL,
                is_deduplicated BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_chunks (
                file_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                chunk_hash TEXT NOT NULL,
                PRIMARY KEY (file_id, chunk_index),
                FOREIGN KEY (file_id) REFERENCES user_files (id) ON DELETE CASCADE,
                FOREIGN KEY (chunk_hash) REFERENCES chunks (chunk_hash)
            )
        """)

        # Migration support for legacy schemas
        cursor.execute("PRAGMA table_info(user_files)")
        cols = [c[1] for c in cursor.fetchall()]
        if "file_hash" not in cols and "chunk_hash" in cols:
            cursor.execute("ALTER TABLE user_files ADD COLUMN file_hash TEXT DEFAULT ''")
        if "total_chunks" not in cols:
            cursor.execute("ALTER TABLE user_files ADD COLUMN total_chunks INTEGER NOT NULL DEFAULT 1")
        if "dedup_chunks" not in cols:
            cursor.execute("ALTER TABLE user_files ADD COLUMN dedup_chunks INTEGER NOT NULL DEFAULT 0")
        if "new_chunks" not in cols:
            cursor.execute("ALTER TABLE user_files ADD COLUMN new_chunks INTEGER NOT NULL DEFAULT 1")

        conn.commit()

    @contextmanager
    def get_conn(self) -> Generator[Any, None, None]:
        if self.is_postgres:
            conn = None
            try:
                conn = psycopg2.connect(self.db_url, cursor_factory=psycopg2.extras.RealDictCursor)
            except Exception as e:
                print(f"[!] Warning: PostgreSQL connection failed ({e}). Falling back to local SQLite.")
                self.is_postgres = False

            if conn is not None:
                try:
                    yield conn
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise
                finally:
                    conn.close()
                return

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        self.ensure_sqlite_schema(conn)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def get_cursor(self, conn) -> CursorAdapter:
        is_pg = not isinstance(conn, sqlite3.Connection)
        return CursorAdapter(conn.cursor(), is_postgres=is_pg)

