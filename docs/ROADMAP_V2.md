# DocuFiscal - ROADMAP V2.0

Fonte di verità per lo stato di sviluppo e la pianificazione futura del progetto.

---

## Stack Tecnologico

- **Frontend**: React (Vite) + TailwindCSS + TypeScript
- **Backend**: Python FastAPI + SQLAlchemy 2.0
- **Database**: SQLite (sviluppo) / PostgreSQL (produzione)
- **AI Classification**: Gemini 2.5 Flash (primario) | Claude Haiku (fallback) | OpenAI GPT-4o-mini
- **Vector Search / RAG**: ChromaDB + `all-MiniLM-L6-v2` (sentence-transformers)
- **Storage**: File system locale (v1)
- **Auth**: JWT-based

---

## Architettura AI Pipeline (Upload Flow)

```
Upload documento
      │
      ▼
[Livello 1] Short ID deterministico (#ID_ nel nome file)
      │ match → assegna cliente
      ▼
[Livello 2] Regex CF/PIVA (prime 2 pagine PDF)
      │ match → assegna cliente
      ▼
[Livello 3] LLM Classifier (Gemini/Claude/OpenAI)
      │ → tipo_documento, macro_categoria, anno_competenza, confidence
      ▼
[Post-upload] Indicizzazione VectorStore (ChromaDB + sentence-transformers)
      │ → abilitazione RAG chatbot e ricerca semantica
```

---

## Stato Attuale

### Fasi 1–4: Core Backend & AI Classification ✅

- **Auth**: JWT, register/login, protezione endpoint
- **Anagrafica**: CRUD Clienti, TipiContratto, Contratti
- **Storage**: upload/download documenti (PDF, immagini, DOCX, XLSX), path traversal protection
- **AI Classification**:
  - `TextExtractionService`: PyPDF2 + OCR (pytesseract) + PyMuPDF
  - Classifiers: `GeminiClassifier`, `ClaudeClassifier`, `OpenAIClassifier`
  - Factory `get_classifier()` via `.env` (AI_PROVIDER)
  - Prompt condiviso in `prompts.py` (zero duplicazione)
  - Confidence threshold (default 0.75), Human-in-the-loop: Conferma / Correggi
  - Output esteso: `tipo_documento`, `macro_categoria`, `anno_competenza`, `codice_fiscale`, `partita_iva`
- **Routing Intelligente**:
  - Short ID (`#ID_NNN` nel filename) → match deterministico
  - `RegexRouter`: estrae CF/PIVA dal testo e cerca in DB prima dell'LLM
  - Fallback auto-matching LLM con normalizzazione CF/PIVA
- **Modello Documento**: `short_id`, `macro_categoria`, `anno_competenza`, `verificato_da_utente`, `confidence_score`

### Fase 5: Dashboard & UX ✅

- `DashboardPage` con KPI: doc totali, clienti, doc non verificati, scadenze imminenti
- Scadenziario contratti con alert visivi
- Sidebar responsive (desktop fissa / mobile slide-in), menu con active state
- Filtri istantanei sui documenti (cliente, tipo, contratto)
- Badge AI colorati per stato classificazione (verificato / alta confidence / bassa confidence)
- PDF Drawer split-screen per visualizzazione inline

### Fase 6: Vector Search & RAG Chatbot ✅

- **VectorStore** (`vector_store.py`): ChromaDB persistente + `all-MiniLM-L6-v2`
  - `add_document()` async con metadata (cliente_id, macro_categoria, anno_competenza, file_name)
  - `search_documents()` con filtri metadata e similarità vettoriale
- **Embeddings legacy** (`embeddings.py`): ChromaDB + Gemini embedding-001 (collezione separata `documenti`)
- **Ricerca Semantica**: `GET /api/v1/search/semantic?q=...` → risultati ordinati per score
- **RAG Chatbot**:
  - `POST /api/v1/chat/query` → context retrieval + LLM (Gemini/OpenAI)
  - Multi-turn conversation con history
  - Citation extraction con link cliccabili ai documenti
  - `DocumentChatbot.tsx`: widget FAB floating, ReactMarkdown, apertura PDF dal riferimento
  - `DocumentContext` per navigazione documento da chatbot
