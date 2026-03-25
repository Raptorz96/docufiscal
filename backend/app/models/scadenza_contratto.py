"""ScadenzaContratto model — structured data extracted from contract documents."""
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ScadenzaContratto(Base):
    """Structured data extracted by AI from a contract document."""

    __tablename__ = "scadenze_contratto"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    documento_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("documenti.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )

    contratto_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("contratti.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )

    cliente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clienti.id", ondelete="CASCADE"),
        nullable=False,
    )

    data_inizio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_scadenza: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    durata: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rinnovo_automatico: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    preavviso_disdetta: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    canone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parti_coinvolte: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    clausole_chiave: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    confidence_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    verificato: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    documento: Mapped[Optional["Documento"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Documento", back_populates="scadenza_contratto"
    )
    contratto: Mapped[Optional["Contratto"]] = relationship("Contratto")  # type: ignore[name-defined]  # noqa: F821
    cliente: Mapped["Cliente"] = relationship("Cliente")  # type: ignore[name-defined]  # noqa: F821
