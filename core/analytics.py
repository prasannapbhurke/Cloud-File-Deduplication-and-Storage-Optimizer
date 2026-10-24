import os
from typing import Dict, Any, Optional
from core.db import DatabaseManager


class StorageAnalytics:
    """
    Storage Analytics & Space Optimization Module.
    Calculates live metrics, deduplication efficiency ratios, and physical space savings.
    Supports both Supabase PostgreSQL and local SQLite.
    """

    def __init__(self, db_path: str = "metadata_catalog.db", db_url: Optional[str] = None):
        self.db_path = os.path.abspath(db_path)
        self.db_manager = DatabaseManager(self.db_path, db_url=db_url)

    @staticmethod
    def format_bytes(num_bytes: int) -> str:
        """Converts bytes to human-readable string (B, KB, MB, GB)."""
        if num_bytes < 1024:
            return f"{num_bytes} B"
        elif num_bytes < 1024 ** 2:
            return f"{num_bytes / 1024:.2f} KB"
        elif num_bytes < 1024 ** 3:
            return f"{num_bytes / (1024 ** 2):.2f} MB"
        else:
            return f"{num_bytes / (1024 ** 3):.2f} GB"

    def get_metrics(self) -> Dict[str, Any]:
        """
        Computes the complete deduplication metrics:
        - Total Files Processed
        - Unique Chunks Stored
        - Total Logical Size
        - Physical Cloud Stored Size
        - Net Space Saved
        - Deduplication Efficiency Ratio
        - Percentage Reduction
        """
        with self.db_manager.get_conn() as conn:
            cursor = self.db_manager.get_cursor(conn)

            # Count total uploaded user files and sum logical sizes
            cursor.execute("""
                SELECT COUNT(*) AS total_files,
                       COALESCE(SUM(file_size), 0) AS total_logical,
                       COALESCE(SUM(total_chunks), 0) AS total_logical_chunks,
                       COALESCE(SUM(CASE WHEN (is_deduplicated = 1 OR is_deduplicated = TRUE) AND dedup_chunks = 0 THEN total_chunks ELSE dedup_chunks END), 0) AS total_dedup_chunks,
                       SUM(CASE WHEN (is_deduplicated = 1 OR is_deduplicated = TRUE) THEN 1 ELSE 0 END) AS duplicate_files
                FROM user_files
            """)
            user_stats = cursor.fetchone()
            total_files = user_stats["total_files"] if user_stats else 0
            total_logical_bytes = user_stats["total_logical"] if user_stats else 0
            total_logical_chunks = user_stats["total_logical_chunks"] if user_stats else 0
            total_dedup_chunks = user_stats["total_dedup_chunks"] if user_stats else 0
            duplicate_files = (user_stats["duplicate_files"] if user_stats else 0) or 0

            # Count unique chunks stored and sum physical sizes
            cursor.execute("SELECT COUNT(*) AS unique_chunks, COALESCE(SUM(size_bytes), 0) AS total_physical FROM chunks")
            chunk_stats = cursor.fetchone()
            unique_chunks = chunk_stats["unique_chunks"] if chunk_stats else 0
            total_physical_bytes = chunk_stats["total_physical"] if chunk_stats else 0

            # Space saved calculation
            space_saved_bytes = max(0, total_logical_bytes - total_physical_bytes)

            # Deduplication ratio: Logical / Physical
            if total_physical_bytes > 0:
                dedup_ratio = round(total_logical_bytes / total_physical_bytes, 2)
                savings_pct = round((space_saved_bytes / total_logical_bytes) * 100, 1) if total_logical_bytes > 0 else 0.0
            else:
                dedup_ratio = 1.0
                savings_pct = 0.0

            return {
                "total_files": total_files,
                "unique_chunks": unique_chunks,
                "total_logical_chunks": total_logical_chunks,
                "total_dedup_chunks": total_dedup_chunks,
                "duplicate_files_count": duplicate_files,
                "total_logical_bytes": total_logical_bytes,
                "total_logical_formatted": self.format_bytes(total_logical_bytes),
                "total_physical_bytes": total_physical_bytes,
                "total_physical_formatted": self.format_bytes(total_physical_bytes),
                "space_saved_bytes": space_saved_bytes,
                "space_saved_formatted": self.format_bytes(space_saved_bytes),
                "deduplication_ratio": f"{dedup_ratio} : 1",
                "deduplication_ratio_float": dedup_ratio,
                "savings_percentage": savings_pct,
            }
