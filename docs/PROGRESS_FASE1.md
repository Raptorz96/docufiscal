# DocuFiscal - Progresso Fase 1

## Stato: In corso

## Task completati

### Task 1 ✅ — Inizializzazione Frontend
- Vite + React + TypeScript
- TailwindCSS v3.4.19 + PostCSS + Autoprefixer
- react-router-dom + axios
- Path alias `@/` configurato in `vite.config.ts` e `tsconfig.app.json`
- Struttura cartelle: components/, pages/, hooks/, services/, utils/, context/, types/

### Task 2 ✅ — Inizializzazione Backend
- FastAPI app con titolo "DocuFiscal API" v0.1.0
- CORS middleware (origin: http://localhost:5173)
- Health check: GET /api/v1/health → {"status": "ok"}
- Struttura cartelle: api/, models/, schemas/, services/, ai/, storage/, core/ (tutti con __init__.py)
- requirements.txt con tutte le dipendenze
- .env.example con variabili ambiente

### Task 3 ✅ — Configurazione Core Backend
- backend/app/core/config.py con classe Settings (pydantic_settings.BaseSettings)
- Campi: DATABASE_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, CLAUDE_API_KEY
- model_config con env_file = ".env"
- Singleton settings esportato da __init__.py

### Task 4 ✅ — Setup Database
- backend/app/core/database.py con SQLAlchemy 2.0
- Engine con check SQLite (connect_args)
- SessionLocal, Base (DeclarativeBase), get_db dependency
- Esportati da core/__init__.py

### Task 5 ✅ — Setup Alembic
- alembic init con env.py configurato
- URL da settings (non hardcoded in alembic.ini)
- target_metadata = Base.metadata

### Task 6 ✅ — Modello Utente
- backend/app/models/user.py con User(Base)
- Campi: id, email (unique, indexed), hashed_password, nome, cognome, role, is_active, created_at, updated_at
- SQLAlchemy 2.0 style (Mapped + mapped_column)
- Migrazione Alembic auto-generata (revision orahb0yfvx9a)
- server_default per role, is_active, timestamps

### Task 7 ✅ — Auth Backend
- backend/app/core/security.py: hash_password, verify_password, create_access_token (JWT)
- backend/app/schemas/user.py: UserCreate, UserLogin, UserResponse, Token
- backend/app/api/deps.py: get_current_user (OAuth2 + JWT decode)
- backend/app/api/auth.py: POST /register (409 duplicati), POST /login (OAuth2PasswordRequestForm), GET /me (protetto)
- Router registrato in main.py su /api/v1/auth/*
- Testato su /docs: register → login → /me funzionante

## Task rimanenti Fase 1

### Task 8 — Auth Frontend
- Pagina login, context auth, protezione route

### Task 9 — Docker-compose
- PostgreSQL per chi vuole usarlo

### Task 10 — README + .gitignore

## Fix applicati
- Downgrade TailwindCSS da v4 a v3 (la v4 ha config incompatibile)
- .gitignore corretto (era su una riga sola causa PowerShell echo)
- Aggiornato declarative_base() → DeclarativeBase (SQLAlchemy 2.0)
- Rimossi import non usati da alembic/env.py
- datetime.utcnow() → datetime.now(timezone.utc) in security.py
- Aggiunto email-validator a requirements.txt
- Creato venv dedicato (conflitto Anaconda/Python 3.10)

## Repo GitHub
- https://github.com/Raptorz96/docufiscal
- Branch: main
