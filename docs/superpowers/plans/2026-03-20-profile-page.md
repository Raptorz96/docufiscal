# Profile Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a user profile page where authenticated users can update their name/surname/email and change their password.

**Architecture:** Backend exposes `PATCH /auth/me` and `POST /auth/change-password`. Frontend adds `ProfilePage` at `/profilo` reachable via a NavLink on the username in the sidebar. Email changes force logout because the JWT `sub` contains the email used by `get_current_user` to look up the user.

**Tech Stack:** FastAPI + SQLAlchemy (backend), React 18 + TypeScript + TailwindCSS v3 + React Router v6 + Axios (frontend). Tests: pytest with SQLite in-memory, FastAPI TestClient.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/app/schemas/user.py` | Modify | Add `UserUpdate`, `PasswordChange` schemas |
| `backend/app/api/auth.py` | Modify | Add `PATCH /auth/me`, `POST /auth/change-password` |
| `backend/tests/test_auth.py` | Modify | Add tests for both new endpoints |
| `frontend/src/types/auth.ts` | Modify | Add `created_at` to `User`, add `ProfileUpdate`, `PasswordChangeRequest` |
| `frontend/src/services/authService.ts` | Modify | Add `updateProfile`, `changePassword` |
| `frontend/src/context/AuthContext.tsx` | Modify | Add `refreshUser` to context |
| `frontend/src/pages/ProfilePage.tsx` | Create | Profile + password change UI |
| `frontend/src/App.tsx` | Modify | Add `/profilo` protected route |
| `frontend/src/layouts/AppLayout.tsx` | Modify | Wrap username `<span>` with `<NavLink to="/profilo">` |
| `frontend/src/pages/LoginPage.tsx` | Modify | Show banner from `location.state.message` |

---

## Task 1: Backend schemas

**Files:**
- Modify: `backend/app/schemas/user.py`

- [ ] **Step 1: Add `UserUpdate` and `PasswordChange` to schemas**

Open `backend/app/schemas/user.py`. Add at the bottom, after the `Token` class:

```python
class UserUpdate(BaseModel):
    """Schema for user profile update. All fields optional — only non-None are applied."""
    nome: str | None = None
    cognome: str | None = None
    email: EmailStr | None = None

    @field_validator('nome', 'cognome')
    @classmethod
    def not_empty(cls, v: str | None) -> str | None:
        if v is not None and v.strip() == '':
            raise ValueError('Il campo non può essere vuoto')
        return v


class PasswordChange(BaseModel):
    """Schema for password change. Length validation is in the route handler (→ 400)."""
    current_password: str
    new_password: str
```

Also update the import line at the top to include `field_validator`:

```python
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
```

- [ ] **Step 2: Verify schemas parse correctly**

```bash
cd backend && python -c "
from app.schemas.user import UserUpdate, PasswordChange
u = UserUpdate(nome='Mario')
assert u.nome == 'Mario' and u.cognome is None
p = PasswordChange(current_password='old', new_password='new')
assert p.new_password == 'new'
print('OK')
"
```

Expected: `OK`

- [ ] **Step 3: Verify `field_validator` rejects empty strings**

```bash
cd backend && python -c "
from pydantic import ValidationError
from app.schemas.user import UserUpdate
try:
    UserUpdate(nome='')
    print('FAIL — should have raised')
except ValidationError:
    print('OK — empty string rejected')
"
```

Expected: `OK — empty string rejected`

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/user.py
git commit -m "feat(backend): add UserUpdate and PasswordChange schemas"
```

---

## Task 2: Backend endpoint `PATCH /auth/me`

**Files:**
- Modify: `backend/app/api/auth.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing tests for `PATCH /auth/me`**

Append a new test class to `backend/tests/test_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests — verify they fail with 404 (endpoint not yet defined)**

```bash
cd backend && python -m pytest tests/test_auth.py::TestUpdateProfile -v
```

Expected: all tests fail, most with `AssertionError` (404 → expected 200/409/422).

- [ ] **Step 3: Implement `PATCH /auth/me` in `auth.py`**

Update the import line in `backend/app/api/auth.py`:

```python
from app.schemas.user import UserCreate, UserResponse, Token, UserUpdate, PasswordChange
```

Add the endpoint after the `get_current_user_profile` function:

