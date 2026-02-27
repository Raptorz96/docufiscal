"""Contratto model for DocuFiscal application."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Contratto(Base):
    """
    Contratto model representing contracts in the system.

    Attributes:
        id: Primary key identifier
        cliente_id: Foreign key to the client
        tipo_contratto_id: Foreign key to the contract type
        data_inizio: Contract start date
        data_fine: Contract end date (nullable)
        stato: Contract status (attivo, scaduto, sospeso)
        note: Optional notes about the contract
        created_at: Timestamp when contract was created
        updated_at: Timestamp when contract was last updated
        cliente: Relationship to the client
        tipo_contratto: Relationship to the contract type
    """
    __tablename__ = "contratti"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Primary key identifier"
    )

    cliente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clienti.id"),
        nullable=False,
        doc="Foreign key to the client"
    )

    tipo_contratto_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tipi_contratto.id"),
        nullable=False,
        doc="Foreign key to the contract type"
    )

    data_inizio: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Contract start date"
    )

    data_fine: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        doc="Contract end date (nullable)"
    )

    stato: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="attivo",
        doc="Contract status (attivo, scaduto, sospeso)"
    )

    note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional notes about the contract"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when contract was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when contract was last updated"
    )

    # Relationships
    cliente: Mapped["Cliente"] = relationship(
        "Cliente",
        back_populates="contratti",
        doc="Relationship to the client"
    )

    tipo_contratto: Mapped["TipoContratto"] = relationship(
        "TipoContratto",
        back_populates="contratti",
        doc="Relationship to the contract type"
    )

    def __repr__(self) -> str:
        """String representation of Contratto instance."""
        return f"<Contratto(id={self.id}, cliente_id={self.cliente_id}, data_inizio='{self.data_inizio}', stato='{self.stato}')>"