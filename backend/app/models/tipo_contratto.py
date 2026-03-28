"""TipoContratto model for DocuFiscal application."""
from typing import List, Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TipoContratto(Base):
    """
    TipoContratto model representing contract types in the system.

    Attributes:
        id: Primary key identifier
        nome: Contract type name (unique)
        descrizione: Optional description of the contract type
        categoria: Contract category (fiscale, previdenziale, societario, lavoro, altro)
        contratti: List of contracts using this type
    """
    __tablename__ = "tipi_contratto"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Primary key identifier"
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        doc="Contract type name (unique)"
    )

    descrizione: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional description of the contract type"
    )

    categoria: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Contract category (fiscale, previdenziale, societario, lavoro, altro)"
    )

    # Relationships
    contratti: Mapped[List["Contratto"]] = relationship(
        "Contratto",
        back_populates="tipo_contratto",
        doc="List of contracts using this type"
    )

    def __repr__(self) -> str:
        """String representation of TipoContratto instance."""
        return f"<TipoContratto(id={self.id}, nome='{self.nome}', categoria='{self.categoria}')>"