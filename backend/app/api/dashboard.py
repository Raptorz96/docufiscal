from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.tipo_contratto import TipoContratto
from app.models.documento import Documento
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import ContrattoScadenzaOut, DashboardStats, DocumentoRecenteOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns full dashboard statistics."""
    today = date.today()
    thirty_days_later = today + timedelta(days=30)

    totale_clienti = db.query(Cliente).count()
    totale_documenti = db.query(Documento).count()
    totale_contratti_attivi = db.query(Contratto).filter(Contratto.stato == "attivo").count()

    documenti_da_verificare = (
        db.query(Documento)
        .filter(
            Documento.classificazione_ai.isnot(None),
            Documento.verificato_da_utente == False,
        )
        .count()
    )

    contratti_scaduti = (
        db.query(Contratto)
        .filter(Contratto.data_fine.isnot(None), Contratto.data_fine < today)
        .count()
    )

    contratti_in_scadenza = (
        db.query(Contratto)
        .filter(
            Contratto.stato == "attivo",
            Contratto.data_fine >= today,
            Contratto.data_fine <= thirty_days_later,
        )
        .count()
    )

    # Union of scaduti + in_scadenza, sorted by data_fine ASC
    critici_rows = (
        db.query(
            Contratto.id,
            Cliente.id.label("cliente_id"),
            Cliente.nome.label("cliente_nome"),
            TipoContratto.nome.label("tipo_contratto_nome"),
            Contratto.data_fine.label("data_scadenza"),
        )
        .join(Cliente, Contratto.cliente_id == Cliente.id)
        .join(TipoContratto, Contratto.tipo_contratto_id == TipoContratto.id)
        .filter(
            Contratto.data_fine.isnot(None),
            or_(
                Contratto.data_fine < today,
                (Contratto.stato == "attivo")
                & (Contratto.data_fine >= today)
                & (Contratto.data_fine <= thirty_days_later),
            ),
        )
        .order_by(Contratto.data_fine.asc())
        .all()
    )

    contratti_critici = [
        ContrattoScadenzaOut(
            id=r.id,
            cliente_id=r.cliente_id,
            cliente_nome=r.cliente_nome,
            tipo_contratto_nome=r.tipo_contratto_nome,
            data_scadenza=r.data_scadenza,
            giorni_rimanenti=(r.data_scadenza - today).days,
        )
        for r in critici_rows
    ]

    # Last 10 documents with client name
    ultimi_rows = (
        db.query(
            Documento.id,
            Documento.file_name,
            Documento.tipo_documento,
            Documento.created_at,
            Documento.verificato_da_utente,
            Documento.confidence_score,
            Cliente.nome.label("cliente_nome"),
            Cliente.cognome.label("cliente_cognome"),
        )
        .outerjoin(Cliente, Documento.cliente_id == Cliente.id)
        .order_by(Documento.created_at.desc())
        .limit(10)
        .all()
    )

    ultimi_documenti = [
        DocumentoRecenteOut(
            id=r.id,
            file_name=r.file_name,
            tipo_documento=r.tipo_documento,
            cliente_nome=(
                f"{r.cliente_nome} {r.cliente_cognome}".strip()
                if r.cliente_nome
                else "Non assegnato"
            ),
            created_at=r.created_at,
            verificato_da_utente=r.verificato_da_utente,
            confidence_score=r.confidence_score,
        )
        for r in ultimi_rows
    ]

    return DashboardStats(
        totale_clienti=totale_clienti,
        totale_documenti=totale_documenti,
        totale_contratti_attivi=totale_contratti_attivi,
        documenti_da_verificare=documenti_da_verificare,
        contratti_scaduti=contratti_scaduti,
        contratti_in_scadenza=contratti_in_scadenza,
        contratti_critici=contratti_critici,
        ultimi_documenti=ultimi_documenti,
    )


@router.get("/scadenze", response_model=list[ContrattoScadenzaOut])
def get_upcoming_deadlines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns contracts expiring within the next 30 days."""
    today = date.today()
    thirty_days_later = today + timedelta(days=30)

    scadenze = (
        db.query(
            Contratto.id,
            Cliente.id.label("cliente_id"),
            Cliente.nome.label("cliente_nome"),
            TipoContratto.nome.label("tipo_contratto_nome"),
            Contratto.data_fine.label("data_scadenza"),
        )
        .join(Cliente, Contratto.cliente_id == Cliente.id)
        .join(TipoContratto, Contratto.tipo_contratto_id == TipoContratto.id)
        .filter(Contratto.data_fine >= today)
        .filter(Contratto.data_fine <= thirty_days_later)
        .order_by(Contratto.data_fine.asc())
        .all()
    )

    result = []
    for s in scadenze:
        result.append(ContrattoScadenzaOut(
            id=s.id,
            cliente_id=s.cliente_id,
            cliente_nome=s.cliente_nome,
            tipo_contratto_nome=s.tipo_contratto_nome,
            data_scadenza=s.data_scadenza,
            giorni_rimanenti=(s.data_scadenza - today).days,
        ))

    return result
