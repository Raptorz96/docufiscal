import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.google_token import GoogleToken
from app.models.scadenza_contratto import ScadenzaContratto
from app.models.cliente import Cliente
from app.models.documento import Documento
from app.models.user import User
from app.schemas.google_calendar import (
    CalendarEventCreate,
    CalendarEventFromScadenza,
    CalendarEventOut,
)
from app.services.google_calendar import create_calendar_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/calendar", tags=["calendar"])


def _require_google_connected(db: Session, user_id: int) -> None:
    """Raise 400 if user has no Google Calendar connection."""
    token = db.query(GoogleToken).filter(GoogleToken.user_id == user_id).first()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google Calendar non connesso. Vai al Profilo per connettere.",
        )


@router.post("/events", response_model=CalendarEventOut)
def create_event(
    payload: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a custom calendar event."""
    _require_google_connected(db, current_user.id)

    result = create_calendar_event(
        db=db,
        user_id=current_user.id,
        summary=payload.summary,
        description=payload.description,
        event_date=payload.event_date,
        start_datetime=payload.start_datetime,
        end_datetime=payload.end_datetime,
        reminder_minutes=payload.reminder_minutes,
    )

    if result:
        return CalendarEventOut(
            success=True,
            event_id=result.get("id"),
            event_link=result.get("htmlLink"),
        )
    return CalendarEventOut(success=False, error="Impossibile creare l'evento. Verifica la connessione Google Calendar.")


@router.post("/events/from-scadenza", response_model=CalendarEventOut)
def create_event_from_scadenza(
    payload: CalendarEventFromScadenza,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a calendar event from an AI-extracted contract deadline."""
    _require_google_connected(db, current_user.id)

    scadenza = db.query(ScadenzaContratto).filter(ScadenzaContratto.id == payload.scadenza_id).first()
    if not scadenza:
        raise HTTPException(status_code=404, detail="Scadenza non trovata")

    cliente = db.query(Cliente).filter(Cliente.id == scadenza.cliente_id).first()
    documento = db.query(Documento).filter(Documento.id == scadenza.documento_id).first()

    cliente_nome = f"{cliente.nome} {cliente.cognome}".strip() if cliente else "Sconosciuto"
    file_name = documento.file_name if documento else "documento"

    summary = f"Scadenza contratto — {cliente_nome}"

    desc_parts = [f"Cliente: {cliente_nome}", f"Documento: {file_name}"]
    if scadenza.canone:
        desc_parts.append(f"Canone: {scadenza.canone}")
    if scadenza.rinnovo_automatico is not None:
        desc_parts.append(f"Rinnovo automatico: {'Sì' if scadenza.rinnovo_automatico else 'No'}")
    if scadenza.preavviso_disdetta:
        desc_parts.append(f"Preavviso disdetta: {scadenza.preavviso_disdetta}")
    if scadenza.clausole_chiave:
        desc_parts.append(f"Clausole: {'; '.join(scadenza.clausole_chiave)}")
    desc_parts.append(f"\nGenerato da DocuFiscal")
    description = "\n".join(desc_parts)

    if not scadenza.data_scadenza:
        return CalendarEventOut(success=False, error="Scadenza senza data — impossibile creare evento.")

    event_date = scadenza.data_scadenza.isoformat()

    result = create_calendar_event(
        db=db,
        user_id=current_user.id,
        summary=summary,
        description=description,
        event_date=event_date,
        reminder_minutes=payload.reminder_minutes,
    )

    if result:
        return CalendarEventOut(
            success=True,
            event_id=result.get("id"),
            event_link=result.get("htmlLink"),
        )
    return CalendarEventOut(success=False, error="Impossibile creare l'evento. Verifica la connessione Google Calendar.")
