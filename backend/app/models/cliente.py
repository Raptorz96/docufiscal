"""Cliente model for DocuFiscal application."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Cliente(Base):
    """
    Cliente model representing clients in the system.

    Attributes:
        id: Primary key identifier
        nome: Client's first name or company name
        cognome: Client's last name (nullable for companies)
        codice_fiscale: Italian tax code (unique)
        partita_iva: Italian VAT number (unique)
        tipo: Client type (persona_fisica or azienda)
        email: Client's email address
        telefono: Client's phone number
        created_at: Timestamp when client was created
        updated_at: Timestamp when client was last updated
        contratti: List of contracts associated with this client
    """
    __tablename__ = "clienti"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Primary key identifier"
    )

    short_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        unique=True,
        index=True,
        nullable=True,
        doc="Unique numeric short ID for rapid routing"
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Client's first name or company name"
    )

    cognome: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Client's last name (nullable for companies)"
    )

    codice_fiscale: Mapped[Optional[str]] = mapped_column(
        String(16),
        unique=True,
        index=True,
        nullable=True,
        doc="Italian tax code (unique)"
    )

    partita_iva: Mapped[Optional[str]] = mapped_column(
        String(11),
        unique=True,
        index=True,
        nullable=True,
        doc="Italian VAT number (unique)"
    )

    tipo: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="persona_fisica",
        doc="Client type (persona_fisica or azienda)"
    )

    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Client's email address"
    )

    telefono: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Client's phone number"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when client was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when client was last updated"
    )

    # Relationships
    contratti: Mapped[List["Contratto"]] = relationship(
        "Contratto",
        back_populates="cliente",
        doc="List of contracts associated with this client"
    )

    documenti: Mapped[List["Documento"]] = relationship(
        "Documento",
        back_populates="cliente",
        doc="List of documents associated with this client"
    )

    def __repr__(self) -> str:
        """String representation of Cliente instance."""
        return f"<Cliente(id={self.id}, short_id={self.short_id}, nome='{self.nome}', cognome='{self.cognome}', tipo='{self.tipo}')>"