"""Dashboard stats endpoint."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento
from app.models.tipo_contratto import TipoContratto
from app.models.user import User
from app.schemas.dashboard import ContrattoScadenzaOut, DashboardStats, DocumentoRecenteOut

router = APIRouter()

_SCADENZA_GIORNI = 30
_ULTIMI_DOCUMENTI_LIMIT = 10


def _cliente_nome(cliente: Cliente) -> str:
    if cliente.cognome:
        return f"{cliente.nome} {cliente.cognome}"
    return cliente.nome


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStats:
    """Return aggregated dashboard statistics in a single query round-trip."""
    oggi = date.today()
    soglia = oggi + timedelta(days=_SCADENZA_GIORNI)

    # --- Simple counters ---
    totale_clienti = db.query(Cliente).count()
    totale_documenti = db.query(Documento).count()
    totale_contratti_attivi = (
        db.query(Contratto).filter(Contratto.stato == "attivo").count()
    )
    documenti_da_verificare = (
        db.query(Documento)
        .filter(
            Documento.classificazione_ai.isnot(None),
            Documento.verificato_da_utente == False,  # noqa: E712
        )
        .count()
    )

    # Count of ALL scaduto contracts (irrespective of data_fine)
    contratti_scaduti_count = (
        db.query(Contratto).filter(Contratto.stato == "scaduto").count()
    )

    # --- Critici: scaduti with data_fine (needed for giorni) + in scadenza ---
    scaduti_rows = (
        db.query(Contratto, Cliente, TipoContratto)
        .join(Cliente, Contratto.cliente_id == Cliente.id)
        .join(TipoContratto, Contratto.tipo_contratto_id == TipoContratto.id)
        .filter(
            Contratto.stato == "scaduto",
            Contratto.data_fine.isnot(None),
        )
        .all()
    )

    in_scadenza_rows = (
        db.query(Contratto, Cliente, TipoContratto)
        .join(Cliente, Contratto.cliente_id == Cliente.id)
        .join(TipoContratto, Contratto.tipo_contratto_id == TipoContratto.id)
        .filter(
            Contratto.stato == "attivo",
            Contratto.data_fine.isnot(None),
            Contratto.data_fine <= soglia,
        )
        .all()
    )

    def _to_scadenza_out(
        contratto: Contratto, cliente: Cliente, tipo: TipoContratto
    ) -> ContrattoScadenzaOut:
        return ContrattoScadenzaOut(
            id=contratto.id,
            cliente_nome=_cliente_nome(cliente),
            tipo_contratto_nome=tipo.nome,
            data_fine=contratto.data_fine,
            stato=contratto.stato,
            giorni_alla_scadenza=(contratto.data_fine - oggi).days,
        )

    contratti_critici = sorted(
        [_to_scadenza_out(c, cl, tc) for c, cl, tc in scaduti_rows + in_scadenza_rows],
        key=lambda x: x.data_fine,
    )

    # --- Ultimi documenti ---
    ultimi_rows = (
        db.query(Documento, Cliente)
        .join(Cliente, Documento.cliente_id == Cliente.id)
        .order_by(Documento.created_at.desc())
        .limit(_ULTIMI_DOCUMENTI_LIMIT)
        .all()
    )

    ultimi_documenti = [
        DocumentoRecenteOut(
            id=doc.id,
            file_name=doc.file_name,
            tipo_documento=doc.tipo_documento,
            cliente_nome=_cliente_nome(cliente),
            created_at=doc.created_at,
            verificato_da_utente=doc.verificato_da_utente,
            confidence_score=doc.confidence_score,
        )
        for doc, cliente in ultimi_rows
    ]

    return DashboardStats(
        totale_clienti=totale_clienti,
        totale_documenti=totale_documenti,
        totale_contratti_attivi=totale_contratti_attivi,
        documenti_da_verificare=documenti_da_verificare,
        contratti_scaduti=contratti_scaduti_count,
        contratti_in_scadenza=len(in_scadenza_rows),
        contratti_critici=contratti_critici,
        ultimi_documenti=ultimi_documenti,
    )
