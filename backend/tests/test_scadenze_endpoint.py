"""Tests for the /scadenze list endpoint."""
from datetime import date, timedelta

import pytest

from app.models.scadenza import Scadenza


@pytest.fixture()
def fake_scadenza(db, fake_cliente, fake_documento):
    """Create a Scadenza linked to fake_documento."""
    s = Scadenza(
        documento_id=fake_documento.id,
        cliente_id=fake_cliente.id,
        tipo_scadenza="pagamento",
        data_scadenza=date.today() + timedelta(days=10),
        descrizione="Pagamento test",
        confidence_score=0.9,
        verificato=False,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def test_list_scadenze_returns_all(client, fake_scadenza):
    """GET /scadenze returns all deadlines."""
    response = client.get("/api/v1/scadenze")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tipo_scadenza"] == "pagamento"
    assert data[0]["descrizione"] == "Pagamento test"


def test_list_scadenze_filter_tipo(client, fake_scadenza):
    """Filtering by tipo_scadenza works."""
    response = client.get("/api/v1/scadenze?tipo_scadenza=pagamento")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/api/v1/scadenze?tipo_scadenza=incasso")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_list_scadenze_filter_cliente(client, fake_scadenza, fake_cliente):
    """Filtering by cliente_id works."""
    response = client.get(f"/api/v1/scadenze?cliente_id={fake_cliente.id}")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/api/v1/scadenze?cliente_id=99999")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_list_scadenze_requires_auth(fake_scadenza):
    """Endpoint requires authentication."""
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    response = c.get("/api/v1/scadenze")
    assert response.status_code == 401
