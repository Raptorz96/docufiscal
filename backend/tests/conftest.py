"""Shared pytest fixtures for DocuFiscal backend tests.

Provides:
- in-memory SQLite engine / session (StaticPool: single shared connection)
- TestClient with overridden get_db and get_current_user dependencies
- Factory fixtures: fake_user, fake_cliente, fake_documento
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.api.deps import get_current_user
from app.main import app
from app.models.user import User
from app.models.cliente import Cliente
from app.models.contratto import Contratto          # noqa: F401 — registers table
from app.models.tipo_contratto import TipoContratto  # noqa: F401 — registers table
from app.models.documento import Documento, TipoDocumento
from app.models.scadenza import Scadenza  # noqa: F401 — registers table

# ---------------------------------------------------------------------------
# In-memory SQLite engine with StaticPool:
# StaticPool ensures ALL SQLAlchemy sessions share the SAME underlying
# connection, so data written by fixtures is visible inside HTTP requests.
# ---------------------------------------------------------------------------
_TEST_DATABASE_URL = "sqlite:///:memory:"

_engine = create_engine(
    _TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


@pytest.fixture()
def db() -> Session:
    """Provide a fresh SQLite in-memory session for each test."""
    Base.metadata.create_all(bind=_engine)
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def fake_user(db: Session) -> User:
    """Create and persist a test User."""
    user = User(
        email="test@docufiscal.it",
        hashed_password="hashed_irrelevant",
        nome="Mario",
        cognome="Rossi",
        role="commercialista",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def fake_cliente(db: Session) -> Cliente:
    """Create and persist a test Cliente."""
    cliente = Cliente(
        nome="Giovanni",
        cognome="Bianchi",
        codice_fiscale="BNCGVN80A01H501Z",
        tipo="persona_fisica",
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@pytest.fixture()
def fake_documento(db: Session, fake_cliente: Cliente) -> Documento:
    """Create and persist a test Documento with AI classification data."""
    documento = Documento(
        cliente_id=fake_cliente.id,
        tipo_documento=TipoDocumento.altro.value,
        file_name="test.pdf",
        file_path="uploads/test.pdf",
        file_size=1024,
        mime_type="application/pdf",
        classificazione_ai={"tipo_documento": "fattura", "confidence": 0.92},
        confidence_score=0.92,
        verificato_da_utente=False,
    )
    db.add(documento)
    db.commit()
    db.refresh(documento)
    return documento


@pytest.fixture()
def client(db: Session, fake_user: User) -> TestClient:
    """TestClient with db and current_user dependencies overridden."""

    def _override_get_db():
        yield db

    def _override_get_current_user():
        return fake_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
