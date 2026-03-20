"""Tests for authentication endpoints: register, login, me."""
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _raw_client(db: Session) -> TestClient:
    """TestClient with only get_db overridden — no auth bypass."""
    def _override_get_db():
        yield db
    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

class TestRegister:

    def test_register_success(self, db: Session) -> None:
        tc = _raw_client(db)
        try:
            resp = tc.post("/api/v1/auth/register", json={
                "email": "nuovo@docufiscal.it",
                "password": "password123",
                "nome": "Luca",
                "cognome": "Verdi",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert data["email"] == "nuovo@docufiscal.it"
            assert data["nome"] == "Luca"
            assert data["cognome"] == "Verdi"
        finally:
            app.dependency_overrides.clear()

    def test_register_duplicate_email(self, db: Session) -> None:
        tc = _raw_client(db)
        try:
            payload = {
                "email": "dup@docufiscal.it",
                "password": "password123",
                "nome": "A",
                "cognome": "B",
            }
            tc.post("/api/v1/auth/register", json=payload)
            resp = tc.post("/api/v1/auth/register", json=payload)
            assert resp.status_code == 409
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:

    def test_login_success(self, db: Session) -> None:
        tc = _raw_client(db)
        try:
            # Register a user with a real password hash first
            tc.post("/api/v1/auth/register", json={
                "email": "login_ok@docufiscal.it",
                "password": "mypassword",
                "nome": "Test",
                "cognome": "User",
            })
            resp = tc.post("/api/v1/auth/login", data={
                "username": "login_ok@docufiscal.it",
                "password": "mypassword",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
        finally:
            app.dependency_overrides.clear()

    def test_login_wrong_password(self, db: Session) -> None:
        tc = _raw_client(db)
        try:
            tc.post("/api/v1/auth/register", json={
                "email": "login_bad@docufiscal.it",
                "password": "correct_password",
                "nome": "Test",
                "cognome": "User",
            })
            resp = tc.post("/api/v1/auth/login", data={
                "username": "login_bad@docufiscal.it",
                "password": "wrong_password",
            })
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()

    def test_login_nonexistent_email(self, db: Session) -> None:
        tc = _raw_client(db)
        try:
            resp = tc.post("/api/v1/auth/login", data={
                "username": "nonexistent@docufiscal.it",
                "password": "anypassword",
            })
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------

class TestMe:

    def test_me_authenticated(self, client: TestClient) -> None:
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert "email" in data
        assert "nome" in data
        assert "cognome" in data

    def test_me_unauthenticated(self, db: Session) -> None:
        tc = _raw_client(db)
        try:
            resp = tc.get("/api/v1/auth/me")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Update Profile (PATCH /auth/me)
# ---------------------------------------------------------------------------

class TestUpdateProfile:

    def test_update_nome_cognome(self, client: TestClient, fake_user) -> None:
        resp = client.patch("/api/v1/auth/me", json={"nome": "Luigi", "cognome": "Neri"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["nome"] == "Luigi"
        assert data["cognome"] == "Neri"

    def test_update_email_success(self, client: TestClient, fake_user) -> None:
        resp = client.patch("/api/v1/auth/me", json={"email": "nuovo@docufiscal.it"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "nuovo@docufiscal.it"

    def test_update_email_conflict(self, client: TestClient, db, fake_user) -> None:
        from app.models.user import User as UserModel
        other = UserModel(
            email="altro@docufiscal.it",
            hashed_password="x",
            nome="A",
            cognome="B",
        )
        db.add(other)
        db.commit()
        resp = client.patch("/api/v1/auth/me", json={"email": "altro@docufiscal.it"})
        assert resp.status_code == 409

    def test_update_empty_nome_rejected(self, client: TestClient, fake_user) -> None:
        resp = client.patch("/api/v1/auth/me", json={"nome": ""})
        assert resp.status_code == 422

    def test_update_noop(self, client: TestClient, fake_user) -> None:
        resp = client.patch("/api/v1/auth/me", json={})
        assert resp.status_code == 200
        assert resp.json()["nome"] == fake_user.nome

    def test_update_unauthenticated(self, db) -> None:
        from app.main import app
        from app.core.database import get_db
        from fastapi.testclient import TestClient

        def _override():
            yield db

        app.dependency_overrides[get_db] = _override
        try:
            tc = TestClient(app, raise_server_exceptions=False)
            resp = tc.patch("/api/v1/auth/me", json={"nome": "X"})
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Change Password (POST /auth/change-password)
# ---------------------------------------------------------------------------

class TestChangePassword:

    def _register_and_login(self, db) -> str:
        """Register a user with a real password hash and return a valid JWT."""
        from app.main import app
        from app.core.database import get_db

        def _override():
            yield db

        app.dependency_overrides[get_db] = _override
        tc = TestClient(app, raise_server_exceptions=False)
        tc.post("/api/v1/auth/register", json={
            "email": "pwchange@docufiscal.it",
            "password": "OldPassword1",
            "nome": "Test",
            "cognome": "User",
        })
        resp = tc.post("/api/v1/auth/login", data={
            "username": "pwchange@docufiscal.it",
            "password": "OldPassword1",
        })
        app.dependency_overrides.clear()
        return resp.json()["access_token"]

    def test_change_password_success(self, db) -> None:
        from app.main import app
        from app.core.database import get_db

        token = self._register_and_login(db)

        def _override():
            yield db

        app.dependency_overrides[get_db] = _override
        try:
            tc = TestClient(app, raise_server_exceptions=False)
            resp = tc.post(
                "/api/v1/auth/change-password",
                json={"current_password": "OldPassword1", "new_password": "NewPassword2"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            assert resp.json()["detail"] == "Password aggiornata con successo"
        finally:
            app.dependency_overrides.clear()

    def test_change_password_wrong_current(self, db) -> None:
        from app.main import app
        from app.core.database import get_db

        token = self._register_and_login(db)

        def _override():
            yield db

        app.dependency_overrides[get_db] = _override
        try:
            tc = TestClient(app, raise_server_exceptions=False)
            resp = tc.post(
                "/api/v1/auth/change-password",
                json={"current_password": "WrongPassword", "new_password": "NewPassword2"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 400
            assert "corrente" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_change_password_too_short(self, db) -> None:
        from app.main import app
        from app.core.database import get_db

        token = self._register_and_login(db)

        def _override():
            yield db

        app.dependency_overrides[get_db] = _override
        try:
            tc = TestClient(app, raise_server_exceptions=False)
            resp = tc.post(
                "/api/v1/auth/change-password",
                json={"current_password": "OldPassword1", "new_password": "short"},
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 400
            assert "8" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    def test_change_password_unauthenticated(self, db) -> None:
        from app.main import app
        from app.core.database import get_db

        def _override():
            yield db

        app.dependency_overrides[get_db] = _override
        try:
            tc = TestClient(app, raise_server_exceptions=False)
            resp = tc.post(
                "/api/v1/auth/change-password",
                json={"current_password": "any", "new_password": "anypassword"},
            )
            assert resp.status_code == 401
        finally:
            app.dependency_overrides.clear()
