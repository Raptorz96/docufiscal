"""API endpoint for listing and filtering all scadenze."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento
from app.models.scadenza import Scadenza
from app.models.user import User
from app.schemas.scadenza import ScadenzaListOut

router = APIRouter(prefix="/scadenze", tags=["scadenze"])


@router.get("", response_model=list[ScadenzaListOut])
def list_scadenze(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tipo_scadenza: Optional[str] = Query(None),
    cliente_id: Optional[int] = Query(None),
    da_data: Optional[date] = Query(None, description="Scadenze da questa data"),
    a_data: Optional[date] = Query(None, description="Scadenze fino a questa data"),
    verificato: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
) -> list[ScadenzaListOut]:
    """List all scadenze with optional filters."""
    today = date.today()

    query = (
        db.query(
            Scadenza.id,
            Scadenza.documento_id,
            Scadenza.contratto_id,
            Scadenza.cliente_id,
            Cliente.nome.label("cliente_nome"),
            Cliente.cognome.label("cliente_cognome"),
            Documento.file_name,
            Documento.is_contratto,
            Scadenza.tipo_scadenza,
            Scadenza.descrizione,
            Scadenza.data_scadenza,
            Scadenza.data_inizio,
            Scadenza.canone,
            Scadenza.rinnovo_automatico,
            Scadenza.preavviso_disdetta,
            Scadenza.confidence_score,
            Scadenza.verificato,
            Scadenza.created_at,
        )
        .join(Cliente, Scadenza.cliente_id == Cliente.id)
        .outerjoin(Documento, Scadenza.documento_id == Documento.id)
        .outerjoin(Contratto, Scadenza.contratto_id == Contratto.id)
    )

    if tipo_scadenza:
        query = query.filter(Scadenza.tipo_scadenza == tipo_scadenza)
    if cliente_id is not None:
        query = query.filter(Scadenza.cliente_id == cliente_id)
    if da_data is not None:
        query = query.filter(Scadenza.data_scadenza >= da_data)
    if a_data is not None:
        query = query.filter(Scadenza.data_scadenza <= a_data)
    if verificato is not None:
        query = query.filter(Scadenza.verificato == verificato)
    if search:
        term = f"%{search}%"
        query = query.filter(
            Cliente.nome.ilike(term) | Cliente.cognome.ilike(term) | Scadenza.descrizione.ilike(term)
        )

    rows = query.order_by(Scadenza.data_scadenza.asc().nullslast()).offset(skip).limit(limit).all()

    result = []
    for r in rows:
        giorni = (r.data_scadenza - today).days if r.data_scadenza else None
        result.append(
            ScadenzaListOut(
                id=r.id,
                documento_id=r.documento_id,
                contratto_id=r.contratto_id,
                cliente_id=r.cliente_id,
                cliente_nome=f"{r.cliente_nome} {r.cliente_cognome}".strip() if r.cliente_nome else "Non assegnato",
                file_name=r.file_name if r.file_name else "Contratto manuale",
                tipo_scadenza=r.tipo_scadenza,
                descrizione=r.descrizione,
                data_scadenza=r.data_scadenza,
                data_inizio=r.data_inizio,
                giorni_rimanenti=giorni,
                canone=r.canone,
                rinnovo_automatico=r.rinnovo_automatico,
                preavviso_disdetta=r.preavviso_disdetta,
                confidence_score=r.confidence_score,
                verificato=r.verificato,
                is_contratto=r.is_contratto if r.is_contratto is not None else False,
                created_at=r.created_at,
            )
        )
    return result
