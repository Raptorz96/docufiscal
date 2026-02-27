# DocuFiscal

Dashboard per commercialisti con classificazione automatica dei documenti tramite intelligenza artificiale.

## Stack Tecnologico

- **Frontend**: React + TypeScript + Vite + TailwindCSS
- **Backend**: FastAPI + SQLAlchemy + Alembic
- **Database**: SQLite (sviluppo) / PostgreSQL (Docker)
- **AI**: Claude API per classificazione documenti
- **Autenticazione**: JWT con OAuth2

## Prerequisiti

- Node.js 20.19+ o 22.12+
- Python 3.11+
- Docker (opzionale)

## Setup Locale (senza Docker)

### 1. Clonare il repository
```bash
git clone <repository-url>
cd DocuFiscal
```

### 2. Backend
```bash
cd backend

# Creare ambiente virtuale
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate     # Windows

# Installare dipendenze
pip install -r requirements.txt

# Configurare variabili ambiente
cp .env.example .env
# Modificare .env con le proprie configurazioni

# Eseguire migrazioni database
alembic upgrade head

# Avviare server
uvicorn app.main:app --reload
```
Backend disponibile su: http://localhost:8000

### 3. Frontend
```bash
cd frontend

# Installare dipendenze
npm install

# Avviare server sviluppo
npm run dev
```
Frontend disponibile su: http://localhost:5173

### 4. Primo utente
1. Aprire http://localhost:8000/docs (Swagger UI)
2. Usare endpoint `POST /api/v1/auth/register` per creare il primo utente
3. Accedere al frontend con le credenziali create

## Setup Docker (opzionale)

```bash
# Configurare variabili ambiente
cp .env.example .env
# Modificare DATABASE_URL per PostgreSQL:
# DATABASE_URL=postgresql://docufiscal:docufiscal@db:5432/docufiscal

# Avviare stack completo
docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Database: PostgreSQL su porta 5432

## Struttura Progetto

```
DocuFiscal/
├── backend/
│   ├── app/
│   │   ├── api/           # Endpoints REST
│   │   ├── core/          # Config, security, database
│   │   ├── models/        # Modelli SQLAlchemy
│   │   └── schemas/       # Schemi Pydantic
│   ├── alembic/           # Migrazioni database
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # Componenti React
│   │   ├── pages/         # Pagine applicazione
│   │   ├── services/      # API client
│   │   ├── context/       # Context providers
│   │   └── types/         # Tipi TypeScript
│   └── package.json
└── docker-compose.yml
```

## Stato Sviluppo

✅ **Fase 1 - Setup e Autenticazione**
- Configurazione progetti frontend e backend
- Sistema autenticazione JWT completo
- Setup Docker con PostgreSQL
- Dashboard base con protezione route

🚧 **Prossime fasi**
- Upload e gestione documenti
- Integrazione Claude API per classificazione
- Dashboard analytics per commercialisti

## Endpoints API

- `POST /api/v1/auth/register` - Registrazione utente
- `POST /api/v1/auth/login` - Login utente
- `GET /api/v1/auth/me` - Profilo utente corrente
- `GET /api/v1/health` - Health check

Documentazione completa: http://localhost:8000/docs
