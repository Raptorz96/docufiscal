"""API endpoints for managing contratti."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.contratto import Contratto
from app.models.cliente import Cliente
from app.models.tipo_contratto import TipoContratto
from app.models.user import User
from app.schemas.contratto import ContrattoCreate, ContrattoUpdate, ContrattoResponse

router = APIRouter(prefix="/contratti", tags=["contratti"])


def _upsert_scadenza_from_contratto(db: Session, contratto: Contratto) -> None:
    """Auto-create/update a scadenza_contratto record from a manual contract."""
    from app.models.scadenza import Scadenza

    existing = db.query(Scadenza).filter(
        Scadenza.contratto_id == contratto.id
    ).first()

    if contratto.data_fine is None:
        # Nessuna data_fine → rimuovi scadenza se esisteva
        if existing:
            db.delete(existing)
        return

    if existing:
        existing.data_inizio = contratto.data_inizio
        existing.data_scadenza = contratto.data_fine
        existing.tipo_scadenza = "canone"
        existing.confidence_score = 1.0
        existing.verificato = True
    else:
        scadenza = Scadenza(
            contratto_id=contratto.id,
            cliente_id=contratto.cliente_id,
            documento_id=None,
            tipo_scadenza="canone",
            data_inizio=contratto.data_inizio,
            data_scadenza=contratto.data_fine,
            confidence_score=1.0,
            verificato=True,
        )
        db.add(scadenza)


@router.get("", response_model=List[ContrattoResponse])
def list_contratti(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cliente_id: Optional[int] = Query(None, description="Filter by cliente_id"),
    tipo_contratto_id: Optional[int] = Query(None, description="Filter by tipo_contratto_id"),
    stato: Optional[str] = Query(None, description="Filter by stato")
) -> List[ContrattoResponse]:
    """
    Get list of all contratti with optional filtering.

    Args:
        db: Database session dependency
        current_user: Current authenticated user
        cliente_id: Optional filter by cliente_id
        tipo_contratto_id: Optional filter by tipo_contratto_id
        stato: Optional filter by stato

    Returns:
        List[ContrattoResponse]: List of contratti matching criteria
    """
    query = db.query(Contratto)

    # Filter by cliente_id if specified
    if cliente_id:
        query = query.filter(Contratto.cliente_id == cliente_id)

    # Filter by tipo_contratto_id if specified
    if tipo_contratto_id:
        query = query.filter(Contratto.tipo_contratto_id == tipo_contratto_id)

    # Filter by stato if specified
    if stato:
        query = query.filter(Contratto.stato == stato)

    contratti = query.all()
    return [ContrattoResponse.model_validate(contratto) for contratto in contratti]


@router.get("/{contratto_id}", response_model=ContrattoResponse)
def get_contratto(
    contratto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContrattoResponse:
    """
    Get a specific contratto by ID.

    Args:
        contratto_id: ID of the contratto to retrieve
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        ContrattoResponse: Contratto data

    Raises:
        HTTPException: 404 if contratto not found
    """
    contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()

    if not contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratto not found"
        )

    return ContrattoResponse.model_validate(contratto)


@router.post("", response_model=ContrattoResponse, status_code=status.HTTP_201_CREATED)
def create_contratto(
    contratto_data: ContrattoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContrattoResponse:
    """
    Create a new contratto.

    Args:
        contratto_data: Contratto creation data
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        ContrattoResponse: Created contratto data

    Raises:
        HTTPException: 404 if cliente_id or tipo_contratto_id do not exist
    """
    # Validate that cliente exists
    cliente = db.query(Cliente).filter(Cliente.id == contratto_data.cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente not found"
        )

    # Validate that tipo_contratto exists
    tipo_contratto = db.query(TipoContratto).filter(TipoContratto.id == contratto_data.tipo_contratto_id).first()
    if not tipo_contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo contratto not found"
        )

    # Create new contratto
    db_contratto = Contratto(**contratto_data.model_dump())
    db.add(db_contratto)
    db.commit()
    db.refresh(db_contratto)

    _upsert_scadenza_from_contratto(db, db_contratto)
    db.commit()

    return ContrattoResponse.model_validate(db_contratto)


@router.put("/{contratto_id}", response_model=ContrattoResponse)
def update_contratto(
    contratto_id: int,
    contratto_data: ContrattoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ContrattoResponse:
    """
    Update an existing contratto.

    Args:
        contratto_id: ID of the contratto to update
        contratto_data: Contratto update data
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        ContrattoResponse: Updated contratto data

    Raises:
        HTTPException: 404 if contratto, cliente_id, or tipo_contratto_id not found
    """
    # Get existing contratto
    contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()

    if not contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratto not found"
        )

    # Validate cliente_id if being changed
    if contratto_data.cliente_id is not None:
        cliente = db.query(Cliente).filter(Cliente.id == contratto_data.cliente_id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente not found"
            )

    # Validate tipo_contratto_id if being changed
    if contratto_data.tipo_contratto_id is not None:
        tipo_contratto = db.query(TipoContratto).filter(TipoContratto.id == contratto_data.tipo_contratto_id).first()
        if not tipo_contratto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tipo contratto not found"
            )

    # Update contratto with only provided fields
    update_data = contratto_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contratto, field, value)

    db.commit()
    db.refresh(contratto)

    _upsert_scadenza_from_contratto(db, contratto)
    db.commit()

    return ContrattoResponse.model_validate(contratto)


@router.delete("/{contratto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contratto(
    contratto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a contratto.

    Args:
        contratto_id: ID of the contratto to delete
        db: Database session dependency
        current_user: Current authenticated user

    Raises:
        HTTPException: 404 if contratto not found
    """
    contratto = db.query(Contratto).filter(Contratto.id == contratto_id).first()

    if not contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contratto not found"
        )

    db.delete(contratto)
    db.commit()