```python
@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Update current user's profile (nome, cognome, email).
    Only non-None fields are applied. Email change is allowed but will
    invalidate the current JWT token (sub = email).
    """
    # No-op if nothing provided
    if all(v is None for v in user_data.model_dump().values()):
        return UserResponse.model_validate(current_user)

    # Check email uniqueness
    if user_data.email is not None and user_data.email != current_user.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email già in uso da un altro account",
            )

    # Apply updates
    if user_data.nome is not None:
        current_user.nome = user_data.nome
    if user_data.cognome is not None:
        current_user.cognome = user_data.cognome
    if user_data.email is not None:
        current_user.email = user_data.email

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd backend && python -m pytest tests/test_auth.py::TestUpdateProfile -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/auth.py backend/tests/test_auth.py
git commit -m "feat(backend): PATCH /auth/me — update user profile"
```

---

## Task 3: Backend endpoint `POST /auth/change-password`

**Files:**
- Modify: `backend/app/api/auth.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing tests for `POST /auth/change-password`**

The `fake_user` fixture uses a non-bcrypt hash (`hashed_password="hashed_irrelevant"`), so `verify_password` will always fail for it. These tests use `_raw_client` + register + login to get a real JWT, then test with that token.

Append this class to `backend/tests/test_auth.py`:

```python
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
```

- [ ] **Step 2: Run tests — verify they fail with 404**

```bash
cd backend && python -m pytest tests/test_auth.py::TestChangePassword -v
```

Expected: all 4 fail with 404 (endpoint not yet implemented).

- [ ] **Step 3: Implement `POST /auth/change-password` in `auth.py`**

Add after `update_current_user_profile`:

```python
@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Change current user's password.
    Verifies current password, enforces min length of 8, then saves new hash.
    Does NOT invalidate existing JWT tokens.
    """
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password corrente non corretta",
        )

    if len(password_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La password deve essere di almeno 8 caratteri",
        )

    current_user.hashed_password = hash_password(password_data.new_password)
    db.commit()
    db.refresh(current_user)
    return {"detail": "Password aggiornata con successo"}
```

- [ ] **Step 4: Run all auth tests**

```bash
cd backend && python -m pytest tests/test_auth.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/auth.py backend/tests/test_auth.py
git commit -m "feat(backend): POST /auth/change-password"
```

---

## Task 4: Frontend types and authService

**Files:**
- Modify: `frontend/src/types/auth.ts`
- Modify: `frontend/src/services/authService.ts`

No frontend unit tests exist in this project — no test files to write.

- [ ] **Step 1: Update `types/auth.ts`**

Add `created_at: string` to the `User` interface and append the two new interfaces. Final file:

```typescript
export interface User {
  id: number;
  email: string;
  nome: string;
  cognome: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterData {
  email: string;
  password: string;
  nome: string;
  cognome: string;
}

export interface ProfileUpdate {
  nome?: string;
  cognome?: string;
  email?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}
```

- [ ] **Step 2: Update `authService.ts`**

Update the import line and add the two new functions. Final file:

```typescript
import api from './api';
import type { LoginCredentials, AuthResponse, User, ProfileUpdate, PasswordChangeRequest } from '../types/auth';

export const login = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.email);
  formData.append('password', credentials.password);

  const response = await api.post<AuthResponse>('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  return response.data;
};

export const getMe = async (): Promise<User> => {
  const response = await api.get<User>('/auth/me');
  return response.data;
};

export const saveToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

export const removeToken = (): void => {
  localStorage.removeItem('access_token');
};

export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

export const updateProfile = async (data: ProfileUpdate): Promise<User> => {
  const response = await api.patch<User>('/auth/me', data);
  return response.data;
};

export const changePassword = async (data: PasswordChangeRequest): Promise<void> => {
  await api.post('/auth/change-password', data);
};
```

- [ ] **Step 3: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/auth.ts frontend/src/services/authService.ts
git commit -m "feat(frontend): add ProfileUpdate, PasswordChangeRequest types and authService methods"
```

---

## Task 5: AuthContext `refreshUser`

**Files:**
- Modify: `frontend/src/context/AuthContext.tsx`

- [ ] **Step 1: Update `AuthContext.tsx`**

Replace the current file content with the updated version that adds `refreshUser`:

```typescript
import React, { createContext, useContext, useEffect, useState } from 'react';
import type { User, LoginCredentials } from '../types/auth';
import * as authService from '../services/authService';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      const token = authService.getToken();
      if (token) {
        try {
          const userData = await authService.getMe();
          setUser(userData);
        } catch (error) {
          console.error('Failed to validate token:', error);
          authService.removeToken();
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials: LoginCredentials): Promise<void> => {
    try {
      const response = await authService.login(credentials);
      authService.saveToken(response.access_token);
      const userData = await authService.getMe();
      setUser(userData);
    } catch (error) {
      throw error;
    }
  };

  const logout = (): void => {
    authService.removeToken();
    setUser(null);
  };

  const refreshUser = async (): Promise<void> => {
    const userData = await authService.getMe();
    setUser(userData);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/context/AuthContext.tsx
git commit -m "feat(frontend): add refreshUser to AuthContext"
```

---

## Task 6: ProfilePage

**Files:**
- Create: `frontend/src/pages/ProfilePage.tsx`

- [ ] **Step 1: Create `ProfilePage.tsx`**

```typescript
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AxiosError } from 'axios';
import { useAuth } from '../context/AuthContext';
import * as authService from '../services/authService';

const ProfilePage: React.FC = () => {
  const { user, logout, refreshUser } = useAuth();
  const navigate = useNavigate();

  // --- Profile form state ---
  const [profileForm, setProfileForm] = useState({
    nome: '',
    cognome: '',
    email: '',
  });
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState('');
  const [profileError, setProfileError] = useState('');

  // --- Password form state ---
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // Populate profile form from user context on mount / user change
  useEffect(() => {
    if (user) {
      setProfileForm({
        nome: user.nome,
        cognome: user.cognome,
        email: user.email,
      });
    }
  }, [user]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileError('');
    setProfileSuccess('');

    // Determine if email is changing BEFORE making any request
    const emailChanged = profileForm.email !== user?.email;

    setProfileLoading(true);
    try {
      await authService.updateProfile({
        nome: profileForm.nome,
        cognome: profileForm.cognome,
        email: profileForm.email,
      });

      if (emailChanged) {
        // Token is now invalid (sub = old email). Logout immediately and
        // redirect to login with message — do NOT call refreshUser() here
        // as it would trigger the 401 global interceptor and lose the message.
        logout();
        navigate('/login', { state: { message: 'Email aggiornata. Effettua nuovamente il login.' } });
      } else {
        await refreshUser();
        setProfileSuccess('Profilo aggiornato con successo.');
      }
    } catch (err) {
      if (err instanceof AxiosError) {
        if (err.response?.status === 409) {
          setProfileError('Email già in uso da un altro account.');
        } else {
          setProfileError('Errore imprevisto. Riprova.');
        }
      } else {
        setProfileError('Errore imprevisto. Riprova.');
      }
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError('');
    setPasswordSuccess('');

    // Client-side validation
    if (passwordForm.new_password.length < 8) {
      setPasswordError('La nuova password deve essere di almeno 8 caratteri.');
      return;
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError('Le password non corrispondono.');
      return;
    }

    setPasswordLoading(true);
    try {
      await authService.changePassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password,
      });
      setPasswordSuccess('Password aggiornata con successo.');
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      if (err instanceof AxiosError && err.response?.status === 400) {
        setPasswordError(err.response.data?.detail ?? 'Errore nella modifica della password.');
      } else {
        setPasswordError('Errore imprevisto. Riprova.');
      }
    } finally {
      setPasswordLoading(false);
    }
  };

  const inputClass =
    'w-full px-3 py-2 border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1';
  const btnPrimary =
    'px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed';

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString('it-IT', {
        day: '2-digit', month: 'long', year: 'numeric',
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Il mio profilo</h1>

      {/* Section 1 — Profile data */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Dati personali</h2>

        {/* Read-only info */}
        <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-md text-sm">
          <div>
            <span className="font-medium text-gray-500">Ruolo</span>
            <p className="text-gray-800 mt-0.5 capitalize">{user?.role ?? '—'}</p>
          </div>
          <div>
            <span className="font-medium text-gray-500">Registrato il</span>
            <p className="text-gray-800 mt-0.5">
              {user?.created_at ? formatDate(user.created_at) : '—'}
            </p>
          </div>
        </div>

        <form onSubmit={handleProfileSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass} htmlFor="nome">Nome</label>
              <input
                id="nome"
                type="text"
                required
                className={inputClass}
                value={profileForm.nome}
                onChange={(e) => setProfileForm((f) => ({ ...f, nome: e.target.value }))}
              />
            </div>
            <div>
              <label className={labelClass} htmlFor="cognome">Cognome</label>
              <input
                id="cognome"
                type="text"
                required
                className={inputClass}
                value={profileForm.cognome}
                onChange={(e) => setProfileForm((f) => ({ ...f, cognome: e.target.value }))}
              />
            </div>
          </div>

          <div>
            <label className={labelClass} htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              className={inputClass}
              value={profileForm.email}
              onChange={(e) => setProfileForm((f) => ({ ...f, email: e.target.value }))}
            />
            <p className="text-xs text-amber-600 mt-1">
              Attenzione: cambiare l'email richiede un nuovo accesso.
            </p>
          </div>

          {profileSuccess && (
            <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-md px-4 py-3">
              {profileSuccess}
            </div>
          )}
          {profileError && (
            <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md px-4 py-3">
              {profileError}
            </div>
          )}

          <div className="flex justify-end">
            <button type="submit" disabled={profileLoading} className={btnPrimary}>
              {profileLoading ? 'Salvataggio...' : 'Salva modifiche'}
            </button>
          </div>
        </form>
      </div>

      {/* Section 2 — Password change */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Cambia password</h2>

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className={labelClass} htmlFor="current_password">Password corrente</label>
            <input
              id="current_password"
              type="password"
              required
              autoComplete="current-password"
              className={inputClass}
              value={passwordForm.current_password}
              onChange={(e) => setPasswordForm((f) => ({ ...f, current_password: e.target.value }))}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="new_password">Nuova password</label>
            <input
              id="new_password"
              type="password"
              required
              autoComplete="new-password"
              className={inputClass}
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm((f) => ({ ...f, new_password: e.target.value }))}
            />
          </div>

          <div>
            <label className={labelClass} htmlFor="confirm_password">Conferma nuova password</label>
            <input
              id="confirm_password"
              type="password"
              required
              autoComplete="new-password"
              className={inputClass}
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm((f) => ({ ...f, confirm_password: e.target.value }))}
            />
          </div>

          {passwordSuccess && (
            <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-md px-4 py-3">
              {passwordSuccess}
            </div>
          )}
          {passwordError && (
            <div className="bg-red-50 border border-red-200 text-red-800 text-sm rounded-md px-4 py-3">
              {passwordError}
            </div>
          )}

          <div className="flex justify-end">
            <button type="submit" disabled={passwordLoading} className={btnPrimary}>
              {passwordLoading ? 'Aggiornamento...' : 'Cambia password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfilePage;
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ProfilePage.tsx
git commit -m "feat(frontend): add ProfilePage with profile update and password change"
```

---

## Task 7: Routing, AppLayout link, LoginPage banner

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/layouts/AppLayout.tsx`
- Modify: `frontend/src/pages/LoginPage.tsx`

- [ ] **Step 1: Add `/profilo` route in `App.tsx`**

Add the import:
```typescript
import ProfilePage from './pages/ProfilePage';
```

Inside the protected `<Route>` block (after the `/documenti` route):
```tsx
<Route path="/profilo" element={<ProfilePage />} />
```

- [ ] **Step 2: Add NavLink on username in `AppLayout.tsx`**

Add `NavLink` to the existing import from `react-router-dom`:
```typescript
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
// NavLink is already imported — just verify it's there
```

Find the `<span>` with `displayName` inside the user block:
```tsx
<span className="text-slate-300 text-sm truncate">{displayName}</span>
```

Replace with:
```tsx
<NavLink
  to="/profilo"
  className="text-slate-300 hover:text-white text-sm truncate underline-offset-2 hover:underline"
>
  {displayName}
</NavLink>
```

- [ ] **Step 3: Add post-email-change banner in `LoginPage.tsx`**

Add `useLocation` to the import:
```typescript
import { useNavigate, Navigate, useLocation } from 'react-router-dom';
```

Add these two lines at the TOP of the component body, before any other hooks or state declarations:
```typescript
const location = useLocation();
const successMessage = (location.state as { message?: string } | null)?.message;
```

In the JSX, place the banner inside the card div, after `<h2>` and before `<form>`:
```tsx
{successMessage && (
  <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-md px-4 py-3 text-center">
    {successMessage}
  </div>
)}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.tsx frontend/src/layouts/AppLayout.tsx frontend/src/pages/LoginPage.tsx
git commit -m "feat(frontend): add /profilo route, sidebar link, and post-email-change banner"
```

---

## Task 8: Final verification and push

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && python -m pytest tests/test_auth.py -v
```

Expected: all tests PASS.

- [ ] **Step 2: Start frontend dev server and verify manually**

```bash
cd frontend && npm run dev
```

Manual checks:
- Click the username in the sidebar → navigates to `/profilo`
- Profile form is pre-filled with current user data
- Role and registration date are shown as read-only text
- Save with nome change → success banner, sidebar name updates
- Save with email change → redirected to `/login` with green banner
- Password change with wrong current → "Password corrente non corretta"
- Password change with `new != confirm` → client-side error before request
- Password change success → green banner, fields cleared

- [ ] **Step 3: Git push**

```bash
git push origin main
```
