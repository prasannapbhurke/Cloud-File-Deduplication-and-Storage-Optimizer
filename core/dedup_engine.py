import os
import sqlite3
import datetime
from contextlib import contextmanager
from typing import BinaryIO, Dict, Any, List, Optional, Generator
from core.hasher import SHA256Hasher
from core.cloud_storage import CloudStorageAdapter
from core.db import DatabaseManager


class DeduplicationManager:
    """
    Chunk-Level Deduplication & Metadata Controller.
    Slices files into fixed-size blocks (e.g., 64 KB), computes cryptographic SHA-256
    fingerprints for both individual chunks and the whole file, tracks reference counters,
    and eliminates redundant physical storage writes at the block level.
    Supports both Supabase PostgreSQL and local SQLite.
    """
    DEFAULT_CHUNK_SIZE = 65536  # 64 KB per block

    def __init__(self, db_path: str = "metadata_catalog.db",
                 db_url: Optional[str] = None,
                 storage_adapter: Optional[CloudStorageAdapter] = None,
                 chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.db_path = os.path.abspath(db_path)
        self.db_manager = DatabaseManager(self.db_path, db_url=db_url)
        self.storage = storage_adapter or CloudStorageAdapter()
        self.chunk_size = chunk_size
        self.has_chunk_hash_col = False
        self._init_db()

    @contextmanager
    def _get_conn(self):
        with self.db_manager.get_conn() as conn:
            yield conn

    def _init_db(self):
        """Initializes database schema with migration support."""
        with self._get_conn() as conn:
            cursor = self.db_manager.get_cursor(conn)
            if self.db_manager.is_postgres:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_hash VARCHAR(64) PRIMARY KEY,
                        size_bytes BIGINT NOT NULL,
                        ref_count INTEGER NOT NULL DEFAULT 1,
                        first_uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_files (
                        id BIGSERIAL PRIMARY KEY,
                        filename TEXT NOT NULL,
                        user_name TEXT NOT NULL,
                        file_size BIGINT NOT NULL,
                        file_hash VARCHAR(64) NOT NULL,
                        total_chunks INTEGER NOT NULL DEFAULT 1,
                        dedup_chunks INTEGER NOT NULL DEFAULT 0,
                        new_chunks INTEGER NOT NULL DEFAULT 1,
                        upload_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        is_deduplicated BOOLEAN NOT NULL DEFAULT FALSE
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_chunks (
                        id BIGSERIAL PRIMARY KEY,
                        file_id BIGINT REFERENCES user_files(id) ON DELETE CASCADE,
                        chunk_index INTEGER NOT NULL,
                        chunk_hash VARCHAR(64) REFERENCES chunks(chunk_hash)
                    )
                """)
                self.has_chunk_hash_col = False
                return

            # Physical unique chunks catalog
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_hash TEXT PRIMARY KEY,
                    size_bytes INTEGER NOT NULL,
                    ref_count INTEGER NOT NULL DEFAULT 1,
                    first_uploaded_at TEXT NOT NULL
                )
            """)
            # Virtual user files catalog
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
            # Check if user_files needs migration from older whole-file schema
            cursor.execute("PRAGMA table_info(user_files)")
            columns = [col["name"] for col in cursor.fetchall()]
            self.has_chunk_hash_col = "chunk_hash" in columns
            if "file_hash" not in columns and "chunk_hash" in columns:
                cursor.execute("ALTER TABLE user_files ADD COLUMN file_hash TEXT DEFAULT ''")
            if "total_chunks" not in columns:
                cursor.execute("ALTER TABLE user_files ADD COLUMN total_chunks INTEGER NOT NULL DEFAULT 1")
            if "dedup_chunks" not in columns:
                cursor.execute("ALTER TABLE user_files ADD COLUMN dedup_chunks INTEGER NOT NULL DEFAULT 0")
            if "new_chunks" not in columns:
                cursor.execute("ALTER TABLE user_files ADD COLUMN new_chunks INTEGER NOT NULL DEFAULT 1")

            # Synchronize file_hash with legacy chunk_hash if blank
            if "chunk_hash" in columns:
                cursor.execute("UPDATE user_files SET file_hash = chunk_hash WHERE (file_hash IS NULL OR file_hash = '') AND chunk_hash IS NOT NULL")
                cursor.execute("""
                    UPDATE user_files
                    SET is_deduplicated = 1,
                        dedup_chunks = CASE WHEN total_chunks > 0 THEN total_chunks ELSE 1 END,
                        new_chunks = 0
                    WHERE id NOT IN (
                        SELECT MIN(id) FROM user_files GROUP BY COALESCE(NULLIF(file_hash, ''), chunk_hash)
                    )
                """)
                cursor.execute("""
                    UPDATE user_files
                    SET is_deduplicated = 0,
                        dedup_chunks = 0,
                        new_chunks = CASE WHEN total_chunks > 0 THEN total_chunks ELSE 1 END
                    WHERE id IN (
                        SELECT MIN(id) FROM user_files GROUP BY COALESCE(NULLIF(file_hash, ''), chunk_hash)
                    )
                """)
            else:
                cursor.execute("""
                    UPDATE user_files
                    SET is_deduplicated = 1,
                        dedup_chunks = CASE WHEN total_chunks > 0 THEN total_chunks ELSE 1 END,
                        new_chunks = 0
                    WHERE id NOT IN (
                        SELECT MIN(id) FROM user_files GROUP BY file_hash
                    )
                """)
                cursor.execute("""
                    UPDATE user_files
                    SET is_deduplicated = 0,
                        dedup_chunks = 0,
                        new_chunks = CASE WHEN total_chunks > 0 THEN total_chunks ELSE 1 END
                    WHERE id IN (
                        SELECT MIN(id) FROM user_files GROUP BY file_hash
                    )
                """)

            # Mapping between user files and their ordered constituent chunks
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

            # Populate file_chunks for legacy single-chunk records if missing
            if "chunk_hash" in columns:
                cursor.execute("""
                    INSERT OR IGNORE INTO file_chunks (file_id, chunk_index, chunk_hash)
                    SELECT id, 0, COALESCE(NULLIF(file_hash, ''), chunk_hash)
                    FROM user_files
                    WHERE id NOT IN (SELECT DISTINCT file_id FROM file_chunks)
                """)
            else:
                cursor.execute("""
                    INSERT OR IGNORE INTO file_chunks (file_id, chunk_index, chunk_hash)
                    SELECT id, 0, file_hash
                    FROM user_files
                    WHERE id NOT IN (SELECT DISTINCT file_id FROM file_chunks)
                """)

            conn.commit()

    def upload_file(self, filename: str, user_name: str, file_stream: BinaryIO) -> Dict[str, Any]:
        """
        Executes the deduplication pipeline:
        1. Read stream and compute overall file SHA-256 fingerprint
        2. Fast-Path: If whole-file SHA-256 matches an existing file, intercept as 100% duplicate
        3. Block-Level: Slice stream into 64 KB blocks and verify individual chunk hashes in CAS
        4. Eliminate redundant block writes, increment ref counters, and link ordered file_chunks
        """
        if hasattr(file_stream, "seek"):
            file_stream.seek(0)

        # Step 1: Compute whole-file SHA-256 hash first
        file_hash = SHA256Hasher.compute_hash(file_stream)

        # Determine file size
        if hasattr(file_stream, "seek"):
            file_stream.seek(0, os.SEEK_END)
            file_size = file_stream.tell()
            file_stream.seek(0)
        else:
            file_size = 0

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_conn() as conn:
            cursor = self.db_manager.get_cursor(conn)

            # Fast-Path: Check if an identical file (exact same bytes/hash) already exists in catalog
            cursor.execute("""
                SELECT id, file_size, total_chunks, is_deduplicated
                FROM user_files
                WHERE file_hash = ?
                ORDER BY id ASC LIMIT 1
            """, (file_hash,))
            existing_match = cursor.fetchone()

            if existing_match:
                # ⚡ 100% EXACT DUPLICATE DETECTED!
                # Fetch existing constituent chunks
                cursor.execute("""
                    SELECT chunk_index, chunk_hash FROM file_chunks
                    WHERE file_id = ? ORDER BY chunk_index ASC
                """, (existing_match["id"],))
                prev_chunks = cursor.fetchall()

                if prev_chunks:
                    total_chunks = len(prev_chunks)
                    for r in prev_chunks:
                        cursor.execute("UPDATE chunks SET ref_count = ref_count + 1 WHERE chunk_hash = ?", (r["chunk_hash"],))
                else:
                    total_chunks = 1
                    cursor.execute("SELECT chunk_hash, ref_count FROM chunks WHERE chunk_hash = ?", (file_hash,))
                    ch = cursor.fetchone()
                    if ch:
                        cursor.execute("UPDATE chunks SET ref_count = ref_count + 1 WHERE chunk_hash = ?", (file_hash,))
                    else:
                        self.storage.store_chunk(file_hash, file_stream)
                        cursor.execute("INSERT OR IGNORE INTO chunks (chunk_hash, size_bytes, ref_count, first_uploaded_at) VALUES (?, ?, 2, ?)",
                                       (file_hash, file_size, now_str))

                # Insert virtual user file mapping
                if getattr(self, "has_chunk_hash_col", False):
                    cursor.execute("""
                        INSERT INTO user_files (
                            filename, user_name, file_size, chunk_hash, file_hash,
                            total_chunks, dedup_chunks, new_chunks,
                            upload_timestamp, is_deduplicated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (filename, user_name, file_size, file_hash, file_hash, total_chunks, total_chunks, 0, now_str))
                else:
                    cursor.execute("""
                        INSERT INTO user_files (
                            filename, user_name, file_size, file_hash,
                            total_chunks, dedup_chunks, new_chunks,
                            upload_timestamp, is_deduplicated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """, (filename, user_name, file_size, file_hash, total_chunks, total_chunks, 0, now_str))
                new_file_id = cursor.lastrowid

                # Link file_chunks
                if prev_chunks:
                    for r in prev_chunks:
                        cursor.execute("""
                            INSERT INTO file_chunks (file_id, chunk_index, chunk_hash)
                            VALUES (?, ?, ?)
                        """, (new_file_id, r["chunk_index"], r["chunk_hash"]))
                else:
                    cursor.execute("""
                        INSERT INTO file_chunks (file_id, chunk_index, chunk_hash)
                        VALUES (?, 0, ?)
                    """, (new_file_id, file_hash))

                conn.commit()

                return {
                    "status": "DEDUPLICATED",
                    "file_id": new_file_id,
                    "filename": filename,
                    "user_name": user_name,
                    "file_size": file_size,
                    "file_hash": file_hash,
                    "chunk_hash": file_hash,
                    "total_chunks": total_chunks,
                    "dedup_chunks": total_chunks,
                    "new_chunks": 0,
                    "dedup_percentage": 100.0,
                    "physical_bytes_written": 0,
                    "space_saved_bytes": file_size,
                    "message": f"Exact duplicate file detected! All {total_chunks}/{total_chunks} chunks reused. 0 bytes written to cloud."
                }

            # Step 2: Not an exact whole-file match -> Slice into 64 KB blocks for block-level deduplication
            file_chunks_data = []
            file_size = 0

            while True:
                chunk_data = file_stream.read(self.chunk_size)
                if not chunk_data:
                    break
                file_size += len(chunk_data)
                chunk_hash = SHA256Hasher.compute_hash(chunk_data)
                file_chunks_data.append((chunk_hash, chunk_data))

            if not file_chunks_data:
                empty_hash = SHA256Hasher.compute_hash(b"")
                file_chunks_data.append((empty_hash, b""))

            total_chunks = len(file_chunks_data)
            dedup_chunks_count = 0
            new_chunks_count = 0
            physical_bytes_written = 0
            space_saved_bytes = 0
            chunk_details = []
            chunk_records = []

            for idx, (c_hash, c_bytes) in enumerate(file_chunks_data):
                c_size = len(c_bytes)
                cursor.execute(
                    "SELECT chunk_hash, size_bytes, ref_count FROM chunks WHERE chunk_hash = ?",
                    (c_hash,)
                )
                existing_chunk = cursor.fetchone()

                if existing_chunk:
                    # Duplicate block detected!
                    new_ref = existing_chunk["ref_count"] + 1
                    cursor.execute("UPDATE chunks SET ref_count = ? WHERE chunk_hash = ?", (new_ref, c_hash))
                    dedup_chunks_count += 1
                    space_saved_bytes += c_size
                    chunk_details.append({
                        "index": idx,
                        "hash": c_hash,
                        "size": c_size,
                        "status": "DEDUPLICATED",
                        "ref_count": new_ref
                    })
                else:
                    # New unique chunk payload -> persist to cloud storage
                    self.storage.store_chunk(c_hash, c_bytes)
                    cursor.execute("""
                        INSERT INTO chunks (chunk_hash, size_bytes, ref_count, first_uploaded_at)
                        VALUES (?, ?, 1, ?)
                    """, (c_hash, c_size, now_str))
                    new_chunks_count += 1
                    physical_bytes_written += c_size
                    chunk_details.append({
                        "index": idx,
                        "hash": c_hash,
                        "size": c_size,
                        "status": "STORED",
                        "ref_count": 1
                    })

                chunk_records.append((idx, c_hash))

            # Determine deduplication status
            is_full_dedup = (dedup_chunks_count == total_chunks and total_chunks > 0)
            is_partial_dedup = (dedup_chunks_count > 0 and not is_full_dedup)

            if is_full_dedup:
                status = "DEDUPLICATED"
                message = f"Exact duplicate file detected! All {total_chunks}/{total_chunks} chunks reused. 0 bytes written to cloud."
            elif is_partial_dedup:
                status = "PARTIALLY_DEDUPLICATED"
                message = f"Partial duplicate detected! {dedup_chunks_count}/{total_chunks} chunks reused, saving {space_saved_bytes} bytes."
            else:
                status = "STORED"
                message = f"Unique file stored successfully across {total_chunks} cloud chunks."

            # Insert virtual user file link
            if getattr(self, "has_chunk_hash_col", False):
                cursor.execute("""
                    INSERT INTO user_files (
                        filename, user_name, file_size, chunk_hash, file_hash,
                        total_chunks, dedup_chunks, new_chunks,
                        upload_timestamp, is_deduplicated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    filename, user_name, file_size, file_hash, file_hash,
                    total_chunks, dedup_chunks_count, new_chunks_count,
                    now_str, 1 if dedup_chunks_count > 0 else 0
                ))
            else:
                cursor.execute("""
                    INSERT INTO user_files (
                        filename, user_name, file_size, file_hash,
                        total_chunks, dedup_chunks, new_chunks,
                        upload_timestamp, is_deduplicated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    filename, user_name, file_size, file_hash,
                    total_chunks, dedup_chunks_count, new_chunks_count,
                    now_str, 1 if dedup_chunks_count > 0 else 0
                ))
            file_id = cursor.lastrowid

            # Insert file_chunks mappings
            for idx, c_hash in chunk_records:
                cursor.execute("""
                    INSERT INTO file_chunks (file_id, chunk_index, chunk_hash)
                    VALUES (?, ?, ?)
                """, (file_id, idx, c_hash))

            conn.commit()

            dedup_pct = round((dedup_chunks_count / total_chunks) * 100, 1) if total_chunks > 0 else 0.0

            return {
                "status": status,
                "file_id": file_id,
                "filename": filename,
                "user_name": user_name,
                "file_size": file_size,
                "file_hash": file_hash,
                "chunk_hash": file_hash,  # Backward compatibility
                "total_chunks": total_chunks,
                "dedup_chunks": dedup_chunks_count,
                "new_chunks": new_chunks_count,
                "dedup_percentage": dedup_pct,
                "physical_bytes_written": physical_bytes_written,
                "space_saved_bytes": space_saved_bytes,
                "chunk_details": chunk_details,
                "message": message
            }

    def list_files(self) -> List[Dict[str, Any]]:
        """Returns all registered user files with chunk statistics."""
        with self._get_conn() as conn:
            cursor = self.db_manager.get_cursor(conn)
            cursor.execute("""
                SELECT uf.id, uf.filename, uf.user_name, uf.file_size, uf.file_hash,
                       uf.total_chunks, uf.dedup_chunks, uf.new_chunks,
                       uf.upload_timestamp, uf.is_deduplicated
                FROM user_files uf
                ORDER BY uf.id DESC
            """)
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                # Keep backward compatibility with chunk_hash
                item["chunk_hash"] = item.get("file_hash") or ""
                target_hash = item["chunk_hash"]

                # Check if this exact hash appeared in an earlier file
                cursor.execute("""
                    SELECT MIN(id) FROM user_files
                    WHERE file_hash = ? AND id != ?
                """, (target_hash, item["id"]))
                earliest_match = cursor.fetchone()

                if earliest_match and earliest_match[0] is not None and item["id"] > earliest_match[0]:
                    item["is_deduplicated"] = 1
                    item["dedup_chunks"] = item["total_chunks"] if item["total_chunks"] > 0 else 1

                # If flagged as deduplicated, ensure dedup_chunks is accurate
                if item.get("is_deduplicated") and (not item.get("dedup_chunks") or item.get("dedup_chunks") == 0):
                    item["dedup_chunks"] = item["total_chunks"] if item["total_chunks"] > 0 else 1

                # Calculate reference count for the primary/first chunk for table display
                cursor.execute("""
                    SELECT c.ref_count FROM file_chunks fc
                    JOIN chunks c ON fc.chunk_hash = c.chunk_hash
                    WHERE fc.file_id = ?
                    LIMIT 1
                """, (item["id"],))
                c_row = cursor.fetchone()
                item["ref_count"] = c_row["ref_count"] if c_row else 1
                result.append(item)
            return result

    def get_file(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Retrieves file metadata and constituent chunk details."""
        with self._get_conn() as conn:
            cursor = self.db_manager.get_cursor(conn)
            cursor.execute("""
                SELECT uf.id, uf.filename, uf.user_name, uf.file_size, uf.file_hash,
                       uf.total_chunks, uf.dedup_chunks, uf.new_chunks, uf.upload_timestamp
                FROM user_files uf
                WHERE uf.id = ?
            """, (file_id,))
            row = cursor.fetchone()
            if not row:
                return None
            res = dict(row)
            res["chunk_hash"] = res.get("file_hash") or ""

            # Fetch all chunks in order
            cursor.execute("""
                SELECT fc.chunk_index, fc.chunk_hash, c.size_bytes, c.ref_count
                FROM file_chunks fc
                JOIN chunks c ON fc.chunk_hash = c.chunk_hash
                WHERE fc.file_id = ?
                ORDER BY fc.chunk_index ASC
            """, (file_id,))
            res["chunks"] = [dict(c) for c in cursor.fetchall()]
            return res

    def get_file_chunks(self, file_id: int) -> List[Dict[str, Any]]:
        """Returns the list of chunks for a given file with metadata."""
        file_info = self.get_file(file_id)
        if not file_info:
            return []
        return file_info.get("chunks", [])

    def reconstruct_file_stream(self, file_id: int) -> Generator[bytes, None, None]:
        """
        Reconstructs the original file stream by reading and yielding each chunk in order.
        Streams data chunk-by-chunk to ensure minimal memory overhead.
        """
        with self._get_conn() as conn:
            cursor = self.db_manager.get_cursor(conn)
            cursor.execute("""
                SELECT fc.chunk_hash
                FROM file_chunks fc
                WHERE fc.file_id = ?
                ORDER BY fc.chunk_index ASC
            """, (file_id,))
            chunk_rows = cursor.fetchall()

        for r in chunk_rows:
            chunk_data = self.storage.get_chunk_bytes(r["chunk_hash"])
            if chunk_data is not None:
                yield chunk_data
            else:
                # If old single-chunk record, fallback check
                yield b""

    def delete_file(self, file_id: int) -> Dict[str, Any]:
        """
        Deletes a user's virtual file link and its constituent chunk mappings.
        Decrements the reference counter in `chunks` for each chunk.
        If a chunk's reference count drops to 0, permanently purges the physical file.
        """
        with self._get_conn() as conn:
            cursor = self.db_manager.get_cursor(conn)
            cursor.execute("SELECT filename FROM user_files WHERE id = ?", (file_id,))
            file_row = cursor.fetchone()
            if not file_row:
                return {"success": False, "error": "File not found"}

            filename = file_row["filename"]

            # Retrieve all chunk hashes mapped to this file
            cursor.execute("SELECT chunk_hash FROM file_chunks WHERE file_id = ?", (file_id,))
            file_chunks = [r["chunk_hash"] for r in cursor.fetchall()]

            # Remove file_chunks mappings and user_files record
            cursor.execute("DELETE FROM file_chunks WHERE file_id = ?", (file_id,))
            cursor.execute("DELETE FROM user_files WHERE id = ?", (file_id,))

            purged_chunks_count = 0
            for c_hash in file_chunks:
                cursor.execute("SELECT ref_count FROM chunks WHERE chunk_hash = ?", (c_hash,))
                c_row = cursor.fetchone()
                if c_row:
                    new_ref = c_row["ref_count"] - 1
                    if new_ref <= 0:
                        cursor.execute("DELETE FROM chunks WHERE chunk_hash = ?", (c_hash,))
                        self.storage.delete_chunk(c_hash)
                        purged_chunks_count += 1
                    else:
                        cursor.execute("UPDATE chunks SET ref_count = ? WHERE chunk_hash = ?", (new_ref, c_hash))

            conn.commit()
            return {
                "success": True,
                "filename": filename,
                "purged_physical_chunks": purged_chunks_count,
                "message": f"File '{filename}' reference removed. Purged {purged_chunks_count} orphaned chunks."
            }

    def reset_all(self):
        """Clears all metadata records, chunk links, and cloud storage chunks."""
        with self._get_conn() as conn:
            cursor = self.db_manager.get_cursor(conn)
            cursor.execute("DELETE FROM file_chunks")
            cursor.execute("DELETE FROM user_files")
            cursor.execute("DELETE FROM chunks")
            conn.commit()
        self.storage.clear_bucket()

