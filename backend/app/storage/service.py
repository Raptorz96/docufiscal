"""Storage service for managing document files on the local filesystem."""
import logging
import mimetypes
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

_CHUNK_SIZE = 8 * 1024  # 8 KB


class StorageService:
    """Handles save, read and delete of uploaded document files."""

    def __init__(self, storage_root: str) -> None:
        self._root = Path(storage_root)

    def save_file(
        self,
        file: UploadFile,
        cliente_id: int,
        contratto_id: int | None,
    ) -> tuple[str, int]:
        """Save an uploaded file to the filesystem.

        Builds path: {STORAGE_ROOT}/{cliente_id}/{contratto_id or "senza_contratto"}/{uuid}_{filename}

        Args:
            file: FastAPI UploadFile instance.
            cliente_id: ID of the owning client.
            contratto_id: ID of the associated contract, or None.

        Returns:
            Tuple of (relative_file_path, file_size_bytes).
            The relative path is relative to STORAGE_ROOT and is what gets stored in DB.
        """
        bucket = str(contratto_id) if contratto_id is not None else "senza_contratto"
        prefix = uuid.uuid4().hex[:12]
        safe_name = Path(file.filename or "file").name  # strip any directory component
        relative_path = Path(str(cliente_id)) / bucket / f"{prefix}_{safe_name}"
        absolute_path = self._root / relative_path

        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        file_size = 0
        with absolute_path.open("wb") as dest:
            shutil.copyfileobj(file.file, dest, length=_CHUNK_SIZE)

        file_size = absolute_path.stat().st_size
        relative_str = relative_path.as_posix()
        logger.info("Saved file %s (%d bytes)", relative_str, file_size)
        return relative_str, file_size

    def get_file_path(self, relative_path: str) -> Path:
        """Return the absolute Path for a stored file.

        Args:
            relative_path: Path relative to STORAGE_ROOT as stored in DB.

        Returns:
            Absolute Path object.

        Raises:
            FileNotFoundError: If the file does not exist on disk.
        """
        absolute_path = self._root / relative_path
        if not absolute_path.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return absolute_path

    def delete_file(self, relative_path: str) -> bool:
        """Delete a stored file from the filesystem.

        Args:
            relative_path: Path relative to STORAGE_ROOT as stored in DB.

        Returns:
            True if the file was deleted, False if it did not exist.
        """
        absolute_path = self._root / relative_path
        if not absolute_path.is_file():
            logger.warning("delete_file: file not found, skipping: %s", relative_path)
            return False
        absolute_path.unlink()
        logger.info("Deleted file %s", relative_path)
        return True

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """Guess MIME type from filename.

        Args:
            filename: Original filename with extension.

        Returns:
            MIME type string, defaults to 'application/octet-stream'.
        """
        mime, _ = mimetypes.guess_type(filename)
        return mime or "application/octet-stream"


storage_service = StorageService(settings.STORAGE_ROOT)
