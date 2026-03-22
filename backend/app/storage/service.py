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
        cliente_id: int | None,
        contratto_id: int | None,
    ) -> tuple[str, int]:
        """Save an uploaded file to the filesystem.

        Builds path: {STORAGE_ROOT}/{cliente_id or "unassigned"}/{contratto_id or "senza_contratto"}/{uuid}_{filename}

        Args:
            file: FastAPI UploadFile instance.
            cliente_id: ID of the owning client, or None for auto-matching.
            contratto_id: ID of the associated contract, or None.

        Returns:
            Tuple of (relative_file_path, file_size_bytes).
        """
        folder_cliente = str(cliente_id) if cliente_id is not None else "unassigned"
        bucket = str(contratto_id) if contratto_id is not None else "senza_contratto"
        prefix = uuid.uuid4().hex[:12]
        safe_name = Path(file.filename or "file").name
        relative_path = Path(folder_cliente) / bucket / f"{prefix}_{safe_name}"
        absolute_path = self._root / relative_path

        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        with absolute_path.open("wb") as dest:
            shutil.copyfileobj(file.file, dest, length=_CHUNK_SIZE)

        file_size = absolute_path.stat().st_size
        relative_str = relative_path.as_posix()
        return relative_str, file_size

    def move_file(
        self,
        old_relative_path: str,
        new_cliente_id: int,
        new_contratto_id: int | None = None,
    ) -> str:
        """Move an existing file to a new client/contract directory structure.

        Args:
            old_relative_path: Current relative path in storage.
            new_cliente_id: Target client ID.
            new_contratto_id: Target contract ID, or None.

        Returns:
            New relative path.
        """
        old_absolute = self.get_file_path(old_relative_path)
        
        folder_cliente = str(new_cliente_id)
        bucket = str(new_contratto_id) if new_contratto_id is not None else "senza_contratto"
        
        # Keep the same filename (including prefix)
        filename = Path(old_relative_path).name
        new_relative = Path(folder_cliente) / bucket / filename
        new_absolute = self._root / new_relative
        
        new_absolute.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(old_absolute), str(new_absolute))
        
        return new_relative.as_posix()

    def _validate_path(self, relative_path: str) -> Path:
        """Resolve absolute path and ensure it's within STORAGE_ROOT.

        Args:
            relative_path: Path relative to STORAGE_ROOT as stored in DB.

        Returns:
            Resolved absolute Path.

        Raises:
            ValueError: If the resolved path escapes STORAGE_ROOT (path traversal).
        """
        absolute_path = (self._root / relative_path).resolve()
        if not str(absolute_path).startswith(str(self._root.resolve())):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return absolute_path

    def get_file_path(self, relative_path: str) -> Path:
        """Return the absolute Path for a stored file.

        Args:
            relative_path: Path relative to STORAGE_ROOT as stored in DB.

        Returns:
            Absolute Path object.

        Raises:
            ValueError: If path traversal is detected.
            FileNotFoundError: If the file does not exist on disk.
        """
        absolute_path = self._validate_path(relative_path)
        if not absolute_path.is_file():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return absolute_path

    def delete_file(self, relative_path: str) -> bool:
        """Delete a stored file from the filesystem.

        Args:
            relative_path: Path relative to STORAGE_ROOT as stored in DB.

        Returns:
            True if the file was deleted, False if it did not exist.

        Raises:
            ValueError: If path traversal is detected.
        """
        absolute_path = self._validate_path(relative_path)
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
