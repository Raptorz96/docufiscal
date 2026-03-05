from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.tipo_contratto import TipoContratto
from app.models.documento import Documento
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import ContrattoScadenzaOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns dashboard statistics."""
    totale_clienti = db.query(Cliente).count()
    totale_documenti = db.query(Documento).count()
    documenti_da_assegnare = db.query(Documento).filter(Documento.cliente_id == None).count()
    
    return {
        "totale_clienti": totale_clienti,
        "totale_documenti": totale_documenti,
        "documenti_da_assegnare": documenti_da_assegnare
    }

@router.get("/scadenze", response_model=list[ContrattoScadenzaOut])
def get_upcoming_deadlines(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
            giorni_rimanenti=(s.data_scadenza - today).days
        ))
    
    return result
