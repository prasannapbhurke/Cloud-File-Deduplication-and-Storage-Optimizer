import sys
import os
import io
from core.dedup_engine import DeduplicationManager
from core.analytics import StorageAnalytics


def print_banner():
    print("=" * 75)
    print("   CLOUD FILE DEDUPLICATION & STORAGE OPTIMIZER - CLI DEMO")
    print("   Cloud Computing (CC) Project | Batch T6 | D.Y. Patil College")
    print("=" * 75)


def run_demo():
    print_banner()
    manager = DeduplicationManager()
    analytics = StorageAnalytics()

    print("\n[INFO] Resetting catalog for pristine demonstration run...")
    manager.reset_all()

    # Create mock files
    print("[INFO] Generating synthetic test payloads...\n")
    
    sample_files = [
        ("CC_Unit1_Notes.pdf", "Sarthak Salokhe", b"Cloud Computing Lecture Notes - Virtualization & Hypervisors" * 1500),
        ("Unit1_Notes_Copy.pdf", "Vyanktesh Madhyapgol", b"Cloud Computing Lecture Notes - Virtualization & Hypervisors" * 1500), # 100% duplicate!
        ("Dataset_Archive.zip", "Prasanna Bhurke", b"PK0304_DATASET_EMULATED_PAYLOAD_CHUNK_ARRAY" * 2500),
        ("Dataset_Team_Backup.zip", "Balaji Gaikwad", b"PK0304_DATASET_EMULATED_PAYLOAD_CHUNK_ARRAY" * 2500), # 100% duplicate!
        ("Project_Report_v1.docx", "Manjunath Gavandi", b"MINI PROJECT REPORT CLOUD COMPUTING 2026 SECTION A" * 1500 + b"SECTION B CONTENT" * 1000),
        ("Project_Report_v2_Edited.docx", "Prasanna Bhurke", b"MINI PROJECT REPORT CLOUD COMPUTING 2026 SECTION A" * 1500 + b"SECTION B REVISED 2026" * 1000), # Partial duplicate!
    ]

    for fname, user, content in sample_files:
        print(f">> Processing Upload: '{fname}' by {user} (Size: {len(content)} bytes)")
        stream = io.BytesIO(content)
        res = manager.upload_file(filename=fname, user_name=user, file_stream=stream)

        print(f"   SHA-256 Digest: {res['file_hash']}")
        print(f"   Blocks/Chunks:  {res['total_chunks']} total | {res['dedup_chunks']} reused | {res['new_chunks']} new")
        if res["status"] == "DEDUPLICATED":
            print(f"   ⚡ STATUS: 100% DUPLICATE DETECTED! Physical upload bypassed.")
            print(f"   Action: Linked virtual pointer to existing chunks.")
            print(f"   Physical Storage Added: 0 bytes | Space Saved: {res['space_saved_bytes']} bytes (100% saved!)\n")
        elif res["status"] == "PARTIALLY_DEDUPLICATED":
            print(f"   🧩 STATUS: SUB-FILE / PARTIAL DUPLICATE DETECTED!")
            print(f"   Action: Reused {res['dedup_chunks']} duplicate chunks, wrote only {res['new_chunks']} changed chunks.")
            print(f"   Physical Storage Added: {res['physical_bytes_written']} bytes | Space Saved: {res['space_saved_bytes']} bytes ({res['dedup_percentage']}% saved!)\n")
        else:
            print(f"   💾 STATUS: UNIQUE PAYLOAD STORED to Cloud Object Store.")
            print(f"   Physical Storage Added: {res['physical_bytes_written']} bytes across {res['total_chunks']} chunks\n")

    print("-" * 75)
    print(">> FINAL STORAGE OPTIMIZATION REPORT:")
    stats = analytics.get_metrics()
    print(f"   Total Files Processed:        {stats['total_files']}")
    print(f"   Unique Chunks in Cloud S3:   {stats['unique_chunks']}")
    print(f"   Duplicate Uploads Intercepted: {stats['duplicate_files_count']}")
    print(f"   Total Logical Upload Volume:  {stats['total_logical_formatted']}")
    print(f"   Physical Cloud Stored:       {stats['total_physical_formatted']}")
    print(f"   Net Cloud Space Saved:       {stats['space_saved_formatted']} ({stats['savings_percentage']}% saved)")
    print(f"   Deduplication Ratio:          {stats['deduplication_ratio']}")
    print("-" * 75)
    print("Demo completed successfully!\n")


def show_stats():
    analytics = StorageAnalytics()
    stats = analytics.get_metrics()
    print("\n--- Current Storage Statistics ---")
    for k, v in stats.items():
        print(f"{k}: {v}")
    print()


def show_list():
    manager = DeduplicationManager()
    files = manager.list_files()
    print(f"\n--- Registered Files ({len(files)}) ---")
    for f in files:
        dedup_label = "[DEDUP]" if f['is_deduplicated'] else "[UNIQUE]"
        print(f"#{f['id']} {dedup_label} {f['filename']} ({f['file_size']} B) | User: {f['user_name']} | Refs: {f['ref_count']} | Hash: {f['chunk_hash'][:16]}...")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "demo":
        run_demo()
    elif sys.argv[1] == "stats":
        show_stats()
    elif sys.argv[1] == "list":
        show_list()
    elif sys.argv[1] == "reset":
        DeduplicationManager().reset_all()
        print("Storage and catalog cleared.")
    else:
        print("Usage: python cli.py [demo|stats|list|reset]")
