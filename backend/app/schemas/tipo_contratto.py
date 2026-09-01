"""TipoContratto-related Pydantic schemas for request/response validation."""
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TipoContrattoBase(BaseModel):
    """Base schema for TipoContratto with common fields."""
    nome: str
    descrizione: Optional[str] = None
    categoria: str


class TipoContrattoCreate(TipoContrattoBase):
    """Schema for tipo contratto creation request."""
    pass


class TipoContrattoUpdate(BaseModel):
    """Schema for tipo contratto update request with all optional fields."""
    nome: Optional[str] = None
    descrizione: Optional[str] = None
    categoria: Optional[str] = None


class TipoContrattoResponse(TipoContrattoBase):
    """Schema for tipo contratto response data."""
    model_config = ConfigDict(from_attributes=True)

    id: int