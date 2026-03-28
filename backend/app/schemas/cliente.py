"""Cliente-related Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ClienteBase(BaseModel):
    """Base schema for Cliente with common fields."""
    nome: str
    cognome: Optional[str] = None
    short_id: Optional[int] = None
    codice_fiscale: Optional[str] = None
    partita_iva: Optional[str] = None
    tipo: str = "persona_fisica"
    email: Optional[str] = None
    telefono: Optional[str] = None


class ClienteCreate(ClienteBase):
    """Schema for cliente creation request."""
    pass


class ClienteUpdate(BaseModel):
    """Schema for cliente update request with all optional fields."""
    nome: Optional[str] = None
    cognome: Optional[str] = None
    short_id: Optional[int] = None
    codice_fiscale: Optional[str] = None
    partita_iva: Optional[str] = None
    tipo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None


class ClienteResponse(ClienteBase):
    """Schema for cliente response data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime