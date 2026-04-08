"""API endpoints for managing clienti."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.user import User
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse

router = APIRouter(prefix="/clienti", tags=["clienti"])


@router.get("", response_model=List[ClienteResponse])
def list_clienti(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tipo: Optional[str] = Query(None, description="Filter by client type"),
    search: Optional[str] = Query(None, description="Search in nome, cognome, codice_fiscale")
) -> List[ClienteResponse]:
    """
    Get list of all clienti with optional filtering.

    Args:
        db: Database session dependency
        current_user: Current authenticated user
        tipo: Optional filter by client type
        search: Optional search term for nome, cognome, codice_fiscale

    Returns:
        List[ClienteResponse]: List of clienti matching criteria
    """
    query = db.query(Cliente)

    # Filter by type if specified
    if tipo:
        query = query.filter(Cliente.tipo == tipo)

    # Search across nome, cognome, codice_fiscale if specified
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Cliente.nome.ilike(search_term),
                Cliente.cognome.ilike(search_term),
                Cliente.codice_fiscale.ilike(search_term)
            )
        )

    clienti = query.all()
    return [ClienteResponse.model_validate(cliente) for cliente in clienti]


@router.get("/{cliente_id}", response_model=ClienteResponse)
def get_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ClienteResponse:
    """
    Get a specific cliente by ID.

    Args:
        cliente_id: ID of the cliente to retrieve
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        ClienteResponse: Cliente data

    Raises:
        HTTPException: 404 if cliente not found
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente not found"
        )

    return ClienteResponse.model_validate(cliente)


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def create_cliente(
    cliente_data: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ClienteResponse:
    """
    Create a new cliente.

    Args:
        cliente_data: Cliente creation data
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        ClienteResponse: Created cliente data

    Raises:
        HTTPException: 409 if codice_fiscale or partita_iva already exists
    """
    # --- Normalization and Formatting ---
    if cliente_data.codice_fiscale:
        val = cliente_data.codice_fiscale
        val = val.replace(" ", "").strip().upper() if val and val.strip() != "" else None
        if val and val.startswith("IT"):
            val = val[2:]
        cliente_data.codice_fiscale = val

    if cliente_data.partita_iva:
        val = cliente_data.partita_iva
        val = val.replace(" ", "").strip().upper() if val and val.strip() != "" else None
        if val and val.startswith("IT"):
            val = val[2:]
        cliente_data.partita_iva = val

    # Check for duplicate codice_fiscale
    if cliente_data.codice_fiscale:
        existing_cf = db.query(Cliente).filter(
            Cliente.codice_fiscale == cliente_data.codice_fiscale
        ).first()
        if existing_cf:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cliente with this codice_fiscale already exists"
            )

    # Check for duplicate partita_iva
    if cliente_data.partita_iva:
        existing_piva = db.query(Cliente).filter(
            Cliente.partita_iva == cliente_data.partita_iva
        ).first()
        if existing_piva:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cliente with this partita_iva already exists"
            )

    # Create new cliente
    db_cliente = Cliente(**cliente_data.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)

    return ClienteResponse.model_validate(db_cliente)


@router.put("/{cliente_id}", response_model=ClienteResponse)
def update_cliente(
    cliente_id: int,
    cliente_data: ClienteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ClienteResponse:
    """
    Update an existing cliente.

    Args:
        cliente_id: ID of the cliente to update
        cliente_data: Cliente update data
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        ClienteResponse: Updated cliente data

    Raises:
        HTTPException: 404 if cliente not found, 409 if codice_fiscale or partita_iva conflicts
    """
    # Get existing cliente
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente not found"
        )

    # Update cliente with only provided fields
    update_data = cliente_data.model_dump(exclude_unset=True)
    
    # Normalizzazione Codice Fiscale
    if "codice_fiscale" in update_data:
        val = update_data["codice_fiscale"]
        val = val.replace(" ", "").strip().upper() if val and val.strip() != "" else None
        if val and val.startswith("IT"):
            val = val[2:]
        update_data["codice_fiscale"] = val

    # Normalizzazione Partita IVA
    if "partita_iva" in update_data:
        val = update_data["partita_iva"]
        val = val.replace(" ", "").strip().upper() if val and val.strip() != "" else None
        if val and val.startswith("IT"):
            val = val[2:]
        update_data["partita_iva"] = val

    # Check for duplicate codice_fiscale (excluding current cliente)
    cf_to_check = update_data.get("codice_fiscale")
    if cf_to_check:
        existing_cf = db.query(Cliente).filter(
            Cliente.codice_fiscale == cf_to_check,
            Cliente.id != cliente_id
        ).first()
        if existing_cf:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another cliente with this codice_fiscale already exists"
            )

    # Check for duplicate partita_iva (excluding current cliente)
    pi_to_check = update_data.get("partita_iva")
    if pi_to_check:
        existing_piva = db.query(Cliente).filter(
            Cliente.partita_iva == pi_to_check,
            Cliente.id != cliente_id
        ).first()
        if existing_piva:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another cliente with this partita_iva already exists"
            )

    # Applica le modifiche al database (SENZA filtri 'if value:' che ignorano i None)
    for field, value in update_data.items():
        setattr(cliente, field, value)

    db.commit()
    db.refresh(cliente)

    return ClienteResponse.model_validate(cliente)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a cliente.

    Args:
        cliente_id: ID of the cliente to delete
        db: Database session dependency
        current_user: Current authenticated user

    Raises:
        HTTPException: 404 if cliente not found, 409 if cliente has associated contracts
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()

    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente not found"
        )

    if cliente.contratti:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Impossibile eliminare: il cliente ha contratti associati"
        )

    db.delete(cliente)
    db.commit()