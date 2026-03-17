"""Tests for /api/v1/clienti endpoints."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.cliente import Cliente


def _unauthenticated_client(db: Session) -> TestClient:
    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app, raise_server_exceptions=False)


class TestClienti:

    def test_create_cliente(self, client: TestClient) -> None:
        resp = client.post("/api/v1/clienti/", json={
            "nome": "Anna",
            "cognome": "Neri",
            "codice_fiscale": "NRANNA80B41H501X",
            "tipo": "persona_fisica",
            "email": "anna.neri@email.it",
            "telefono": "3331234567",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["nome"] == "Anna"
        assert data["cognome"] == "Neri"
        assert data["tipo"] == "persona_fisica"

    def test_create_cliente_azienda(self, client: TestClient) -> None:
        resp = client.post("/api/v1/clienti/", json={
            "nome": "Acme Srl",
            "tipo": "azienda",
            "partita_iva": "12345678901",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo"] == "azienda"
        assert data["partita_iva"] == "12345678901"

    def test_list_clienti(self, client: TestClient, fake_cliente: Cliente) -> None:
        resp = client.get("/api/v1/clienti/")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_clienti_filter_tipo(self, client: TestClient, fake_cliente: Cliente) -> None:
        resp = client.get("/api/v1/clienti/?tipo=persona_fisica")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(c["tipo"] == "persona_fisica" for c in data)

    def test_list_clienti_search(self, client: TestClient, fake_cliente: Cliente) -> None:
        resp = client.get("/api/v1/clienti/?search=Bianchi")
        assert resp.status_code == 200
        data = resp.json()
        assert any("Bianchi" in (c.get("cognome") or "") for c in data)

    def test_get_cliente(self, client: TestClient, fake_cliente: Cliente) -> None:
        resp = client.get(f"/api/v1/clienti/{fake_cliente.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == fake_cliente.id

    def test_get_cliente_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/clienti/99999")
        assert resp.status_code == 404

    def test_update_cliente(self, client: TestClient, fake_cliente: Cliente) -> None:
        resp = client.put(f"/api/v1/clienti/{fake_cliente.id}", json={
            "nome": "Giovanni Aggiornato",
        })
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Giovanni Aggiornato"

    def test_delete_cliente(self, client: TestClient, db: Session) -> None:
        # Create a fresh cliente with no contracts so deletion succeeds
        c = Cliente(nome="ToDelete", tipo="persona_fisica")
        db.add(c)
        db.commit()
        db.refresh(c)

        resp = client.delete(f"/api/v1/clienti/{c.id}")
        assert resp.status_code == 204

    def test_delete_cliente_not_found(self, client: TestClient) -> None:
        resp = client.delete("/api/v1/clienti/99999")
        assert resp.status_code == 404

    def test_list_clienti_unauthenticated(self, db: Session) -> None:
        tc = _unauthenticated_client(db)
        try:
            resp = tc.get("/api/v1/clienti/")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()
