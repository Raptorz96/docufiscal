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
from app.schemas.documento import ClassificazioneOverride, DocumentoOut, DocumentoUpdate
from app.storage import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documenti", tags=["documenti"])


@router.post(
    "/upload",
    response_model=DocumentoOut,
    status_code=status.HTTP_201_CREATED,
)
def upload_documento(
    cliente_id: Optional[int] = Form(None),
    contratto_id: Optional[int] = Form(None),
    tipo_documento: str = Form("altro"),
    note: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentoOut:
    """Upload a document and associate it with a client and optionally a contract.
    If cliente_id is not provided, AI will attempt to find a match via tax code (CF/PI).
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

    # --- Validate cliente (if provided) ---
    if cliente_id is not None:
        cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente {cliente_id} not found",
            )

    # --- Validate contratto (if provided) ---
    if contratto_id is not None:
        contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()
        if not contratto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contratto {contratto_id} not found",
            )
        if cliente_id and contratto.cliente_id != cliente_id:
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

    # --- Save file to storage (temporary if no cliente_id) ---
    file_path, file_size = storage_service.save_file(file, cliente_id, contratto_id)

    # --- Check size limit ---
    if file_size > settings.MAX_UPLOAD_SIZE:
        storage_service.delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {file_size} bytes.",
        )

    mime_type = storage_service.get_mime_type(file.filename or "")
    if mime_type == "application/octet-stream" and mime_for_check:
        mime_type = mime_for_check

    # --- Save file to storage (temporary if no cliente_id) ---
    file_path, file_size = storage_service.save_file(file, cliente_id, contratto_id)

    # --- Check size limit ---
    if file_size > settings.MAX_UPLOAD_SIZE:
        storage_service.delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {file_size} bytes.",
        )

    mime_type = storage_service.get_mime_type(file.filename or "")
    if mime_type == "application/octet-stream" and mime_for_check:
        mime_type = mime_for_check

    # --- Classification and Match (Mandatory if cliente_id missing) ---
    abs_path = storage_service.get_file_path(file_path)
    extracted_text = ""
    try:
        extracted_text = text_extraction_service.extract_text(abs_path, mime_type)
    except Exception as e:
        logger.error("Text extraction failed: %s", str(e))

    classification_result = None
    matched_cliente_id = cliente_id

    if extracted_text.strip():
        # Prepare context for AI
        clienti_all = db.query(Cliente).all()
        clienti_context = [
            {"nome": c.nome, "cognome": c.cognome, "codice_fiscale": c.codice_fiscale}
            for c in clienti_all
        ]
        
        available_types = [e.value for e in TipoDocumento]
        classifier = get_classifier()
        classification_result = classifier.classify(
            text=extracted_text,
            available_types=available_types,
            clienti_context=clienti_context
        )

        # --- Local Matching Logic ---
        if matched_cliente_id is None:
            cf = classification_result.codice_fiscale
            pi = classification_result.partita_iva
            
            # Try match by CF
            if cf:
                found = db.query(Cliente).filter(Cliente.codice_fiscale == cf).first()
                if found:
                    matched_cliente_id = found.id
                    logger.info("Auto-matched client by CODE_FISCALE: %s -> %d", cf, found.id)
            
            # Try match by PI if CF didn't work
            if not matched_cliente_id and pi:
                found = db.query(Cliente).filter(Cliente.partita_iva == pi).first()
                if found:
                    matched_cliente_id = found.id
                    logger.info("Auto-matched client by PARTITA_IVA: %s -> %d", pi, found.id)

    # --- Final validation of cliente_id ---
    if matched_cliente_id is None:
        storage_service.delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile associare il documento a un cliente. Per favore selezionalo manualmente."
        )

    # --- Use the matched client to check contratto ---
    if contratto_id and not cliente_id:
        # We need to verify the found client owns the contract if provided
        contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()
        if contratto and contratto.cliente_id != matched_cliente_id:
            storage_service.delete_file(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Il contratto {contratto_id} non appartiene al cliente identificato ({matched_cliente_id})"
            )

    # --- Relocate file if it was unassigned ---
    if cliente_id is None:
        try:
            old_path = file_path
            file_path = storage_service.move_file(old_path, matched_cliente_id, contratto_id)
            logger.info("Relocated file from unassigned to client %d", matched_cliente_id)
        except Exception as e:
            logger.error("Failed to relocate file: %s", str(e))
            # Continue with old path if move fails, but ideally it shouldn't

    # --- Persist DB record ---
    try:
        documento = Documento(
            cliente_id=matched_cliente_id,
            contratto_id=contratto_id,
            tipo_documento=tipo_doc_enum.value,
            file_name=file.filename or "unknown",
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            note=note,
        )
        
        if classification_result:
            documento.classificazione_ai = classification_result.raw_response
            documento.confidence_score = classification_result.confidence
            documento.tipo_documento_raw = classification_result.tipo_documento_raw
            
            # Apply auto-classification if confidence is high and user didn't specify one
            if (classification_result.confidence >= settings.CONFIDENCE_THRESHOLD 
                and tipo_documento == "altro"):
                documento.tipo_documento = classification_result.tipo_documento

        db.add(documento)
        db.commit()
        db.refresh(documento)
        return DocumentoOut.model_validate(documento)
    except Exception:
        db.rollback()
        storage_service.delete_file(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document record",
        )


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


@router.patch("/{documento_id}/classifica", response_model=DocumentoOut)
def classifica_documento(
    documento_id: int,
    body: ClassificazioneOverride,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentoOut:
    """Confirm or override the AI classification of a document.

    Args:
        documento_id: ID of the document to classify.
        body: Classification override payload.
        db: Database session dependency.
        current_user: Current authenticated user.

    Returns:
        DocumentoOut: The updated document record.

    Raises:
        HTTPException 400: If the contratto does not belong to the specified cliente.
        HTTPException 404: If the document, cliente, or contratto is not found.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {documento_id} not found",
        )

    # Determine effective cliente_id
    if body.cliente_id is not None:
        cliente = db.query(Cliente).filter(Cliente.id == body.cliente_id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente {body.cliente_id} not found",
            )
        effective_cliente_id = body.cliente_id
    else:
        effective_cliente_id = documento.cliente_id

    # Handle contratto_id only when explicitly included in the request body
    if "contratto_id" in body.model_fields_set:
        if body.contratto_id is None:
            documento.contratto_id = None
        else:
            contratto = db.query(Contratto).filter(Contratto.id == body.contratto_id).first()
            if not contratto:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contratto {body.contratto_id} not found",
                )
            if contratto.cliente_id != effective_cliente_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Il contratto non appartiene al cliente specificato",
                )
            documento.contratto_id = body.contratto_id

    documento.verificato_da_utente = True
    documento.cliente_id = effective_cliente_id

    if body.tipo_documento is not None:
        documento.tipo_documento = body.tipo_documento.value

    if "note" in body.model_fields_set:
        documento.note = body.note

    db.commit()
    db.refresh(documento)

    logger.info(
        "Documento %d classificato manualmente: tipo=%s, verificato=True, utente=%s",
        documento.id,
        documento.tipo_documento,
        current_user.email,
    )

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
