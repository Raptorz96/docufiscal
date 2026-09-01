from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ScadenzaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int | None = None
    contratto_id: int | None = None
    cliente_id: int
    tipo_scadenza: str = "contratto"
    descrizione: str | None = None
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


class ScadenzaListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int | None = None
    contratto_id: int | None = None
    cliente_id: int
    cliente_nome: str
    file_name: str = "Contratto manuale"
    tipo_scadenza: str
    descrizione: str | None = None
    data_scadenza: date | None
    data_inizio: date | None = None
    giorni_rimanenti: int | None = None
    canone: str | None = None
    rinnovo_automatico: bool | None = None
    preavviso_disdetta: str | None = None
    confidence_score: float
    verificato: bool
    is_contratto: bool = False
    created_at: datetime
