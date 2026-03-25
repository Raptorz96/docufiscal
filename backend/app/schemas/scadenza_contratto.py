from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ScadenzaContrattoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int | None = None
    contratto_id: int | None = None
    cliente_id: int
    data_inizio: date | None = None
    data_scadenza: date | None = None
    durata: str | None = None
    rinnovo_automatico: bool | None = None
    preavviso_disdetta: str | None = None
    canone: str | None = None
    parti_coinvolte: list[str] | None = None
    clausole_chiave: list[str] | None = None
    confidence_score: float
    verificato: bool
    created_at: datetime
    updated_at: datetime
