# DocuFiscal — CLAUDE.md

Piattaforma AI di gestione documentale e classificazione fiscale per commercialisti italiani.

## Stack

- **Frontend**: React 19 + TypeScript + Vite + TailwindCSS 3
- **Backend**: Python FastAPI + SQLAlchemy 2.0 + Alembic
- **Database**: PostgreSQL (prod), SQLite (dev)
- **AI**: Gemini 2.5 Flash (primario), Claude Haiku + OpenAI GPT-4o-mini (fallback)
- **Vector Search**: ChromaDB + sentence-transformers `all-MiniLM-L6-v2`
- **Deploy**: Docker Compose su VPS Ubuntu, Nginx reverse proxy + HTTPS

## Struttura progetto

```
docufiscal/
├── backend/
│   ├── app/
│   │   ├── ai/              # classificatori, prompts, vector store, deadline extractor
│   │   ├── api/             # endpoint FastAPI (auth, clienti, contratti, documenti, google, scadenze)
│   │   ├── core/            # config, security
│   │   ├── models/          # SQLAlchemy models
│   │   └── schemas/         # Pydantic schemas
│   ├── tests/               # pytest
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/      # componenti riutilizzabili
│       ├── layouts/         # AppLayout con sidebar
│       ├── pages/           # pagine principali
│       ├── hooks/           # custom hooks (useTheme, ecc.)
│       └── services/        # API client
├── docker-compose.yml
└── CLAUDE.md                # questo file
```

## Workflow di sviluppo

**NON implementare direttamente.** Segui sempre la spec ricevuta task per task.

1. Ricevi una spec con task numerati e comandi git inclusi
2. Implementa UN task alla volta nell'ordine dato
3. Esegui i test dopo ogni task: `cd backend && python -m pytest tests/ -v`
4. Committa con i comandi git esatti dalla spec (conventional commits)
5. Alla fine: `git push origin main`

## Comandi

```bash
# Test backend
cd backend && python -m pytest tests/ -v

# Test singolo file
cd backend && python -m pytest tests/test_auth.py -v

# Dev frontend
cd frontend && npm run dev

# Build frontend
cd frontend && npm run build
```

## Convenzioni codice

### Backend (Python)
- snake_case per variabili e funzioni
- Type hints ovunque
- Docstrings per funzioni pubbliche
- API RESTful versionate: `/api/v1/`
- Risposte JSON con schema consistente

### Frontend (TypeScript/React)
- camelCase per variabili, PascalCase per componenti
- Componenti funzionali con hooks
- `import type` per import solo-tipo (verbatimModuleSyntax)
- TailwindCSS per styling, NO CSS separati
- Dark mode: usa classi `dark:` di Tailwind (`darkMode: 'class'`)

### Git
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Committa ogni task separatamente, non fare commit cumulativi

## Errori noti — NON ripeterli

### `is not None` per metadata ChromaDB
ChromaDB `collection.update()` rimpiazza l'intero dict metadata. Usare `if value is not None` e MAI check truthy (`if value`) per campi nullable, altrimenti le chiavi vengono silenziosamente droppate.

### `anyio.to_thread.run_sync` per chiamate AI sync
Le chiamate sync ai classificatori AI (Gemini, Claude, OpenAI) dentro endpoint FastAPI async DEVONO essere wrappate con `anyio.to_thread.run_sync()`. Non bloccare mai l'event loop.

### Confidence threshold > 0.3
Per deadline extraction usare `confidence > 0.3`, NON `confidence > 0`. Valori troppo bassi producono scadenze spazzatura.

### Docker: `restart: always`
Ogni servizio in `docker-compose.yml` DEVE avere `restart: always` o i container non sopravvivono ai reboot del server.

### Named volumes Docker
Lo storage file DEVE usare named volumes (`backend_storage:/app/storage`). Senza, i file uploadati vengono persi ad ogni redeploy.

### `.env` mai in git
I file `.env` sono in `.gitignore`. Se per errore vengono committati, rimuoverli con `git rm --cached .env` e poi purge dalla history con `git filter-repo`.

### Upload MAI bloccanti
La classificazione AI e l'estrazione deadline sono best-effort. Se l'AI fallisce, il documento viene comunque salvato con valori di default. MAI lanciare eccezioni che bloccano l'upload.

### Import Alembic
In `alembic/env.py` il modello si chiama `Scadenza` (NON `ScadenzaContratto` — è stato rinominato).

## Architettura AI

### Pipeline classificazione documenti
1. Upload → estrazione testo (PyPDF2 / pytesseract OCR)
2. Routing: Short ID → Regex CF/PIVA → LLM classifier
3. Classificatore multi-provider con fallback chain: Gemini → Claude → OpenAI
4. Risultato: `tipo_documento`, `macro_categoria`, `anno_competenza`, `confidence`, `cliente_suggerito`
5. Se `confidence > soglia` → archiviazione automatica

### Pipeline scadenze (dual-phase)
1. **Upload documento**: `deadline_extractor.py` estrae scadenze generiche
2. **Se è contratto**: `contract_extractor.py` estrae dati contrattuali (date, canone, clausole)
3. Record salvati in tabella `scadenze` con `tipo_scadenza` (pagamento, incasso, canone, adempimento, rinnovo, generico)

### RAG Chatbot
- ChromaDB collection `documenti_rag` con chunking
- Keyword detection per scadenze → iniezione dati strutturati nel prompt
- Citazioni per nome documento (NO placeholder `[ID: X]`)
- Google Calendar action support se OAuth2 connesso

## Test

**69 test backend attualmente passanti.** Questo numero è il sanity check di salute del progetto.

Dopo ogni modifica: `python -m pytest tests/ -v` — tutti e 69 devono passare.

Test suites: auth (18), clienti (11), contratti (11), tipi_contratto (8), classificazione (6), vector_store (3), routing_regex (3), altri.

## File sul server (NON nel repo)

Questi file sono gestiti manualmente sul server e NON sono versionati:
- `/opt/docufiscal/.env` — variabili ambiente backend (DB, API keys, JWT secret)
- `/opt/docufiscal/frontend/.env.production` — `VITE_API_BASE_URL`
- Nginx config nel container `nextgen-itsm-nginx`

## Note importanti

- `docker compose restart` NON ricarica variabili `.env` — serve `down` + `up`
- Google OAuth2 redirect URI: `https://itsm.maftei.it/api/v1/google/callback` (aggiornare se si migra)
- `Europe/Rome` è hardcoded in `google_calendar.py`
- OAuth `_pending_states` è in-memory: se il container restarta tra authorize e callback, lo state si perde
