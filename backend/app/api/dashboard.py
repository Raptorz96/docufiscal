from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.documento import Documento
from app.api.deps import get_current_user
from app.models.user import User

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
