"""Documento-related Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.models.documento import TipoDocumento


class DocumentoCreate(BaseModel):
    """Schema for documento creation request."""
    cliente_id: int
    contratto_id: Optional[int] = None
    tipo_documento: TipoDocumento = TipoDocumento.altro
    note: Optional[str] = None


class DocumentoUpdate(BaseModel):
    """Schema for documento update request with all optional fields."""
    tipo_documento: Optional[TipoDocumento] = None
    contratto_id: Optional[int] = None
    tipo_documento_raw: Optional[str] = None
    note: Optional[str] = None
    verificato_da_utente: Optional[bool] = None


class DocumentoOut(BaseModel):
    """Schema for documento response data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    contratto_id: Optional[int] = None
    tipo_documento: str
    tipo_documento_raw: Optional[str] = None
    file_name: str
    file_size: int
    mime_type: str
    classificazione_ai: Optional[Any] = None
    confidence_score: Optional[float] = None
    verificato_da_utente: bool
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
