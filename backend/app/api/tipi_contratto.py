"""API endpoints for managing tipi contratto."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.tipo_contratto import TipoContratto
from app.models.user import User
from app.schemas.tipo_contratto import TipoContrattoCreate, TipoContrattoUpdate, TipoContrattoResponse

router = APIRouter(prefix="/tipi-contratto", tags=["tipi_contratto"])


@router.get("", response_model=List[TipoContrattoResponse])
def list_tipi_contratto(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    categoria: Optional[str] = Query(None, description="Filter by categoria"),
    search: Optional[str] = Query(None, description="Search in nome")
) -> List[TipoContrattoResponse]:
    """
    Get list of all tipi contratto with optional filtering.

    Args:
        db: Database session dependency
        current_user: Current authenticated user
        categoria: Optional filter by categoria
        search: Optional search term for nome

    Returns:
        List[TipoContrattoResponse]: List of tipi contratto matching criteria
    """
    query = db.query(TipoContratto)

    # Filter by categoria if specified
    if categoria:
        query = query.filter(TipoContratto.categoria == categoria)

    # Search in nome if specified
    if search:
        search_term = f"%{search}%"
        query = query.filter(TipoContratto.nome.ilike(search_term))

    tipi_contratto = query.all()
    return [TipoContrattoResponse.model_validate(tipo) for tipo in tipi_contratto]


@router.get("/{tipo_contratto_id}", response_model=TipoContrattoResponse)
def get_tipo_contratto(
    tipo_contratto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TipoContrattoResponse:
    """
    Get a specific tipo contratto by ID.

    Args:
        tipo_contratto_id: ID of the tipo contratto to retrieve
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        TipoContrattoResponse: Tipo contratto data

    Raises:
        HTTPException: 404 if tipo contratto not found
    """
    tipo_contratto = db.query(TipoContratto).filter(TipoContratto.id == tipo_contratto_id).first()

    if not tipo_contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo contratto not found"
        )

    return TipoContrattoResponse.model_validate(tipo_contratto)


@router.post("", response_model=TipoContrattoResponse, status_code=status.HTTP_201_CREATED)
def create_tipo_contratto(
    tipo_contratto_data: TipoContrattoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TipoContrattoResponse:
    """
    Create a new tipo contratto.

    Args:
        tipo_contratto_data: Tipo contratto creation data
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        TipoContrattoResponse: Created tipo contratto data

    Raises:
        HTTPException: 409 if nome already exists
    """
    # Check for duplicate nome
    existing_tipo = db.query(TipoContratto).filter(
        TipoContratto.nome == tipo_contratto_data.nome
    ).first()
    if existing_tipo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tipo contratto with this nome already exists"
        )

    # Create new tipo contratto
    db_tipo_contratto = TipoContratto(**tipo_contratto_data.model_dump())
    db.add(db_tipo_contratto)
    db.commit()
    db.refresh(db_tipo_contratto)

    return TipoContrattoResponse.model_validate(db_tipo_contratto)


@router.put("/{tipo_contratto_id}", response_model=TipoContrattoResponse)
def update_tipo_contratto(
    tipo_contratto_id: int,
    tipo_contratto_data: TipoContrattoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TipoContrattoResponse:
    """
    Update an existing tipo contratto.

    Args:
        tipo_contratto_id: ID of the tipo contratto to update
        tipo_contratto_data: Tipo contratto update data
        db: Database session dependency
        current_user: Current authenticated user

    Returns:
        TipoContrattoResponse: Updated tipo contratto data

    Raises:
        HTTPException: 404 if tipo contratto not found, 409 if nome conflicts
    """
    # Get existing tipo contratto
    tipo_contratto = db.query(TipoContratto).filter(TipoContratto.id == tipo_contratto_id).first()

    if not tipo_contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo contratto not found"
        )

    # Check for duplicate nome (excluding current tipo contratto)
    if tipo_contratto_data.nome is not None:
        existing_tipo = db.query(TipoContratto).filter(
            TipoContratto.nome == tipo_contratto_data.nome,
            TipoContratto.id != tipo_contratto_id
        ).first()
        if existing_tipo:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another tipo contratto with this nome already exists"
            )

    # Update tipo contratto with only provided fields
    update_data = tipo_contratto_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tipo_contratto, field, value)

    db.commit()
    db.refresh(tipo_contratto)

    return TipoContrattoResponse.model_validate(tipo_contratto)


@router.delete("/{tipo_contratto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_contratto(
    tipo_contratto_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a tipo contratto.

    Args:
        tipo_contratto_id: ID of the tipo contratto to delete
        db: Database session dependency
        current_user: Current authenticated user

    Raises:
        HTTPException: 404 if tipo contratto not found, 409 if tipo contratto has associated contracts
    """
    tipo_contratto = db.query(TipoContratto).filter(TipoContratto.id == tipo_contratto_id).first()

    if not tipo_contratto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tipo contratto not found"
        )

    if tipo_contratto.contratti:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Impossibile eliminare: il tipo contratto ha contratti associati"
        )

    db.delete(tipo_contratto)
    db.commit()