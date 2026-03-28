"""User model for DocuFiscal application."""
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.google_token import GoogleToken


class User(Base):
    """
    User model representing registered users in the system.

    Attributes:
        id: Primary key identifier
        email: Unique email address for authentication
        hashed_password: Bcrypt hashed password
        nome: User's first name
        cognome: User's last name
        role: User role (default: commercialista)
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Primary key identifier"
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique email address for authentication"
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt hashed password"
    )

    nome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User's first name"
    )

    cognome: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User's last name"
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="commercialista",
        doc="User role in the system"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Whether the user account is active"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        doc="Timestamp when user was created"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        doc="Timestamp when user was last updated"
    )

    google_token: Mapped[Optional["GoogleToken"]] = relationship(
        "GoogleToken", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation of User instance."""
        return f"<User(id={self.id}, email='{self.email}', nome='{self.nome}', cognome='{self.cognome}')>"