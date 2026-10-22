import os
import shutil
from typing import BinaryIO, Optional, Union


class CloudStorageAdapter:
    """
    Cloud Object Storage Adapter.
    Provides Content-Addressable Storage (CAS) semantics compatible with AWS S3,
    Google Cloud Storage, or MinIO.
    Stores unique file payloads addressed by their SHA-256 hash digest.
    """

    def __init__(self, bucket_dir: str = "cloud_storage_bucket"):
        self.bucket_dir = os.path.abspath(bucket_dir)
        self.chunks_dir = os.path.join(self.bucket_dir, "chunks")
        os.makedirs(self.chunks_dir, exist_ok=True)

    def chunk_exists(self, file_hash: str) -> bool:
        """Checks if a chunk with the given SHA-256 hash is physically stored."""
        chunk_path = self.get_chunk_path(file_hash)
        return os.path.isfile(chunk_path)

    def get_chunk_path(self, file_hash: str) -> str:
        """Returns the absolute path to the stored chunk object."""
        return os.path.join(self.chunks_dir, file_hash)

    def store_chunk(self, file_hash: str, data_or_stream: Union[bytes, BinaryIO]) -> int:
        """
        Stores unique payload into the cloud bucket under /chunks/<file_hash>.
        Accepts either raw bytes or a stream.
        Returns the number of physical bytes written.
        """
        chunk_path = self.get_chunk_path(file_hash)

        if isinstance(data_or_stream, bytes):
            with open(chunk_path, "wb") as f_out:
                f_out.write(data_or_stream)
            return len(data_or_stream)

        # Rewind stream before saving if applicable
        if hasattr(data_or_stream, "seek"):
            data_or_stream.seek(0)

        bytes_written = 0
        with open(chunk_path, "wb") as f_out:
            while True:
                buf = data_or_stream.read(65536)
                if not buf:
                    break
                f_out.write(buf)
                bytes_written += len(buf)

        return bytes_written

    def get_chunk_bytes(self, file_hash: str) -> Optional[bytes]:
        """Reads and returns the raw bytes for the stored chunk."""
        chunk_path = self.get_chunk_path(file_hash)
        if not os.path.isfile(chunk_path):
            return None
        with open(chunk_path, "rb") as f_in:
            return f_in.read()

    def get_chunk_stream(self, file_hash: str) -> Optional[BinaryIO]:
        """Opens and returns a binary read stream for the stored chunk."""
        chunk_path = self.get_chunk_path(file_hash)
        if not os.path.isfile(chunk_path):
            return None
        return open(chunk_path, "rb")

    def delete_chunk(self, file_hash: str) -> bool:
        """Permanently purges a chunk from cloud storage when ref_count reaches 0."""
        chunk_path = self.get_chunk_path(file_hash)
        if os.path.isfile(chunk_path):
            os.remove(chunk_path)
            return True
        return False

    def clear_bucket(self):
        """Purges all stored chunks from the cloud bucket."""
        if os.path.exists(self.chunks_dir):
            shutil.rmtree(self.chunks_dir)
            os.makedirs(self.chunks_dir, exist_ok=True)
