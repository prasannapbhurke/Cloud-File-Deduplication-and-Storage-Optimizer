import io
import os
import shutil
from core.dedup_engine import DeduplicationManager
from core.cloud_storage import CloudStorageAdapter
from core.analytics import StorageAnalytics

def run_tests():
    test_db = "test_metadata.db"
    test_bucket = "test_storage_bucket"

    # Cleanup any previous test artifacts
    if os.path.exists(test_db):
        os.remove(test_db)
    if os.path.exists(test_bucket):
        shutil.rmtree(test_bucket)

    storage = CloudStorageAdapter(bucket_dir=test_bucket)
    manager = DeduplicationManager(db_path=test_db, storage_adapter=storage, chunk_size=65536)
    analytics = StorageAnalytics(db_path=test_db)

    print("--- TEST 1: Uploading File 1 (150 KB = 3 chunks) ---")
    data1 = b"CHUNK1_DATA" * 6000 + b"CHUNK2_DATA" * 6000 + b"CHUNK3_DATA" * 1000
    res1 = manager.upload_file("Doc1.pdf", "Prasanna", io.BytesIO(data1))
    print(f"File 1 Status: {res1['status']}")
    print(f"Total Chunks: {res1['total_chunks']}, New: {res1['new_chunks']}, Dedup: {res1['dedup_chunks']}")
    print(f"Physical written: {res1['physical_bytes_written']} bytes")
    assert res1["status"] == "STORED"
    assert res1["new_chunks"] == 3
    assert res1["dedup_chunks"] == 0

    print("\n--- TEST 2: Uploading File 2 with EXACT SAME CONTENT (Should detect 100% duplicate) ---")
    res2 = manager.upload_file("Doc2_Copy.pdf", "Sarthak", io.BytesIO(data1))
    print(f"File 2 Status: {res2['status']}")
    print(f"File 1 Hash: {res1['file_hash']}")
    print(f"File 2 Hash: {res2['file_hash']}")
    print(f"Total Chunks: {res2['total_chunks']}, New: {res2['new_chunks']}, Dedup: {res2['dedup_chunks']}")
    print(f"Physical written: {res2['physical_bytes_written']} bytes, Saved: {res2['space_saved_bytes']} bytes")
    assert res2["status"] == "DEDUPLICATED"
    assert res1["file_hash"] == res2["file_hash"]
    assert res2["total_chunks"] == 3
    assert res2["dedup_chunks"] == 3
    assert res2["new_chunks"] == 0
    assert res2["physical_bytes_written"] == 0
    assert res2["space_saved_bytes"] == len(data1)
    print(">> TEST 2 PASSED: Exact duplicate 100% detected! 0 bytes written.")

    print("\n--- TEST 3: Uploading File 3 with PARTIAL CONTENT (2 identical chunks + 1 modified chunk) ---")
    data3 = b"CHUNK1_DATA" * 6000 + b"CHUNK2_DATA" * 6000 + b"MODIFIED_CHUNK3" * 1000
    res3 = manager.upload_file("Doc3_Modified.pdf", "Balaji", io.BytesIO(data3))
    print(f"File 3 Status: {res3['status']}")
    print(f"Total Chunks: {res3['total_chunks']}, New: {res3['new_chunks']}, Dedup: {res3['dedup_chunks']}")
    print(f"Physical written: {res3['physical_bytes_written']} bytes, Saved: {res3['space_saved_bytes']} bytes")
    assert res3["status"] == "PARTIALLY_DEDUPLICATED"
    assert res3["dedup_chunks"] == 2
    assert res3["new_chunks"] == 1
    print(">> TEST 3 PASSED: Partial duplicate detected! Only 1 chunk written.")

    print("\n--- TEST 4: Reconstructing & Streaming Download of all files ---")
    reconstructed1 = b"".join(manager.reconstruct_file_stream(res1["file_id"]))
    reconstructed2 = b"".join(manager.reconstruct_file_stream(res2["file_id"]))
    reconstructed3 = b"".join(manager.reconstruct_file_stream(res3["file_id"]))
    assert reconstructed1 == data1
    assert reconstructed2 == data1
    assert reconstructed3 == data3
    print(">> TEST 4 PASSED: Byte-for-byte stream reconstruction verified!")

    print("\n--- TEST 5: Storage Analytics Validation ---")
    stats = analytics.get_metrics()
    print(f"Total Files: {stats['total_files']}")
    print(f"Unique Chunks: {stats['unique_chunks']}")
    print(f"Duplicate Files: {stats['duplicate_files_count']}")
    print(f"Total Logical: {stats['total_logical_formatted']}")
    print(f"Physical Stored: {stats['total_physical_formatted']}")
    print(f"Space Saved: {stats['space_saved_formatted']} ({stats['savings_percentage']}%)")
    print(f"Dedup Ratio: {stats['deduplication_ratio']}")
    assert stats["total_files"] == 3
    assert stats["unique_chunks"] == 4  # 3 original chunks + 1 modified chunk
    print(">> TEST 5 PASSED: Storage analytics accurate!")

    print("\n--- CLEANUP ---")
    manager.reset_all()
    if os.path.exists(test_db):
        os.remove(test_db)
    if os.path.exists(test_bucket):
        shutil.rmtree(test_bucket)
    print("ALL TESTS PASSED SUCCESSFULLY! [OK]")

if __name__ == "__main__":
    run_tests()
