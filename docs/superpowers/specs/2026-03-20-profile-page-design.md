# Design Spec — Pagina Profilo Utente + Cambio Password

**Data:** 2026-03-20
**Stato:** Approvato

---

## Obiettivo

Permettere all'utente autenticato di visualizzare e aggiornare i propri dati (nome, cognome, email) e cambiare la password, tramite una pagina profilo accessibile dalla sidebar.

---

## Architettura

### Backend

**File modificati:**
- `backend/app/schemas/user.py` — nuovi schema `UserUpdate`, `PasswordChange`
- `backend/app/api/auth.py` — nuovi endpoint `PATCH /auth/me` e `POST /auth/change-password`

#### Schema `UserUpdate`
```python
class UserUpdate(BaseModel):
    nome: str | None = None
    cognome: str | None = None
    email: EmailStr | None = None
```

#### Schema `PasswordChange`
```python
class PasswordChange(BaseModel):
    current_password: str
    new_password: str
```

#### `PATCH /auth/me`
- Autenticazione richiesta (`get_current_user`)
- Applica solo i campi non-None
- Se `email` cambia: verifica che non sia già usata da altro utente → 409 se duplicata
- Ritorna `UserResponse`
- **Nota token:** Il token JWT usa `sub: email`. Se l'email cambia, il token attuale diventa immediatamente invalido (il prossimo request fallirà). Il frontend gestisce questo con logout + redirect.

#### `POST /auth/change-password`
- Autenticazione richiesta (`get_current_user`)
- Verifica `current_password` contro hash in DB → 400 "Password corrente non corretta" se errata
- Valida `new_password` min 8 caratteri → 400 se troppo corta
- Salva nuovo hash
- Ritorna `{"detail": "Password aggiornata con successo"}`
- Il token corrente rimane valido (nessun blacklist)

---

### Frontend

**File modificati/creati:**
- `frontend/src/types/auth.ts` — aggiunta `created_at`, `ProfileUpdate`, `PasswordChangeRequest`
- `frontend/src/services/authService.ts` — aggiunta `updateProfile()`, `changePassword()`
- `frontend/src/context/AuthContext.tsx` — aggiunta `refreshUser()`
- `frontend/src/pages/ProfilePage.tsx` — nuova pagina (creata)
- `frontend/src/App.tsx` — nuova rotta `/profilo`
- `frontend/src/layouts/AppLayout.tsx` — link al profilo sul nome utente

#### `types/auth.ts`

Aggiunge `created_at: string` a `User`:
```ts
export interface User {
  id: number;
  email: string;
  nome: string;
  cognome: string;
  role: string;
  is_active: boolean;
  created_at: string;
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

#### `authService.ts`
```ts
export const updateProfile = async (data: ProfileUpdate): Promise<User> => {
  const response = await api.patch<User>('/auth/me', data);
  return response.data;
};

export const changePassword = async (data: PasswordChangeRequest): Promise<void> => {
  await api.post('/auth/change-password', data);
};
```

#### `AuthContext.tsx`

Aggiunge `refreshUser` al type e al value:
```ts
const refreshUser = async (): Promise<void> => {
  const userData = await authService.getMe();
  setUser(userData);
};
```

#### `ProfilePage.tsx`

Layout: card centrata (`max-w-2xl mx-auto`), stile coerente con il resto (Tailwind, sfondo `gray-50`).

**Sezione 1 — Dati Profilo:**
- Input: nome, cognome, email (precompilati da `useAuth().user`)
- Info non modificabili come testo: ruolo, data registrazione
- Submit → `updateProfile()` → se email cambiata: `logout()` + `navigate('/login', { state: { message: '...' } })`, altrimenti `refreshUser()` + messaggio verde

**Sezione 2 — Cambio Password:**
- Input: password corrente, nuova password, conferma nuova password
- Validazione client: nuova ≥ 8 char, conferma deve corrispondere
- Submit → `changePassword()` → messaggio verde + reset campi
- Errore 400 → mostra `detail` dal backend

#### Routing

In `App.tsx`, dentro il blocco `ProtectedRoute`:
```tsx
<Route path="/profilo" element={<ProfilePage />} />
```

#### Link profilo in sidebar (`AppLayout.tsx`)

Il `<span>` con `displayName` (riga 108) diventa `<NavLink to="/profilo">` con stile coerente con `inactiveLinkClass`.

#### Gestione messaggio post-cambio email

`LoginPage.tsx` legge `location.state?.message` (via `useLocation`) e lo mostra come banner verde sopra il form.

---

## Flussi principali

### Aggiornamento profilo (senza cambio email)
1. Utente modifica nome/cognome → Salva Modifiche
2. `PATCH /auth/me` → 200 con `UserResponse`
3. `refreshUser()` → `getMe()` → `setUser(...)` → messaggio verde

### Aggiornamento email
1. Utente modifica email → Salva Modifiche
2. `PATCH /auth/me` → 200 con `UserResponse`
3. Frontend: `logout()` (rimuove token) + `navigate('/login', { state: { message: 'Email aggiornata, effettua nuovamente il login' } })`
4. `LoginPage` mostra il messaggio in verde

### Cambio password
1. Utente compila i 3 campi → Cambia Password
2. Validazione client → `POST /auth/change-password`
3. Successo: messaggio verde + reset campi
4. Errore 400: mostra messaggio dal backend

---

## Vincoli & Note

- TailwindCSS v3, nessuna libreria UI aggiuntiva
- Nessun token blacklist per cambio password
- `email` nel token (`sub`) → cambio email invalida il token immediatamente
- Cambio email causa logout obbligatorio per coerenza con la sessione
