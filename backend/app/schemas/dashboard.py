"""Pydantic schemas for the dashboard stats endpoint."""
from datetime import date, datetime

from pydantic import BaseModel


class ScadenzaDashboardOut(BaseModel):
    id: int  # scadenze_contratto.id
    documento_id: int | None = None
    contratto_id: int | None = None
    cliente_id: int
    cliente_nome: str
    file_name: str = "Contratto manuale"  # nome del PDF contratto o fallback
    data_scadenza: date | None
    giorni_rimanenti: int | None
    canone: str | None
    rinnovo_automatico: bool | None
    preavviso_disdetta: str | None
    confidence_score: float
    verificato: bool


class DocumentoRecenteOut(BaseModel):
    id: int
    file_name: str
    tipo_documento: str
    cliente_nome: str
    created_at: datetime
    verificato_da_utente: bool
    confidence_score: float | None


class DashboardStats(BaseModel):
    # Counters
    totale_clienti: int
    totale_documenti: int
    totale_contratti_attivi: int

    # AI classification
    documenti_da_verificare: int  # classificazione_ai not null AND verificato_da_utente = false

    # Critical deadlines (from scadenze_contratto AI-extracted)
    scadenze_scadute: int
    scadenze_in_scadenza: int  # data_scadenza within 30 days
    scadenze_critiche: list[ScadenzaDashboardOut]  # union of above, sorted by data_scadenza

    # Recent feed
    ultimi_documenti: list[DocumentoRecenteOut]  # last 10 by created_at DESC
