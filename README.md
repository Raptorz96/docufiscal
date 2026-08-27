# DocuFiscal

DocuFiscal è un'applicazione per studi professionali e commercialisti che centralizza clienti, contratti, documenti e scadenze. Integra classificazione documentale tramite AI, estrazione delle scadenze, ricerca semantica e consultazione RAG con riferimenti ai documenti.

## Funzionalità principali

- Gestione di clienti, tipi di contratto e contratti.
- Upload, classificazione AI e associazione dei documenti.
- Gestione dei documenti non ancora assegnati a un cliente.
- Estrazione e consultazione delle scadenze documentali e contrattuali.
- Ricerca semantica globale tramite Omnibox.
- Chatbot RAG con riferimenti ai documenti.
- Anteprima PDF tramite drawer.
- Eliminazione bulk di documenti e contratti.
- Autenticazione JWT e gestione del profilo.
- Integrazione opzionale con Google Calendar.
- Interfaccia responsive con dark mode.

## Stack

- **Frontend:** React 19, TypeScript, Vite e Tailwind CSS.
- **Backend:** FastAPI, SQLAlchemy 2.x e Alembic.
- **Database:** SQLite in locale, PostgreSQL con Docker Compose.
- **Storage:** filesystem persistente.
- **AI:** provider configurabile, con Gemini come default corrente.
- **RAG:** ChromaDB ed embedding `all-MiniLM-L6-v2`.
- **Integrazioni:** Google Calendar OAuth2.

## Requisiti locali

- Node.js `22.22.2`, versione canonica definita in `.nvmrc`.
- Python 3.11+.
- NVM consigliato.
- Docker e Docker Compose opzionali.

Il progetto non fissa attualmente una versione npm tramite `packageManager` o `engines`. La baseline verificata ha usato npm `10.9.7`.

Per selezionare Node e verificare le versioni:

```bash
nvm use
node -v
npm -v
```

## Avvio locale

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Su Windows, il comando di attivazione dell'ambiente virtuale è:

```bash
.venv\Scripts\activate
```

Il backend è disponibile su `http://localhost:8000`; la documentazione OpenAPI è disponibile su `http://localhost:8000/docs`.

### Frontend

In un secondo terminale, dalla root del repository:

```bash
nvm use
cd frontend
npm ci
npm run dev
```

Il frontend è disponibile su `http://localhost:5173`.

### Primo accesso

Se il database non contiene utenti:

1. aprire `http://localhost:8000/docs`;
2. usare `POST /api/v1/auth/register`;
3. accedere dal frontend con le credenziali create.

## Avvio con Docker

```bash
cp .env.example .env
docker compose up --build
```

Il file `.env.example` nella root è una base storica per Docker Compose e deve essere revisionato prima dell'uso, perché non rappresenta tutta la configurazione AI corrente.

## Configurazione

- `.env.example` nella root è la base storica usata per Docker Compose, ma è attualmente incompleto rispetto alla configurazione AI.
- `backend/.env.example` è la base per il backend locale.
- Entrambi i file example devono essere revisionati prima dell'uso.
- Le credenziali reali non devono essere versionate.

Gemini è il provider AI predefinito. `AI_PROVIDER` seleziona un singolo provider e non esiste una fallback chain automatica Gemini → Claude → OpenAI.

## Verifiche

Backend:

```bash
cd backend
python -m pytest
```

Frontend:

```bash
nvm use
cd frontend
npm run lint
npm run build
```

Baseline verificata durante la migrazione:

- backend: 80/80 test passing;
- frontend lint: 0 errori / 0 warning;
- frontend build: PASS;
- npm usato nella baseline: `10.9.7`.

Questi valori descrivono la baseline verificata, non requisiti permanenti del progetto.

## Documentazione

- [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — contesto tecnico canonico.
- [`docs/ROADMAP_V2.md`](docs/ROADMAP_V2.md) — backlog ed evoluzioni candidate, non fonte dello stato corrente.

In caso di divergenza documentale prevalgono la codebase e i test, quindi `docs/PROJECT_CONTEXT.md`.
