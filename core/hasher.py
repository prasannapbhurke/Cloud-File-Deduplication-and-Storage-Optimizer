import hashlib
import io
from typing import BinaryIO, Union


class SHA256Hasher:
    """
    Streaming SHA-256 Cryptographic Hash Engine.
    Processes file streams in 64 KB chunks to maintain low memory footprint
    even with large files.
    """
    CHUNK_SIZE = 65536  # 64 KB

    @classmethod
    def compute_hash(cls, file_obj_or_bytes: Union[BinaryIO, bytes, io.BytesIO]) -> str:
        """
        Computes the SHA-256 cryptographic digest of a file stream or byte buffer.
        Returns a 64-character lowercase hexadecimal string.
        """
        hasher = hashlib.sha256()

        if isinstance(file_obj_or_bytes, bytes):
            hasher.update(file_obj_or_bytes)
            return hasher.hexdigest()

        # Handle stream / file-like object
        current_pos = None
        if hasattr(file_obj_or_bytes, "tell") and hasattr(file_obj_or_bytes, "seek"):
            try:
                current_pos = file_obj_or_bytes.tell()
                file_obj_or_bytes.seek(0)
            except Exception:
                current_pos = None

        while True:
            chunk = file_obj_or_bytes.read(cls.CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)

        # Restore original stream position if applicable
        if current_pos is not None and hasattr(file_obj_or_bytes, "seek"):
            file_obj_or_bytes.seek(current_pos)

        return hasher.hexdigest()

    @classmethod
    def verify_hash(cls, file_obj_or_bytes: Union[BinaryIO, bytes], expected_hash: str) -> bool:
        """
        Verifies if the stream matches the expected SHA-256 hash.
        """
        computed = cls.compute_hash(file_obj_or_bytes)
        return computed.lower() == expected_hash.lower()
