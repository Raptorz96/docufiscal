"""Tests for /api/v1/contratti endpoints."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.tipo_contratto import TipoContratto


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tipo_contratto(db: Session, nome: str = "Consulenza fiscale") -> TipoContratto:
    tc = TipoContratto(nome=nome, categoria="fiscale")
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


def _make_cliente(db: Session, nome: str = "Cliente Test") -> Cliente:
    c = Cliente(nome=nome, tipo="persona_fisica")
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _unauthenticated_client(db: Session) -> TestClient:
    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestContratti:

    def test_create_contratto(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        tc = _make_tipo_contratto(db)
        resp = client.post("/api/v1/contratti", json={
            "cliente_id": fake_cliente.id,
            "tipo_contratto_id": tc.id,
            "data_inizio": "2024-01-01",
            "stato": "attivo",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["cliente_id"] == fake_cliente.id
        assert data["tipo_contratto_id"] == tc.id
        assert data["stato"] == "attivo"

    def test_create_contratto_cliente_not_found(self, client: TestClient, db: Session) -> None:
        tc = _make_tipo_contratto(db, "TC per cliente assente")
        resp = client.post("/api/v1/contratti", json={
            "cliente_id": 99999,
            "tipo_contratto_id": tc.id,
            "data_inizio": "2024-01-01",
        })
        assert resp.status_code == 404

    def test_create_contratto_tipo_not_found(self, client: TestClient, fake_cliente: Cliente) -> None:
        resp = client.post("/api/v1/contratti", json={
            "cliente_id": fake_cliente.id,
            "tipo_contratto_id": 99999,
            "data_inizio": "2024-01-01",
        })
        assert resp.status_code == 404

    def test_list_contratti(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        tc = _make_tipo_contratto(db, "TC List")
        client.post("/api/v1/contratti", json={
            "cliente_id": fake_cliente.id,
            "tipo_contratto_id": tc.id,
            "data_inizio": "2024-01-01",
        })
        resp = client.get("/api/v1/contratti")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_contratti_filter_cliente(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        tc = _make_tipo_contratto(db, "TC Filter Cliente")
        client.post("/api/v1/contratti", json={
            "cliente_id": fake_cliente.id,
            "tipo_contratto_id": tc.id,
            "data_inizio": "2024-01-01",
        })
        resp = client.get(f"/api/v1/contratti?cliente_id={fake_cliente.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(c["cliente_id"] == fake_cliente.id for c in data)

    def test_list_contratti_filter_stato(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        tc = _make_tipo_contratto(db, "TC Filter Stato")
        client.post("/api/v1/contratti", json={
            "cliente_id": fake_cliente.id,
            "tipo_contratto_id": tc.id,
            "data_inizio": "2024-01-01",
            "stato": "sospeso",
        })
        resp = client.get("/api/v1/contratti?stato=sospeso")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(c["stato"] == "sospeso" for c in data)

    def test_get_contratto(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        tc = _make_tipo_contratto(db, "TC Get")
        create_resp = client.post("/api/v1/contratti", json={
            "cliente_id": fake_cliente.id,
            "tipo_contratto_id": tc.id,
            "data_inizio": "2024-01-01",
        })
        contratto_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/contratti/{contratto_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == contratto_id

    def test_get_contratto_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/contratti99999")
        assert resp.status_code == 404

    def test_update_contratto(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        tc = _make_tipo_contratto(db, "TC Update")
        create_resp = client.post("/api/v1/contratti", json={
            "cliente_id": fake_cliente.id,
            "tipo_contratto_id": tc.id,
            "data_inizio": "2024-01-01",
            "stato": "attivo",
        })
        contratto_id = create_resp.json()["id"]

        resp = client.put(f"/api/v1/contratti/{contratto_id}", json={
            "stato": "scaduto",
        })
        assert resp.status_code == 200
        assert resp.json()["stato"] == "scaduto"

    def test_delete_contratto(self, client: TestClient, db: Session, fake_cliente: Cliente) -> None:
        tc = _make_tipo_contratto(db, "TC Delete")
        create_resp = client.post("/api/v1/contratti", json={
            "cliente_id": fake_cliente.id,
            "tipo_contratto_id": tc.id,
            "data_inizio": "2024-01-01",
        })
        contratto_id = create_resp.json()["id"]

        resp = client.delete(f"/api/v1/contratti/{contratto_id}")
        assert resp.status_code == 204

    def test_list_contratti_unauthenticated(self, db: Session) -> None:
        tc = _unauthenticated_client(db)
        try:
            resp = tc.get("/api/v1/contratti")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()
