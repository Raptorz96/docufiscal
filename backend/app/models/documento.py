"""Documento model for DocuFiscal application."""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TipoDocumento(str, Enum):
    """Enum for document types."""
    dichiarazione_redditi = "dichiarazione_redditi"
    fattura = "fattura"
    f24 = "f24"
    cu = "cu"
    visura_camerale = "visura_camerale"
    busta_paga = "busta_paga"
    contratto = "contratto"
    bilancio = "bilancio"
    comunicazione_agenzia = "comunicazione_agenzia"
    documento_identita = "documento_identita"
    altro = "altro"


class MacroCategoria(str, Enum):
    """Enum for document macro categories."""
    fiscale = "fiscale"
    lavoro = "lavoro"
    amministrazione = "amministrazione"
    altro = "altro"


class Documento(Base):
    """
    Documento model representing uploaded documents in the system.

    Attributes:
        id: Primary key identifier
        cliente_id: Foreign key to the client (required)
        contratto_id: Foreign key to the contract (optional)
        macro_categoria: Macro category (Fiscale, Lavoro, Amministrazione)
        tipo_documento: Document type from TipoDocumento enum
        tipo_documento_raw: Free-text document type from AI classification
        anno_competenza: Reference year for the document
        file_name: Original uploaded filename
        file_path: Path on filesystem
        file_size: File size in bytes
        mime_type: MIME type (e.g. application/pdf)
        classificazione_ai: Full Claude classification output
        confidence_score: AI confidence score 0.0-1.0
        verificato_da_utente: Whether user has verified the classification
        note: Optional notes
        created_at: Timestamp when document was created
        updated_at: Timestamp when document was last updated
        cliente: Relationship to the client
        contratto: Relationship to the contract
    """
    __tablename__ = "documenti"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Primary key identifier"
    )

    cliente_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("clienti.id"),
        nullable=True,
        doc="Foreign key to the client (optional)"
    )

    contratto_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("contratti.id"),
        nullable=True,
        doc="Foreign key to the contract (optional)"
    )

    macro_categoria: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="altro",
        doc="Macro category (Fiscale, Lavoro, Amministrazione)"
    )

    tipo_documento: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="altro",
        doc="Document type from TipoDocumento enum"
    )

    tipo_documento_raw: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Free-text document type from AI classification"
    )

    anno_competenza: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Reference year for the document"
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Original uploaded filename"
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Path on filesystem"
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="File size in bytes"
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="MIME type (e.g. application/pdf)"
    )

    classificazione_ai: Mapped[Optional[Any]] = mapped_column(
        JSON,
        nullable=True,
        doc="Full Claude classification output"
    )

    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="AI confidence score 0.0-1.0"
    )

    verificato_da_utente: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        doc="Whether user has verified the classification"
    )

    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when document was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when document was last updated"
    )

    # Relationships
    cliente: Mapped["Cliente"] = relationship(
        "Cliente",
        back_populates="documenti",
        doc="Relationship to the client"
    )

    contratto: Mapped[Optional["Contratto"]] = relationship(
        "Contratto",
        back_populates="documenti",
        doc="Relationship to the contract"
    )

    def __repr__(self) -> str:
        """String representation of Documento instance."""
        return f"<Documento(id={self.id}, cliente_id={self.cliente_id}, macro='{self.macro_categoria}', tipo='{self.tipo_documento}', anno={self.anno_competenza})>"
