"""Contratto-related Pydantic schemas for request/response validation."""
from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContrattoBase(BaseModel):
    """Base schema for Contratto with common fields."""
    cliente_id: int
    tipo_contratto_id: int
    data_inizio: date
    data_fine: Optional[date] = None
    stato: str = "attivo"
    note: Optional[str] = None


class ContrattoCreate(ContrattoBase):
    """Schema for contratto creation request."""
    pass


class ContrattoUpdate(BaseModel):
    """Schema for contratto update request with all optional fields."""
    cliente_id: Optional[int] = None
    tipo_contratto_id: Optional[int] = None
    data_inizio: Optional[date] = None
    data_fine: Optional[date] = None
    stato: Optional[str] = None
    note: Optional[str] = None


class ContrattoResponse(ContrattoBase):
    """Schema for contratto response data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime