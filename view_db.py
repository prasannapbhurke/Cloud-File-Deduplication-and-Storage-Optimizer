import sqlite3
import os

DB_PATH = "metadata_catalog.db"

def inspect_database():
    if not os.path.exists(DB_PATH):
        print(f"[!] Database file '{DB_PATH}' not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print(f" DATABASE CATALOG VIEWER: {DB_PATH}")
    print("=" * 80)

    # 1. user_files
    print("\n--- [TABLE: user_files] ---")
    cursor.execute("SELECT id, filename, user_name, file_size, total_chunks, upload_timestamp FROM user_files")
    rows = cursor.fetchall()
    if not rows:
        print("(No files uploaded yet)")
    else:
        for r in rows:
            print(f"ID: {r['id']:<3} | File: {r['filename']:<30} | User: {r['user_name']:<18} | Size: {r['file_size']:<8}B | Chunks: {r['total_chunks']:<3} | Date: {r['upload_timestamp']}")

    # 2. chunks summary
    print("\n--- [TABLE: chunks (Unique Physical Blocks)] ---")
    cursor.execute("SELECT COUNT(*) as total_unique, SUM(size_bytes) as total_physical, MAX(ref_count) as max_refs FROM chunks")
    chunk_stats = cursor.fetchone()
    print(f"Total Unique Physical Chunks: {chunk_stats['total_unique']}")
    print(f"Total Physical Storage Used:  {chunk_stats['total_physical'] or 0} bytes")
    print(f"Max References on a Chunk:    {chunk_stats['max_refs'] or 0}")

    cursor.execute("SELECT chunk_hash, size_bytes, ref_count, first_uploaded_at FROM chunks ORDER BY ref_count DESC LIMIT 5")
    sample_chunks = cursor.fetchall()
    if sample_chunks:
        print("\nTop 5 Most Referenced Chunks:")
        for c in sample_chunks:
            print(f"Hash: {c['chunk_hash'][:16]}... | Size: {c['size_bytes']:<6}B | Refs: {c['ref_count']} | Uploaded: {c['first_uploaded_at']}")

    # 3. file_chunks count
    cursor.execute("SELECT COUNT(*) FROM file_chunks")
    total_mappings = cursor.fetchone()[0]
    print(f"\nTotal Chunk Mappings in Catalog: {total_mappings}")

    print("=" * 80 + "\n")
    conn.close()

if __name__ == "__main__":
    inspect_database()
