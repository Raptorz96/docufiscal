"""Tests for /api/v1/tipi-contratto endpoints."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db
from app.models.tipo_contratto import TipoContratto


def _unauthenticated_client(db: Session) -> TestClient:
    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app, raise_server_exceptions=False)


class TestTipiContratto:

    def test_create_tipo_contratto(self, client: TestClient) -> None:
        resp = client.post("/api/v1/tipi-contratto", json={
            "nome": "Consulenza Fiscale",
            "categoria": "fiscale",
            "descrizione": "Consulenza in materia fiscale",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["nome"] == "Consulenza Fiscale"
        assert data["categoria"] == "fiscale"

    def test_list_tipi_contratto(self, client: TestClient, db: Session) -> None:
        tc = TipoContratto(nome="TC Lista", categoria="legale")
        db.add(tc)
        db.commit()

        resp = client.get("/api/v1/tipi-contratto")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_tipi_contratto_filter_categoria(self, client: TestClient, db: Session) -> None:
        tc = TipoContratto(nome="TC Contabile", categoria="contabile")
        db.add(tc)
        db.commit()

        resp = client.get("/api/v1/tipi-contratto?categoria=contabile")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(t["categoria"] == "contabile" for t in data)

    def test_get_tipo_contratto(self, client: TestClient, db: Session) -> None:
        tc = TipoContratto(nome="TC Get", categoria="fiscale")
        db.add(tc)
        db.commit()
        db.refresh(tc)

        resp = client.get(f"/api/v1/tipi-contratto/{tc.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == tc.id

    def test_get_tipo_contratto_not_found(self, client: TestClient) -> None:
        resp = client.get("/api/v1/tipi-contratto99999")
        assert resp.status_code == 404

    def test_update_tipo_contratto(self, client: TestClient, db: Session) -> None:
        tc = TipoContratto(nome="TC Prima", categoria="fiscale")
        db.add(tc)
        db.commit()
        db.refresh(tc)

        resp = client.put(f"/api/v1/tipi-contratto/{tc.id}", json={
            "nome": "TC Dopo",
        })
        assert resp.status_code == 200
        assert resp.json()["nome"] == "TC Dopo"

    def test_delete_tipo_contratto(self, client: TestClient, db: Session) -> None:
        tc = TipoContratto(nome="TC Eliminare", categoria="legale")
        db.add(tc)
        db.commit()
        db.refresh(tc)

        resp = client.delete(f"/api/v1/tipi-contratto/{tc.id}")
        assert resp.status_code == 204

    def test_list_tipi_contratto_unauthenticated(self, db: Session) -> None:
        tc = _unauthenticated_client(db)
        try:
            resp = tc.get("/api/v1/tipi-contratto")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()
