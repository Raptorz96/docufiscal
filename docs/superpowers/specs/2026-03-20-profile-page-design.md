# Design Spec — Pagina Profilo Utente + Cambio Password

**Data:** 2026-03-20
**Stato:** Approvato (rev 2)

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
from pydantic import field_validator

class UserUpdate(BaseModel):
    nome: str | None = None
    cognome: str | None = None
    email: EmailStr | None = None

    @field_validator('nome', 'cognome')
    @classmethod
    def not_empty(cls, v):
        if v is not None and v.strip() == '':
            raise ValueError('Il campo non può essere vuoto')
        return v
```

I campi `nome` e `cognome` accettano `None` (non aggiornare) ma non stringhe vuote. Questo evita scritture di stringhe vuote su colonne `nullable=False`.

#### Schema `PasswordChange`

```python
class PasswordChange(BaseModel):
    current_password: str
    new_password: str
```

La validazione della lunghezza minima di `new_password` (≥ 8 caratteri) è gestita esplicitamente nel route handler con `HTTPException(400)` — coerente con la specifica frontend che gestisce errori 400.

#### `PATCH /auth/me`

- Autenticazione richiesta (`get_current_user`)
- Se nessun campo è non-None, ritorna `UserResponse` senza scrivere nel DB (no-op)
- Applica solo i campi non-None all'oggetto ORM
- Se `email` cambia: verifica che non sia già usata da altro utente → 409 se duplicata
- Dopo commit: chiama `db.refresh(db_user)` per ottenere dati aggiornati (incluso `updated_at`)
- Ritorna `UserResponse`

**Nota token:** Il token JWT usa `sub: email`. Se l'email cambia, il token attuale diventa immediatamente invalido perché `get_current_user` in `deps.py` cerca l'utente per email nel DB. Il frontend gestisce questo scenario senza fare request autenticate successive (vedi sezione frontend).

#### `POST /auth/change-password`

- Autenticazione richiesta (`get_current_user`)
- Verifica `current_password` contro hash in DB → 400 "Password corrente non corretta" se errata
- Controlla manualmente `len(new_password) < 8` → 400 "La password deve essere di almeno 8 caratteri"
- Salva nuovo hash + `db.commit()` + `db.refresh()`
- Ritorna `{"detail": "Password aggiornata con successo"}`
- Il token corrente rimane valido (nessun token blacklist)

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

Aggiornare la riga di import esistente aggiungendo `ProfileUpdate` e `PasswordChangeRequest`:
```ts
import type { LoginCredentials, AuthResponse, User, ProfileUpdate, PasswordChangeRequest } from '../types/auth';
```

Aggiungere i due export:
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

Tipo aggiornato:
```ts
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}
```

Implementazione da aggiungere nel provider:
```ts
const refreshUser = async (): Promise<void> => {
  const userData = await authService.getMe();
  setUser(userData);
};
```

Aggiungere `refreshUser` all'oggetto `value`.

#### `ProfilePage.tsx`

Layout: card centrata (`max-w-2xl mx-auto p-6`), sfondo `bg-gray-50`, due sezioni separate con bordo.

**Sezione 1 — Dati Profilo:**
- Input controllati: nome, cognome, email — precompilati da `useAuth().user` nell'`useEffect` iniziale
- Info non modificabili mostrate come testo: ruolo, data registrazione (formattata in italiano)
- Submit button disabilitato e con spinner durante la request
- **Gestione cambio email (critico):**
  - Prima di chiamare `updateProfile()`, calcolare `const emailChanged = formData.email !== user.email`
  - Questo confronto avviene PRIMA di qualsiasi request autenticata
  - Su successo dal PATCH:
    - Se `emailChanged`: chiamare `logout()` (rimuove token da localStorage) + `navigate('/login', { state: { message: 'Email aggiornata. Effettua nuovamente il login.' } })` — NON chiamare `refreshUser()` perché il token è ora invalido e causerebbe un 401 intercettato dal global interceptor che farebbe `window.location.href = '/login'` perdendo lo state del messaggio
    - Se non `emailChanged`: chiamare `refreshUser()` + mostrare banner verde "Profilo aggiornato"
- Errore 409 → "Email già in uso da un altro account"
- Errori generici (network, 500) → "Errore imprevisto. Riprova."

**Sezione 2 — Cambio Password:**
- Input: password corrente, nuova password, conferma nuova password
- Validazione client-side PRIMA della request:
  - nuova password < 8 caratteri → "La password deve essere di almeno 8 caratteri"
  - conferma ≠ nuova → "Le password non corrispondono"
- Submit button disabilitato e con spinner durante la request
- Su successo: banner verde "Password aggiornata con successo" + reset dei 3 campi password
- Errore 400 → mostrare il `detail` ricevuto dal backend
- Errori generici → "Errore imprevisto. Riprova."

#### Routing

In `App.tsx`, dentro il blocco `ProtectedRoute`:
```tsx
<Route path="/profilo" element={<ProfilePage />} />
```

#### Link profilo in sidebar (`AppLayout.tsx`)

Il blocco utente in fondo alla sidebar (sezione "User + Logout") mantiene la struttura. Il `<span>` con `displayName` dentro il `div` con classe `flex items-center gap-3 px-4 py-2 mb-2` diventa un `<NavLink to="/profilo">` con classe `text-slate-300 hover:text-white underline-offset-2 hover:underline text-sm truncate` — senza `flex` o `px`/`py` aggiuntivi, perché il padding è già fornito dal `div` wrapper.

#### Banner post-cambio email in `LoginPage.tsx`

Aggiungere all'inizio del componente (dopo gli `useState`, prima dei check di autenticazione):
```tsx
const location = useLocation();
const successMessage = location.state?.message as string | undefined;
```

Nel JSX, sopra il `<form>` e dopo l'`<h2>`:
```tsx
{successMessage && (
  <div className="bg-green-50 border border-green-200 text-green-800 text-sm rounded-md px-4 py-3">
    {successMessage}
  </div>
)}
```

Il componente già controlla `isAuthenticated` a riga 14 con early return — il banner viene renderizzato solo se l'utente non è autenticato (che è il caso dopo logout da cambio email). L'`useLocation` deve essere chiamato prima di qualsiasi early return per rispettare le regole degli hook React.

---

## Flussi principali

### Aggiornamento profilo (senza cambio email)
1. Utente modifica nome/cognome → Salva Modifiche
2. `emailChanged = false` (calcolato prima della request)
3. `PATCH /auth/me` → 200 con `UserResponse`
4. `refreshUser()` → `getMe()` → `setUser(...)` → banner verde

### Aggiornamento email
1. Utente modifica email → Salva Modifiche
2. `emailChanged = true` (calcolato prima della request)
3. `PATCH /auth/me` → 200 con `UserResponse`
4. `logout()` (rimuove token) + `navigate('/login', { state: { message: '...' } })`
5. Nessuna request autenticata successiva — il 401 interceptor non si attiva
6. `LoginPage` legge `location.state.message` e mostra banner verde

### Cambio password
1. Utente compila i 3 campi → Cambia Password
2. Validazione client → `POST /auth/change-password`
3. Successo: banner verde + reset campi password
4. Errore 400: mostra `detail` dal backend

---

## Vincoli & Note

- TailwindCSS v3, nessuna libreria UI aggiuntiva
- Nessun token blacklist per cambio password
- `email` nel token (`sub`) → cambio email invalida il token immediatamente
- Il frontend non deve mai effettuare request autenticate dopo un cambio email — gestire sempre il branch `emailChanged` chiamando `logout()` prima di qualsiasi altra operazione
- `db.refresh()` sempre dopo `db.commit()` per restituire dati aggiornati incluso `updated_at`
- Submit button sempre disabilitato durante le request per prevenire doppio invio
