"""API endpoints for document upload and management."""
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento, TipoDocumento
from app.models.user import User
from app.schemas.documento import DocumentoOut
from app.storage import storage_service

router = APIRouter(prefix="/documenti", tags=["documenti"])


@router.post(
    "/upload",
    response_model=DocumentoOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_documento(
    cliente_id: int = Form(...),
    contratto_id: Optional[int] = Form(None),
    tipo_documento: str = Form("altro"),
    note: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentoOut:
    """Upload a document and associate it with a client and optionally a contract.

    Args:
        cliente_id: ID of the owning client (required).
        contratto_id: ID of the associated contract (optional).
        tipo_documento: Document type from TipoDocumento enum (default: "altro").
        note: Optional free-text notes.
        file: The file to upload (multipart/form-data).
        db: Database session dependency.
        current_user: Current authenticated user.

    Returns:
        DocumentoOut: The created document record.

    Raises:
        HTTPException 400: Invalid tipo_documento, MIME type not allowed, or
            contratto does not belong to the given cliente.
        HTTPException 404: Cliente or contratto not found.
        HTTPException 413: File exceeds MAX_UPLOAD_SIZE.
    """
    # --- Validate tipo_documento enum ---
    try:
        tipo_doc_enum = TipoDocumento(tipo_documento)
    except ValueError:
        valid = [e.value for e in TipoDocumento]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tipo_documento: '{tipo_documento}'. Valid values: {valid}",
        )

    # --- Validate cliente exists ---
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente {cliente_id} not found",
        )

    # --- Validate contratto (if provided) exists and belongs to cliente ---
    if contratto_id is not None:
        contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()
        if not contratto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contratto {contratto_id} not found",
            )
        if contratto.cliente_id != cliente_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contratto {contratto_id} does not belong to cliente {cliente_id}",
            )

    # --- Validate MIME type ---
    raw_content_type = file.content_type or ""
    mime_for_check = raw_content_type.split(";")[0].strip()
    if mime_for_check not in settings.ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed: '{mime_for_check}'. Allowed: {settings.ALLOWED_MIME_TYPES}",
        )

    # --- Save file to storage ---
    file_path, file_size = storage_service.save_file(file, cliente_id, contratto_id)

    # --- Check size limit (after save — content-length is unreliable for multipart) ---
    if file_size > settings.MAX_UPLOAD_SIZE:
        storage_service.delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File too large: {file_size} bytes. "
                f"Maximum allowed: {settings.MAX_UPLOAD_SIZE} bytes."
            ),
        )

    # --- Determine MIME type for storage ---
    # Prefer filename-based detection; fall back to what the client reported.
    mime_type = storage_service.get_mime_type(file.filename or "")
    if mime_type == "application/octet-stream" and mime_for_check:
        mime_type = mime_for_check

    # --- Persist DB record ---
    try:
        documento = Documento(
            cliente_id=cliente_id,
            contratto_id=contratto_id,
            tipo_documento=tipo_doc_enum.value,
            file_name=file.filename or "unknown",
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            note=note,
        )
        db.add(documento)
        db.commit()
        db.refresh(documento)
    except Exception:
        db.rollback()
        storage_service.delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document record",
        )

    return DocumentoOut.model_validate(documento)
