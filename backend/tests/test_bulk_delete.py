"""Tests for POST /api/v1/documenti/bulk-delete and POST /api/v1/contratti/bulk-delete."""
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento, TipoDocumento
from app.models.scadenza import Scadenza
from app.models.tipo_contratto import TipoContratto


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_documento(db: Session, cliente_id: int, name: str = "test.pdf") -> Documento:
    doc = Documento(
        cliente_id=cliente_id,
        tipo_documento=TipoDocumento.altro.value,
        file_name=name,
        file_path=f"uploads/{name}",
        file_size=1024,
        mime_type="application/pdf",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _make_tipo_contratto(db: Session) -> TipoContratto:
    tc = TipoContratto(nome="TC Bulk Test", categoria="fiscale")
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


def _make_contratto(db: Session, cliente_id: int, tipo_contratto_id: int) -> Contratto:
    c = Contratto(
        cliente_id=cliente_id,
        tipo_contratto_id=tipo_contratto_id,
        data_inizio=date(2024, 1, 1),
        stato="attivo",
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@contextmanager
def _unauthenticated_client(db: Session) -> Iterator[TestClient]:
    from app.main import app
    from app.core.database import get_db

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Documenti bulk-delete
# ---------------------------------------------------------------------------

class TestBulkDeleteDocumenti:

    def test_bulk_delete_ok(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        d1 = _make_documento(db, fake_cliente.id, "bulk1.pdf")
        d2 = _make_documento(db, fake_cliente.id, "bulk2.pdf")
        resp = client.post("/api/v1/documenti/bulk-delete", json={"ids": [d1.id, d2.id]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 2
        assert data["failed"] == []
        assert db.query(Documento).filter(Documento.id == d1.id).first() is None
        assert db.query(Documento).filter(Documento.id == d2.id).first() is None

    def test_bulk_delete_empty_list_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/documenti/bulk-delete", json={"ids": []})
        assert resp.status_code == 422

    def test_bulk_delete_mixed_valid_and_not_found(
        self, client: TestClient, db: Session, fake_cliente: Cliente
    ) -> None:
        d1 = _make_documento(db, fake_cliente.id, "mix.pdf")
        resp = client.post("/api/v1/documenti/bulk-delete", json={"ids": [d1.id, 99999]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 1
        assert len(data["failed"]) == 1
        assert data["failed"][0]["id"] == 99999
        assert db.query(Documento).filter(Documento.id == d1.id).first() is None

    def test_bulk_delete_all_not_found(self, client: TestClient) -> None:
        resp = client.post("/api/v1/documenti/bulk-delete", json={"ids": [88888, 99999]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 0
        assert len(data["failed"]) == 2

    def test_bulk_delete_cleans_scadenze(
        self, client: TestClient, db: Session, fake_cliente: Cliente
    ) -> None:
        d1 = _make_documento(db, fake_cliente.id, "scad.pdf")
        scadenza = Scadenza(
            documento_id=d1.id,
            cliente_id=fake_cliente.id,
            tipo_scadenza="generico",
            confidence_score=0.9,
        )
        db.add(scadenza)
        db.commit()
        scadenza_id = scadenza.id

        resp = client.post("/api/v1/documenti/bulk-delete", json={"ids": [d1.id]})
        assert resp.status_code == 200
        assert resp.json()["deleted"] == 1
        # SQLAlchemy cascade="all, delete-orphan" removes the scadenza
        assert db.query(Scadenza).filter(Scadenza.id == scadenza_id).first() is None

    def test_bulk_delete_unauthenticated(self, db: Session, fake_cliente: Cliente) -> None:
        d1 = _make_documento(db, fake_cliente.id, "auth.pdf")
        with _unauthenticated_client(db) as tc:
            resp = tc.post("/api/v1/documenti/bulk-delete", json={"ids": [d1.id]})
            assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Contratti bulk-delete
# ---------------------------------------------------------------------------

class TestBulkDeleteContratti:

    def test_bulk_delete_ok(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        tc = _make_tipo_contratto(db)
        c1 = _make_contratto(db, fake_cliente.id, tc.id)
        c2 = _make_contratto(db, fake_cliente.id, tc.id)
        resp = client.post("/api/v1/contratti/bulk-delete", json={"ids": [c1.id, c2.id]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 2
        assert data["failed"] == []
        assert db.query(Contratto).filter(Contratto.id == c1.id).first() is None
        assert db.query(Contratto).filter(Contratto.id == c2.id).first() is None

    def test_bulk_delete_empty_list_422(self, client: TestClient) -> None:
        resp = client.post("/api/v1/contratti/bulk-delete", json={"ids": []})
        assert resp.status_code == 422

    def test_bulk_delete_mixed_valid_and_not_found(
        self, client: TestClient, db: Session, fake_cliente: Cliente
    ) -> None:
        tc = _make_tipo_contratto(db)
        c1 = _make_contratto(db, fake_cliente.id, tc.id)
        resp = client.post("/api/v1/contratti/bulk-delete", json={"ids": [c1.id, 99999]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 1
        assert len(data["failed"]) == 1
        assert data["failed"][0]["id"] == 99999
        assert db.query(Contratto).filter(Contratto.id == c1.id).first() is None

    def test_bulk_delete_all_not_found(self, client: TestClient) -> None:
        resp = client.post("/api/v1/contratti/bulk-delete", json={"ids": [88888, 99999]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted"] == 0
        assert len(data["failed"]) == 2

    def test_bulk_delete_unauthenticated(self, db: Session) -> None:
        tc_obj = _make_tipo_contratto(db)
        cliente = Cliente(nome="Test", tipo="azienda")
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        c1 = _make_contratto(db, cliente.id, tc_obj.id)
        with _unauthenticated_client(db) as uc:
            resp = uc.post("/api/v1/contratti/bulk-delete", json={"ids": [c1.id]})
            assert resp.status_code == 401
