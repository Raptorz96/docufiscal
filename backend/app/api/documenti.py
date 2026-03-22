"""API endpoints for document upload and management."""
import logging
from pathlib import Path
from typing import Any, Dict, Generator, Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from app.ai import extract_short_id, get_classifier, text_extraction_service
from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento, MacroCategoria, TipoDocumento
from app.models.user import User
from app.schemas.documento import ClassificazioneOverride, DocumentoOut, DocumentoUpdate
from app.storage import storage_service

logger = logging.getLogger(__name__)

from app.ai.routing import regex_router
import anyio

router = APIRouter(prefix="/documenti", tags=["documenti"])


@router.post(
    "/upload",
    response_model=DocumentoOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_documento(
    cliente_id: Optional[int] = Form(None),
    contratto_id: Optional[int] = Form(None),
    tipo_documento: str = Form("altro"),
    note: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentoOut:
    """Upload a document and associate it with a client and optionally a contract.
    If cliente_id is not provided, Regex/AI will attempt to find a match.
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

    matched_cliente_id = cliente_id

    # --- Level 1: Deterministic Routing (Short ID) ---
    short_id_from_file = extract_short_id(file.filename or "")
    if matched_cliente_id is None and short_id_from_file is not None:
        cliente_by_short = db.query(Cliente).filter(Cliente.short_id == short_id_from_file).first()
        if cliente_by_short:
            matched_cliente_id = cliente_by_short.id
            logger.info("Level 1 Match: Client found by short_id %d", short_id_from_file)

    # --- Validate cliente (if provided or matched) ---
    if matched_cliente_id is not None:
        cliente = db.query(Cliente).filter(Cliente.id == matched_cliente_id).first()
        if not cliente:
            if cliente_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Cliente {matched_cliente_id} not found",
                )
            matched_cliente_id = None

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

    # --- Save file to storage (temporary if no cliente_id matched) ---
    # Run synchronous storage call in a thread
    file_path, file_size = await anyio.to_thread.run_sync(
        storage_service.save_file, file, matched_cliente_id, contratto_id
    )

    # --- Check size limit ---
    if file_size > settings.MAX_UPLOAD_SIZE:
        await anyio.to_thread.run_sync(storage_service.delete_file, file_path)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {file_size} bytes.",
        )

    mime_type = storage_service.get_mime_type(file.filename or "")
    if mime_type == "application/octet-stream" and mime_for_check:
        mime_type = mime_for_check

    abs_path = storage_service.get_file_path(file_path)
    
    # --- Level 2: Regex Routing (P.IVA / CF) ---
    regex_matched = False
    if matched_cliente_id is None:
        matched_cliente = await regex_router.find_client_by_regex(db, file_path, mime_type)
        if matched_cliente:
            matched_cliente_id = matched_cliente.id
            regex_matched = True
            logger.info("Level 2 Match: Client found by Regex routing (ID: %d)", matched_cliente_id)

    # --- Classification and Match (Mandatory if cliente_id missing) ---
    extracted_text = ""
    try:
        # Full text extraction for embeddings and classification
        extracted_text = await anyio.to_thread.run_sync(
            text_extraction_service.extract_text, file_path, mime_type
        )
    except Exception as e:
        logger.error("Text extraction failed: %s", str(e))

    classification_result = None

    if extracted_text.strip():
        # Prepare context for AI
        clienti_context = None
        # Skip client identification if already matched in Level 1 or 2
        if matched_cliente_id is None:
            clienti_all = db.query(Cliente).all()
            clienti_context = [
                {"nome": c.nome, "cognome": c.cognome, "codice_fiscale": c.codice_fiscale}
                for c in clienti_all
            ]
        
        available_types = [e.value for e in TipoDocumento]
        classifier = get_classifier()
        # Use async classification
        classification_result = await classifier.aclassify(
            text=extracted_text,
            available_types=available_types,
            clienti_context=clienti_context,
            skip_client_id=(matched_cliente_id is not None)
        )

        # --- Local matching fallback (if regex and level 1 failed) ---
        print(f"DATI ESTRATTI DALL'IA: {classification_result}")
        if matched_cliente_id is None:
            cf = classification_result.codice_fiscale
            pi = classification_result.partita_iva
            
            # Normalizzazione dati estratti
            if cf and isinstance(cf, str):
                cf = cf.replace(" ", "").strip().upper()
                if cf.startswith("IT"):
                    cf = cf[2:]
            if pi and isinstance(pi, str):
                pi = pi.replace(" ", "").strip().upper()
                if pi.startswith("IT"):
                    pi = pi[2:]
            
            if cf or pi:
                found = db.query(Cliente).filter(
                    or_(
                        Cliente.codice_fiscale == cf if cf else False,
                        Cliente.partita_iva == pi if pi else False
                    )
                ).first()
                if found:
                    matched_cliente_id = found.id
                    logger.info("Auto-matched client via AI: %s %s (ID: %d)", found.nome, found.cognome or "", found.id)

    # --- Use the matched client to check contratto ---
    if contratto_id and matched_cliente_id:
        # We need to verify the found client owns the contract if provided
        contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()
        if contratto and contratto.cliente_id != matched_cliente_id:
            await anyio.to_thread.run_sync(storage_service.delete_file, file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Il contratto {contratto_id} non appartiene al cliente identificato ({matched_cliente_id})"
            )

    # --- Relocate file if it was unassigned AND a match was found ---
    if cliente_id is None and matched_cliente_id is not None:
        try:
            old_path = file_path
            file_path = await anyio.to_thread.run_sync(
                storage_service.move_file, old_path, matched_cliente_id, contratto_id
            )
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
            macro_categoria=MacroCategoria.altro.value,
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
            documento.macro_categoria = classification_result.macro_categoria
            documento.anno_competenza = classification_result.anno_competenza
            
            # Apply auto-classification if confidence is high and user didn't specify one
            if (classification_result.confidence >= settings.CONFIDENCE_THRESHOLD 
                and tipo_documento == "altro"):
                documento.tipo_documento = classification_result.tipo_documento

        db.add(documento)
        db.commit()
        db.refresh(documento)
        
        # --- Index Document in VectorStore (for RAG) ---
        if extracted_text.strip():
            from app.ai.vector_store import vector_store
            await vector_store.add_document(
                text=extracted_text,
                document_id=documento.id,
                file_name=documento.file_name,
                cliente_id=documento.cliente_id,
                macro_categoria=documento.macro_categoria,
                anno_competenza=documento.anno_competenza
            )

        # --- Contract structured extraction (best-effort) ---
        if documento.tipo_documento == "contratto" and documento.cliente_id is not None and extracted_text.strip():
            try:
                from app.ai.contract_extractor import extract_contract_data
                from app.models.scadenza_contratto import ScadenzaContratto
                extraction = await anyio.to_thread.run_sync(
                    lambda: extract_contract_data(extracted_text)
                )
                if extraction.confidence > 0:
                    scadenza = ScadenzaContratto(
                        documento_id=documento.id,
                        cliente_id=documento.cliente_id,
                        data_inizio=extraction.data_inizio,
                        data_scadenza=extraction.data_scadenza,
                        durata=extraction.durata,
                        rinnovo_automatico=extraction.rinnovo_automatico,
                        preavviso_disdetta=extraction.preavviso_disdetta,
                        canone=extraction.canone,
                        parti_coinvolte=extraction.parti_coinvolte,
                        clausole_chiave=extraction.clausole_chiave,
                        confidence_score=extraction.confidence,
                    )
                    db.add(scadenza)
                    db.commit()
                    logger.info(
                        "Contract extraction saved for documento %d (confidence=%.2f)",
                        documento.id,
                        extraction.confidence,
                    )
            except Exception:
                logger.exception("Contract extraction failed for documento %d, skipping", documento.id)

        return DocumentoOut.model_validate(documento)
    except Exception:
        db.rollback()
        await anyio.to_thread.run_sync(storage_service.delete_file, file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document record",
        )


@router.get("", response_model=list[DocumentoOut])
def list_documenti(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cliente_id: Optional[int] = Query(None, description="Filter by cliente_id"),
    contratto_id: Optional[int] = Query(None, description="Filter by contratto_id"),
    tipo_documento: Optional[str] = Query(None, description="Filter by tipo_documento"),
    unassigned: bool = Query(False, description="Filter only unassigned documents (cliente_id is null)"),
    search: Optional[str] = Query(None, description="Search in file name"),
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
    if unassigned:
        query = query.filter(Documento.cliente_id == None)
    
    if tipo_documento is not None:
        query = query.filter(Documento.tipo_documento == tipo_documento)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Documento.file_name.ilike(search_term),
                Documento.tipo_documento_raw.ilike(search_term),
                Documento.note.ilike(search_term)
            )
        )

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


@router.patch("/{documento_id}", response_model=DocumentoOut)
async def update_documento(
    documento_id: int,
    update_data: DocumentoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentoOut:
    """Update document metadata with optional file relocation if cliente_id changes.

    Args:
        documento_id: ID of the document to update.
        update_data: Fields to update (only non-None values are applied).
        db: Database session dependency.
        current_user: Current authenticated user.

    Returns:
        DocumentoOut: The updated document record.

    Raises:
        HTTPException 400: If the new contratto_id does not belong to the target cliente.
        HTTPException 404: If the document, target cliente, or new contratto_id is not found.
    """
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento {documento_id} not found",
        )

    # Effective IDs for validation
    new_cliente_id = update_data.cliente_id if "cliente_id" in update_data.model_fields_set else documento.cliente_id
    new_contratto_id = update_data.contratto_id if "contratto_id" in update_data.model_fields_set else documento.contratto_id

    # Validate target cliente if being changed
    if update_data.cliente_id is not None and update_data.cliente_id != documento.cliente_id:
        cliente = db.query(Cliente).filter(Cliente.id == update_data.cliente_id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cliente {update_data.cliente_id} not found",
            )

    # Validate new contratto_id if being changed or if cliente changed
    if new_contratto_id is not None:
        contratto = db.query(Contratto).filter(Contratto.id == new_contratto_id).first()
        if not contratto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contratto {new_contratto_id} not found",
            )
        if contratto.cliente_id != new_cliente_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contratto {new_contratto_id} does not belong to cliente {new_cliente_id}",
            )

    # Relocate physical file if cliente_id or contratto_id changed
    cliente_changed = "cliente_id" in update_data.model_fields_set and update_data.cliente_id != documento.cliente_id
    contratto_changed = "contratto_id" in update_data.model_fields_set and update_data.contratto_id != documento.contratto_id
    
    if (cliente_changed or contratto_changed) and new_cliente_id is not None:
        try:
            old_path = documento.file_path
            new_path = storage_service.move_file(old_path, new_cliente_id, new_contratto_id)
            documento.file_path = new_path
            logger.info("Relocated file %d to client %s, contract %s", documento_id, new_cliente_id, new_contratto_id)
        except Exception as e:
            logger.error("Failed to relocate file: %s", str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to relocate physical file: {str(e)}"
            )

    # Apply remaining updates
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(documento, field, value)

    db.commit()
    db.refresh(documento)

    # --- Sync VectorStore metadata ---
    try:
        from app.ai.vector_store import vector_store
        await vector_store.update_metadata(
            document_id=documento.id,
            file_name=documento.file_name,
            cliente_id=documento.cliente_id,
            macro_categoria=documento.macro_categoria,
            anno_competenza=documento.anno_competenza,
        )
    except Exception as e:
        logger.error("Failed to sync VectorStore after update_documento %d: %s", documento.id, e)

    return DocumentoOut.model_validate(documento)


@router.patch("/{documento_id}/classifica", response_model=DocumentoOut)
async def classifica_documento(
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

    if body.macro_categoria is not None:
        documento.macro_categoria = body.macro_categoria.value
    
    if "anno_competenza" in body.model_fields_set:
        documento.anno_competenza = body.anno_competenza

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

    # --- Sync VectorStore metadata ---
    try:
        from app.ai.vector_store import vector_store
        await vector_store.update_metadata(
            document_id=documento.id,
            file_name=documento.file_name,
            cliente_id=documento.cliente_id,
            macro_categoria=documento.macro_categoria,
            anno_competenza=documento.anno_competenza,
        )
    except Exception as e:
        logger.error("Failed to sync VectorStore after classifica_documento %d: %s", documento.id, e)

    return DocumentoOut.model_validate(documento)


@router.delete("/{documento_id}", status_code=status.HTTP_200_OK)
async def delete_documento(
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

    # --- Delete from ChromaDB ---
    from app.ai.vector_store import vector_store
    await vector_store.delete_document(documento_id)

    return {"detail": "Documento eliminato"}


_DOWNLOAD_CHUNK_SIZE = 8 * 1024  # 8 KB


@router.get("/{documento_id}/view")
def view_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a document file inline (for browser/iframe rendering).

    Unlike the download endpoint, this sets Content-Disposition to 'inline'
    so the browser renders the file instead of prompting a download.

    Args:
        documento_id: ID of the document to view.
        db: Database session dependency.
        current_user: Current authenticated user.

    Returns:
        StreamingResponse: File content streamed in 8 KB chunks with inline disposition.

    Raises:
        HTTPException 404: If the document record or the file on disk is not found.
        HTTPException 400: If the file is not a PDF.
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
        "Content-Disposition": f'inline; filename="{safe_name}"; filename*=UTF-8\'\'{encoded_name}',
        "Content-Length": str(documento.file_size),
        "X-Content-Type-Options": "nosniff",
    }
    # Always serve as application/pdf for the viewer; only PDFs are supported inline
    media_type = "application/pdf" if documento.mime_type == "application/pdf" else documento.mime_type
    return StreamingResponse(
        file_generator(),
        media_type=media_type,
        headers=headers,
    )


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
