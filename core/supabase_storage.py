import os
import shutil
import io
from typing import BinaryIO, Optional, Union
import requests


class SupabaseStorageAdapter:
    """
    Supabase S3-Compatible Cloud Object Storage Adapter.
    Stores content-addressable binary chunks in a remote Supabase Storage bucket.
    Includes smart local caching to accelerate repeated reads and stream reconstruction.
    """

    def __init__(self, supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None,
                 bucket_name: str = "cloud-chunks",
                 cache_dir: str = "cloud_storage_bucket/cache"):
        self.supabase_url = (supabase_url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.bucket_name = bucket_name
        self.cache_dir = os.path.abspath(cache_dir)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.session = requests.Session()
        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}"
        }
        if self.is_configured:
            self._ensure_bucket()

    @property
    def is_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    def _ensure_bucket(self):
        """Ensures the storage bucket exists in Supabase."""
        try:
            url = f"{self.supabase_url}/storage/v1/bucket"
            res = self.session.get(url, headers=self.headers, timeout=5)
            if res.status_code == 200:
                existing_buckets = [b.get("id") or b.get("name") for b in res.json()]
                if self.bucket_name not in existing_buckets:
                    create_url = f"{self.supabase_url}/storage/v1/bucket"
                    payload = {"id": self.bucket_name, "name": self.bucket_name, "public": True}
                    self.session.post(create_url, json=payload, headers=self.headers, timeout=5)
        except Exception as e:
            print(f"[SupabaseStorageAdapter] Bucket check notice: {e}")

    def _get_cache_path(self, file_hash: str) -> str:
        return os.path.join(self.cache_dir, file_hash)

    def chunk_exists(self, file_hash: str) -> bool:
        """Checks if a chunk with the given hash exists either in cache or remote Supabase bucket."""
        if os.path.isfile(self._get_cache_path(file_hash)):
            return True

        if not self.is_configured:
            return False

        try:
            url = f"{self.supabase_url}/storage/v1/object/list/{self.bucket_name}"
            res = self.session.post(url, json={"prefix": file_hash, "limit": 1}, headers=self.headers, timeout=5)
            if res.status_code == 200:
                files = res.json()
                return any(f.get("name") == file_hash for f in files)
        except Exception:
            pass
        return False

    def store_chunk(self, file_hash: str, data_or_stream: Union[bytes, BinaryIO]) -> int:
        """Stores chunk both in local cache and remote Supabase Storage."""
        if isinstance(data_or_stream, bytes):
            payload = data_or_stream
        else:
            if hasattr(data_or_stream, "seek"):
                data_or_stream.seek(0)
            payload = data_or_stream.read()

        cache_path = self._get_cache_path(file_hash)
        with open(cache_path, "wb") as f_out:
            f_out.write(payload)

        # Upload to Supabase Storage if configured
        if self.is_configured:
            try:
                url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{file_hash}"
                upload_headers = dict(self.headers)
                upload_headers["Content-Type"] = "application/octet-stream"
                upload_headers["x-upsert"] = "true"
                self.session.post(url, data=payload, headers=upload_headers, timeout=10)
            except Exception as e:
                print(f"[SupabaseStorageAdapter] Remote upload warning: {e}")

        return len(payload)

    def get_chunk_bytes(self, file_hash: str) -> Optional[bytes]:
        """Reads chunk from local cache or pulls from Supabase Storage."""
        cache_path = self._get_cache_path(file_hash)
        if os.path.isfile(cache_path):
            with open(cache_path, "rb") as f_in:
                return f_in.read()

        if not self.is_configured:
            return None

        try:
            url = f"{self.supabase_url}/storage/v1/object/authenticated/{self.bucket_name}/{file_hash}"
            res = self.session.get(url, headers=self.headers, timeout=10)
            if res.status_code == 200:
                with open(cache_path, "wb") as f_out:
                    f_out.write(res.content)
                return res.content
        except Exception:
            pass
        return None

    def get_chunk_stream(self, file_hash: str) -> Optional[BinaryIO]:
        data = self.get_chunk_bytes(file_hash)
        if data is not None:
            return io.BytesIO(data)
        return None

    def delete_chunk(self, file_hash: str) -> bool:
        cache_path = self._get_cache_path(file_hash)
        if os.path.isfile(cache_path):
            os.remove(cache_path)

        if not self.is_configured:
            return True

        try:
            url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}"
            self.session.delete(url, json={"prefixes": [file_hash]}, headers=self.headers, timeout=5)
            return True
        except Exception:
            return False

    def clear_bucket(self):
        if os.path.exists(self.cache_dir):
            shutil.rmtree(self.cache_dir)
            os.makedirs(self.cache_dir, exist_ok=True)

        if not self.is_configured:
            return

        try:
            list_url = f"{self.supabase_url}/storage/v1/object/list/{self.bucket_name}"
            res = self.session.post(list_url, json={"limit": 500}, headers=self.headers, timeout=5)
            if res.status_code == 200:
                names = [f.get("name") for f in res.json() if f.get("name")]
                if names:
                    del_url = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}"
                    self.session.delete(del_url, json={"prefixes": names}, headers=self.headers, timeout=5)
        except Exception:
            pass
