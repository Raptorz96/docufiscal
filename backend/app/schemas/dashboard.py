"""Pydantic schemas for the dashboard stats endpoint."""
from datetime import date, datetime

from pydantic import BaseModel


class ContrattoScadenzaOut(BaseModel):
    id: int
    cliente_id: int
    cliente_nome: str
    tipo_contratto_nome: str
    data_scadenza: date  # Mapped from data_fine
    giorni_rimanenti: int


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

    # Critical contracts
    contratti_scaduti: int
    contratti_in_scadenza: int  # active with data_fine within 30 days
    contratti_critici: list[ContrattoScadenzaOut]  # union of above, sorted by data_fine

    # Recent feed
    ultimi_documenti: list[DocumentoRecenteOut]  # last 10 by created_at DESC
