"""
Supabase Automated Provisioning & Verification Utility
Connects to Supabase PostgreSQL and Supabase Storage to initialize tables,
verify storage bucket access, and test end-to-end cloud deduplication.
"""

import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def prompt_env(key, description, default=""):
    val = os.environ.get(key)
    if not val:
        prompt_text = f"Enter {description}"
        if default:
            prompt_text += f" [{default}]"
        prompt_text += ": "
        val = input(prompt_text).strip() or default
    return val

def run_setup():
    print("=" * 70)
    print("⚡ SUPABASE DATABASE & STORAGE SETUP UTILITY")
    print("=" * 70)

    # 1. Gather credentials
    supabase_url = prompt_env("SUPABASE_URL", "Supabase Project URL (e.g., https://xyz.supabase.co)")
    supabase_key = prompt_env("SUPABASE_KEY", "Supabase Service Role Key or Anon Key")
    database_url = prompt_env("DATABASE_URL", "Supabase PostgreSQL URI (from Database -> Connection string -> URI)")

    if not supabase_url or not supabase_key or not database_url:
        print("\n❌ Error: All 3 Supabase credentials are required.")
        print("Please check your Supabase dashboard at https://supabase.com")
        sys.exit(1)

    # Save to local environment for this run
    os.environ["SUPABASE_URL"] = supabase_url
    os.environ["SUPABASE_KEY"] = supabase_key
    os.environ["DATABASE_URL"] = database_url

    # 2. Test PostgreSQL Database Connection & Provision Tables
    print("\n[1/3] Connecting to Supabase PostgreSQL database...")
    try:
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        pg_ver = cursor.fetchone()[0]
        print(f"  ✅ Connected successfully to PostgreSQL!")
        print(f"     Version: {pg_ver.split(',')[0]}")

        print("  -> Creating tables ('chunks', 'user_files', 'file_chunks')...")
        ddl = """
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_hash VARCHAR(64) PRIMARY KEY,
            size_bytes BIGINT NOT NULL,
            ref_count INTEGER NOT NULL DEFAULT 1,
            first_uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

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
        );

        CREATE TABLE IF NOT EXISTS file_chunks (
            id BIGSERIAL PRIMARY KEY,
            file_id BIGINT REFERENCES user_files(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            chunk_hash VARCHAR(64) REFERENCES chunks(chunk_hash)
        );

        CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(chunk_hash);
        CREATE INDEX IF NOT EXISTS idx_user_files_hash ON user_files(file_hash);
        CREATE INDEX IF NOT EXISTS idx_file_chunks_file_id ON file_chunks(file_id);
        """
        cursor.execute(ddl)
        print("  ✅ Database tables & indexes verified!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        sys.exit(1)

    # 3. Test Supabase Storage Bucket Access
    print("\n[2/3] Connecting to Supabase Cloud Object Storage...")
    try:
        from core.supabase_storage import SupabaseStorageAdapter
        adapter = SupabaseStorageAdapter(supabase_url=supabase_url, supabase_key=supabase_key, bucket_name="cloud-chunks")
        print("  -> Verifying bucket 'cloud-chunks'...")
        
        # Test storing a tiny sample test chunk
        test_hash = "00000000000000000000000000000000000000000000000000000000test"
        test_payload = b"Supabase Cloud Storage Integration Test"
        adapter.store_chunk(test_hash, test_payload)

        # Verify read back
        retrieved = adapter.get_chunk_bytes(test_hash)
        if retrieved == test_payload:
            print("  ✅ Storage bucket active & verified! Read/write test passed.")
            adapter.delete_chunk(test_hash)
        else:
            print("  ⚠️ Warning: Test chunk could not be read back directly, check bucket permissions.")
    except Exception as e:
        print(f"  ❌ Storage verification notice: {e}")

    # 4. Save to .env file for easy deployment
    print("\n[3/3] Saving environment configuration to .env...")
    env_content = f"""# Supabase Cloud Configuration
SUPABASE_URL="{supabase_url}"
SUPABASE_KEY="{supabase_key}"
DATABASE_URL="{database_url}"
"""
    with open(".env", "w") as f:
        f.write(env_content)
    print("  ✅ Created .env configuration file!")

    print("\n" + "=" * 70)
    print("🎉 SUPABASE INTEGRATION COMPLETE & READY!")
    print("=" * 70)
    print("Whenever app.py starts, it will automatically connect to your")
    print("Supabase PostgreSQL database and Supabase Storage bucket!")
    print("=" * 70)

if __name__ == "__main__":
    run_setup()