- **OpenAI Provider**: `OpenAIClassifier` con sync/async, `json_object` response format

### Convenzioni Codice

- **Backend**: snake_case, type hints, docstrings, SQLAlchemy 2.0
- **Frontend**: camelCase, functional components, TypeScript strict, `import type` per type-only
- **Hooks**: `useCallback` per fetch, `useRef` per timer/flags/maps
- **Utils**: moduli condivisi in `utils/` per labels, formatters
- **API**: RESTful, `/api/v1/`, JSON, HTTPException, JWT protection
- **Git**: conventional commits

---

## Gap Analysis — Cosa Manca

1. **Duplicazione VectorStore**: `embeddings.py` (Gemini embeddings, collezione `documenti`) e `vector_store.py` (sentence-transformers, collezione `documenti_rag`) coesistono — da consolidare
2. **Ingestione Multicanale**: nessun bot Telegram/WhatsApp
3. **Upload Asincrono**: upload sincrono (2-5s accettabile per v1, ma bottleneck per batch)
4. **Google Calendar**: integrazione assente
5. **Re-indicizzazione Automatica**: script manuali (`reindex_all.py`), non automatica
6. **Omnibox Frontend**: nessuna search bar globale integrata nel layout
7. **Test Coverage**: test unitari limitati (solo classificazione); mancano test per routing, vector store, chat

---

## Pianificazione Futura

### Fase 7: Consolidamento & Qualità (Prossima)

- **Task 7.1** — Unifica VectorStore: rimuovi `embeddings.py` legacy, migra `search.py` su `vector_store.py`
- **Task 7.2** — Test Coverage: pytest per routing regex, vector store, chat endpoint
- **Task 7.3** — Omnibox Frontend: search bar globale nel layout (AppLayout) con query semantica
- **Task 7.4** — Re-indicizzazione automatica on-upload: assicura che ogni documento sia indicizzato post-classificazione

### Fase 8: Ingestione Mobile & Background Tasks

- **Task 8.1** — Webhook Telegram per ricezione file da mobile
- **Task 8.2** — Coda asincrona upload (FastAPI BackgroundTasks o Celery) per batch massivi
- **Task 8.3** — Auth via numero telefono (operatori Studio)

### Fase 9: Automazione Scadenze & API Esterne

- **Task 9.1** — Estrazione AI proattiva scadenze dai documenti (F24, contratti)
- **Task 9.2** — Integrazione Google Calendar API per sync scadenze
- **Task 9.3** — Notifiche push/email per scadenze imminenti

### Fase 10: Deploy & Produzione

- **Task 10.1** — Docker Compose (FastAPI + PostgreSQL + frontend build)
- **Task 10.2** — Migrazione storage S3-compatible (MinIO o AWS S3)
- **Task 10.3** — CI/CD pipeline (GitHub Actions)
- **Task 10.4** — Variabili ambiente production-grade, HTTPS, rate limiting

---

## Struttura Modulo AI

```
backend/app/ai/
├── __init__.py              # Export: text_extraction_service, get_classifier, extract_short_id
├── text_extraction.py       # TextExtractionService (PDF + OCR + PyMuPDF)
├── classifier.py            # BaseClassifier ABC, ClassificationResult, get_classifier factory
├── prompts.py               # Prompt condivisi: build_classification_prompt, build_rag_chat_prompt
├── gemini_classifier.py     # GeminiClassifier con structured JSON output
├── claude_classifier.py     # ClaudeClassifier con JSON-only system prompt
├── openai_classifier.py     # OpenAIClassifier sync/async
├── routing.py               # RegexRouter: CF/PIVA extraction per auto-matching
├── vector_store.py          # VectorStore (ChromaDB + sentence-transformers) — RAG
└── embeddings.py            # Legacy: Gemini embeddings (da consolidare in Fase 7)
```
