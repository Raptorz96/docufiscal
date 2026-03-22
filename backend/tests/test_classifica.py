"""Tests for PATCH /api/v1/documenti/{documento_id}/classifica endpoint.

Covers:
1. Conferma pura  — body vuoto: solo verificato_da_utente=True, tipo invariato.
2. Override tipo  — tipo_documento specificato: tipo aggiornato + verificato=True.
3. Documento non trovato — 404.
4. Contratto di altro cliente — 400.
5. Non autenticato — 401.
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.contratto import Contratto
from app.models.cliente import Cliente
from app.models.documento import Documento, TipoDocumento
from app.models.tipo_contratto import TipoContratto


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _url(documento_id: int) -> str:
    return f"/api/v1/documenti/{documento_id}/classifica"


def _make_tipo_contratto(db: Session) -> TipoContratto:
    """Persist a minimal TipoContratto needed to satisfy the FK."""
    tc = TipoContratto(
        nome="Consulenza fiscale",
        categoria="fiscale",
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


def _make_contratto(db: Session, cliente_id: int, tipo_contratto_id: int) -> Contratto:
    """Persist a Contratto linked to the given cliente."""
    contratto = Contratto(
        cliente_id=cliente_id,
        tipo_contratto_id=tipo_contratto_id,
        data_inizio=date(2024, 1, 1),
        stato="attivo",
    )
    db.add(contratto)
    db.commit()
    db.refresh(contratto)
    return contratto


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestConfermaClassificazione:
    """Endpoint PATCH /documenti/{id}/classifica."""

    def test_conferma_pura(
        self, client: TestClient, fake_documento: Documento
    ) -> None:
        """Body vuoto: tipo_documento rimane invariato, verificato_da_utente=True."""
        original_tipo = fake_documento.tipo_documento

        resp = client.patch(_url(fake_documento.id), json={})

        assert resp.status_code == 200
        data = resp.json()
        assert data["verificato_da_utente"] is True
        assert data["tipo_documento"] == original_tipo

    def test_override_tipo_documento(
        self, client: TestClient, fake_documento: Documento
    ) -> None:
        """tipo_documento esplicito: tipo aggiornato + verificato=True."""
        resp = client.patch(
            _url(fake_documento.id),
            json={"tipo_documento": "fattura"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["verificato_da_utente"] is True
        assert data["tipo_documento"] == "fattura"

    def test_override_con_note(
        self, client: TestClient, fake_documento: Documento
    ) -> None:
        """Override con note: note aggiornate nel documento."""
        resp = client.patch(
            _url(fake_documento.id),
            json={"tipo_documento": "f24", "note": "Verificato manualmente"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["tipo_documento"] == "f24"
        assert data["note"] == "Verificato manualmente"
        assert data["verificato_da_utente"] is True

    def test_documento_not_found(self, client: TestClient) -> None:
        """Documento inesistente → 404."""
        resp = client.patch(_url(99999), json={})
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_contratto_wrong_cliente(
        self,
        client: TestClient,
        db: Session,
        fake_documento: Documento,
    ) -> None:
        """contratto_id di un altro cliente → 400."""
        # Crea un secondo cliente e un contratto associato a lui
        altro_cliente = Cliente(nome="Altro", tipo="azienda")
        db.add(altro_cliente)
        db.commit()
        db.refresh(altro_cliente)

        tc = _make_tipo_contratto(db)
        contratto_altro = _make_contratto(db, altro_cliente.id, tc.id)

        resp = client.patch(
            _url(fake_documento.id),
            json={"contratto_id": contratto_altro.id},
        )

        assert resp.status_code == 400
        assert "cliente" in resp.json()["detail"].lower()

    def test_unauthenticated(
        self, db: Session, fake_documento: Documento
    ) -> None:
        """Nessun JWT → 401 (get_current_user NON overridato)."""
        from app.main import app
        from app.core.database import get_db

        def _override_get_db():
            yield db

        app.dependency_overrides[get_db] = _override_get_db
        # get_current_user NON viene overridato → richiede token reale
        try:
            with TestClient(app, raise_server_exceptions=False) as unauthenticated:
                resp = unauthenticated.patch(_url(fake_documento.id), json={})
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()
