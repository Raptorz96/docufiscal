from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento
from app.models.scadenza import Scadenza
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import ScadenzaDashboardOut, DashboardStats, DocumentoRecenteOut

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

    scadenze_scadute = (
        db.query(Scadenza)
        .filter(
            Scadenza.data_scadenza.isnot(None),
            Scadenza.data_scadenza < today,
        )
        .count()
    )

    scadenze_in_scadenza = (
        db.query(Scadenza)
        .filter(
            Scadenza.data_scadenza.isnot(None),
            Scadenza.data_scadenza >= today,
            Scadenza.data_scadenza <= thirty_days_later,
        )
        .count()
    )

    critiche_rows = (
        db.query(
            Scadenza.id,
            Scadenza.documento_id,
            Scadenza.contratto_id,
            Scadenza.cliente_id,
            Cliente.nome.label("cliente_nome"),
            Cliente.cognome.label("cliente_cognome"),
            Documento.file_name,
            Documento.is_contratto,
            Scadenza.data_scadenza,
            Scadenza.canone,
            Scadenza.rinnovo_automatico,
            Scadenza.preavviso_disdetta,
            Scadenza.confidence_score,
            Scadenza.verificato,
        )
        .join(Cliente, Scadenza.cliente_id == Cliente.id)
        .outerjoin(Documento, Scadenza.documento_id == Documento.id)
        .outerjoin(Contratto, Scadenza.contratto_id == Contratto.id)
        .filter(
            Scadenza.data_scadenza.isnot(None),
            or_(
                Scadenza.data_scadenza < today,
                and_(
                    Scadenza.data_scadenza >= today,
                    Scadenza.data_scadenza <= thirty_days_later,
                ),
            ),
        )
        .order_by(Scadenza.data_scadenza.asc())
        .all()
    )

    scadenze_critiche = [
        ScadenzaDashboardOut(
            id=r.id,
            documento_id=r.documento_id,
            contratto_id=r.contratto_id,
            cliente_id=r.cliente_id,
            cliente_nome=f"{r.cliente_nome} {r.cliente_cognome}".strip() if r.cliente_nome else "Non assegnato",
            file_name=r.file_name if r.file_name else "Contratto manuale",
            data_scadenza=r.data_scadenza,
            giorni_rimanenti=(r.data_scadenza - today).days,
            canone=r.canone,
            rinnovo_automatico=r.rinnovo_automatico,
            preavviso_disdetta=r.preavviso_disdetta,
            confidence_score=r.confidence_score,
            verificato=r.verificato,
            is_contratto=r.is_contratto if r.is_contratto is not None else False,
        )
        for r in critiche_rows
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
        scadenze_scadute=scadenze_scadute,
        scadenze_in_scadenza=scadenze_in_scadenza,
        scadenze_critiche=scadenze_critiche,
        ultimi_documenti=ultimi_documenti,
    )


@router.get("/scadenze", response_model=list[ScadenzaDashboardOut])
def get_upcoming_deadlines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns AI-extracted contract deadlines within the next 30 days."""
    today = date.today()
    thirty_days_later = today + timedelta(days=30)

    rows = (
        db.query(
            Scadenza.id,
            Scadenza.documento_id,
            Scadenza.contratto_id,
            Scadenza.cliente_id,
            Cliente.nome.label("cliente_nome"),
            Cliente.cognome.label("cliente_cognome"),
            Documento.file_name,
            Documento.is_contratto,
            Scadenza.data_scadenza,
            Scadenza.canone,
            Scadenza.rinnovo_automatico,
            Scadenza.preavviso_disdetta,
            Scadenza.confidence_score,
            Scadenza.verificato,
        )
        .join(Cliente, Scadenza.cliente_id == Cliente.id)
        .outerjoin(Documento, Scadenza.documento_id == Documento.id)
        .outerjoin(Contratto, Scadenza.contratto_id == Contratto.id)
        .filter(
            Scadenza.data_scadenza.isnot(None),
            Scadenza.data_scadenza >= today,
            Scadenza.data_scadenza <= thirty_days_later,
        )
        .order_by(Scadenza.data_scadenza.asc())
        .all()
    )

    return [
        ScadenzaDashboardOut(
            id=r.id,
            documento_id=r.documento_id,
            contratto_id=r.contratto_id,
            cliente_id=r.cliente_id,
            cliente_nome=f"{r.cliente_nome} {r.cliente_cognome}".strip() if r.cliente_nome else "Non assegnato",
            file_name=r.file_name if r.file_name else "Contratto manuale",
            data_scadenza=r.data_scadenza,
            giorni_rimanenti=(r.data_scadenza - today).days,
            canone=r.canone,
            rinnovo_automatico=r.rinnovo_automatico,
            preavviso_disdetta=r.preavviso_disdetta,
            confidence_score=r.confidence_score,
            verificato=r.verificato,
            is_contratto=r.is_contratto if r.is_contratto is not None else False,
        )
        for r in rows
    ]
