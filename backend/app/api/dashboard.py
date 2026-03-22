from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento
from app.models.scadenza_contratto import ScadenzaContratto
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
        db.query(ScadenzaContratto)
        .filter(
            ScadenzaContratto.data_scadenza.isnot(None),
            ScadenzaContratto.data_scadenza < today,
        )
        .count()
    )

    scadenze_in_scadenza = (
        db.query(ScadenzaContratto)
        .filter(
            ScadenzaContratto.data_scadenza.isnot(None),
            ScadenzaContratto.data_scadenza >= today,
            ScadenzaContratto.data_scadenza <= thirty_days_later,
        )
        .count()
    )

    critiche_rows = (
        db.query(
            ScadenzaContratto.id,
            ScadenzaContratto.documento_id,
            ScadenzaContratto.cliente_id,
            Cliente.nome.label("cliente_nome"),
            Documento.file_name,
            ScadenzaContratto.data_scadenza,
            ScadenzaContratto.canone,
            ScadenzaContratto.rinnovo_automatico,
            ScadenzaContratto.preavviso_disdetta,
            ScadenzaContratto.confidence_score,
            ScadenzaContratto.verificato,
        )
        .join(Cliente, ScadenzaContratto.cliente_id == Cliente.id)
        .join(Documento, ScadenzaContratto.documento_id == Documento.id)
        .filter(
            ScadenzaContratto.data_scadenza.isnot(None),
            or_(
                ScadenzaContratto.data_scadenza < today,
                and_(
                    ScadenzaContratto.data_scadenza >= today,
                    ScadenzaContratto.data_scadenza <= thirty_days_later,
                ),
            ),
        )
        .order_by(ScadenzaContratto.data_scadenza.asc())
        .all()
    )

    scadenze_critiche = [
        ScadenzaDashboardOut(
            id=r.id,
            documento_id=r.documento_id,
            cliente_id=r.cliente_id,
            cliente_nome=r.cliente_nome,
            file_name=r.file_name,
            data_scadenza=r.data_scadenza,
            giorni_rimanenti=(r.data_scadenza - today).days,
            canone=r.canone,
            rinnovo_automatico=r.rinnovo_automatico,
            preavviso_disdetta=r.preavviso_disdetta,
            confidence_score=r.confidence_score,
            verificato=r.verificato,
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
            ScadenzaContratto.id,
            ScadenzaContratto.documento_id,
            ScadenzaContratto.cliente_id,
            Cliente.nome.label("cliente_nome"),
            Documento.file_name,
            ScadenzaContratto.data_scadenza,
            ScadenzaContratto.canone,
            ScadenzaContratto.rinnovo_automatico,
            ScadenzaContratto.preavviso_disdetta,
            ScadenzaContratto.confidence_score,
            ScadenzaContratto.verificato,
        )
        .join(Cliente, ScadenzaContratto.cliente_id == Cliente.id)
        .join(Documento, ScadenzaContratto.documento_id == Documento.id)
        .filter(
            ScadenzaContratto.data_scadenza.isnot(None),
            ScadenzaContratto.data_scadenza >= today,
            ScadenzaContratto.data_scadenza <= thirty_days_later,
        )
        .order_by(ScadenzaContratto.data_scadenza.asc())
        .all()
    )

    return [
        ScadenzaDashboardOut(
            id=r.id,
            documento_id=r.documento_id,
            cliente_id=r.cliente_id,
            cliente_nome=r.cliente_nome,
            file_name=r.file_name,
            data_scadenza=r.data_scadenza,
            giorni_rimanenti=(r.data_scadenza - today).days,
            canone=r.canone,
            rinnovo_automatico=r.rinnovo_automatico,
            preavviso_disdetta=r.preavviso_disdetta,
            confidence_score=r.confidence_score,
            verificato=r.verificato,
        )
        for r in rows
    ]
