"""API endpoints for document upload and management."""
import logging
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.ai import get_classifier, text_extraction_service
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento, TipoDocumento
from app.models.user import User
from app.schemas.documento import DocumentoOut, DocumentoUpdate
from app.storage import storage_service

logger = logging.getLogger(__name__)

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

    # --- AI Classification (non-blocking: errors only log, document stays saved) ---
    try:
        abs_path = storage_service.get_file_path(documento.file_path)
        extracted_text = text_extraction_service.extract_text(
            abs_path, documento.mime_type
        )

        if extracted_text.strip():
            clienti = db.query(Cliente).all()
            clienti_context = [
                {
                    "nome": c.nome,
                    "cognome": c.cognome,
                    "codice_fiscale": c.codice_fiscale,
                }
                for c in clienti
            ]

            available_types = [e.value for e in TipoDocumento]
            classifier = get_classifier()
            result = classifier.classify(
                text=extracted_text,
                available_types=available_types,
                clienti_context=clienti_context,
            )

            documento.classificazione_ai = result.raw_response
            documento.confidence_score = result.confidence
            documento.tipo_documento_raw = result.tipo_documento_raw

            if (
                result.confidence >= settings.CONFIDENCE_THRESHOLD
                and tipo_documento == "altro"
            ):
                documento.tipo_documento = result.tipo_documento

            db.commit()
            db.refresh(documento)

            logger.info(
                "AI classification for documento %d: tipo=%s, confidence=%.2f",
                documento.id,
                result.tipo_documento,
                result.confidence,
            )
        else:
            logger.warning(
                "No text extracted from documento %d, skipping AI classification",
                documento.id,
            )

    except Exception:
        logger.exception(
            "AI classification failed for documento %d, document saved without classification",
            documento.id,
        )

    return DocumentoOut.model_validate(documento)


@router.get("/", response_model=list[DocumentoOut])
def list_documenti(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cliente_id: Optional[int] = Query(None, description="Filter by cliente_id"),
    contratto_id: Optional[int] = Query(None, description="Filter by contratto_id"),
    tipo_documento: Optional[str] = Query(None, description="Filter by tipo_documento"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return"),
) -> list[DocumentoOut]:
    """List documents with optional filters, ordered by most recent first.

    Args:
        db: Database session dependency.
        current_user: Current authenticated user.
        cliente_id: Optional filter by client ID.
        contratto_id: Optional filter by contract ID.
        tipo_documento: Optional filter by document type.
        skip: Pagination offset.
        limit: Maximum number of results (capped at 500).

    Returns:
        list[DocumentoOut]: Matching documents, newest first.
    """
    query = db.query(Documento)

    if cliente_id is not None:
        query = query.filter(Documento.cliente_id == cliente_id)
    if contratto_id is not None:
        query = query.filter(Documento.contratto_id == contratto_id)
    if tipo_documento is not None:
        query = query.filter(Documento.tipo_documento == tipo_documento)

    documenti = (
        query
        .order_by(Documento.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [DocumentoOut.model_validate(d) for d in documenti]


@router.get("/{documento_id}", response_model=DocumentoOut)
def get_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentoOut:
    """Get a single document by ID.

    Args:
        documento_id: ID of the document to retrieve.
        db: Database session dependency.
        current_user: Current authenticated user.

    Returns:
        DocumentoOut: The document record.

    Raises:
        HTTPException 404: If the document does not exist.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {documento_id} not found",
        )
    return DocumentoOut.model_validate(documento)


@router.put("/{documento_id}", response_model=DocumentoOut)
def update_documento(
    documento_id: int,
    update_data: DocumentoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentoOut:
    """Update document metadata. File fields (file_name, file_path, file_size, mime_type) are immutable.

    Args:
        documento_id: ID of the document to update.
        update_data: Fields to update (only non-None values are applied).
        db: Database session dependency.
        current_user: Current authenticated user.

    Returns:
        DocumentoOut: The updated document record.

    Raises:
        HTTPException 400: If the new contratto_id does not belong to the document's cliente.
        HTTPException 404: If the document or new contratto_id is not found.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {documento_id} not found",
        )

    # Validate new contratto_id if being changed
    if update_data.contratto_id is not None:
        contratto = db.query(Contratto).filter(Contratto.id == update_data.contratto_id).first()
        if not contratto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contratto {update_data.contratto_id} not found",
            )
        if contratto.cliente_id != documento.cliente_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Contratto {update_data.contratto_id} does not belong to "
                    f"cliente {documento.cliente_id}"
                ),
            )

    fields: Dict[str, Any] = update_data.model_dump(exclude_unset=True)
    for field, value in fields.items():
        setattr(documento, field, value)

    db.commit()
    db.refresh(documento)
    return DocumentoOut.model_validate(documento)


@router.delete("/{documento_id}", status_code=status.HTTP_200_OK)
def delete_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Delete a document record and its file from the filesystem.

    The DB record is deleted first; only on success is the file removed.
    This prevents orphaned DB records if storage deletion fails.

    Args:
        documento_id: ID of the document to delete.
        db: Database session dependency.
        current_user: Current authenticated user.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException 404: If the document does not exist.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {documento_id} not found",
        )

    file_path = documento.file_path
    db.delete(documento)
    db.commit()

    storage_service.delete_file(file_path)

    return {"detail": "Documento eliminato"}


_DOWNLOAD_CHUNK_SIZE = 8 * 1024  # 8 KB


@router.get("/{documento_id}/download")
def download_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a document file to the client as an attachment.

    Args:
        documento_id: ID of the document to download.
        db: Database session dependency.
        current_user: Current authenticated user.

    Returns:
        StreamingResponse: File content streamed in 8 KB chunks.

    Raises:
        HTTPException 404: If the document record or the file on disk is not found.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {documento_id} not found",
        )

    try:
        absolute_path: Path = storage_service.get_file_path(documento.file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found on filesystem: {documento.file_name}",
        )

    def file_generator() -> Generator[bytes, None, None]:
        with absolute_path.open("rb") as f:
            while chunk := f.read(_DOWNLOAD_CHUNK_SIZE):
                yield chunk

    safe_name = documento.file_name.replace('"', '\\"')
    encoded_name = quote(documento.file_name)
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_name}"; filename*=UTF-8\'\'{encoded_name}',
        "Content-Length": str(documento.file_size),
    }
    return StreamingResponse(
        file_generator(),
        media_type=documento.mime_type,
        headers=headers,
    )
