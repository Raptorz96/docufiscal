# DocuFiscal - Progress Fase 2

## Obiettivi Fase 2
Modelli dati completi, CRUD API, frontend pagine principali.

## Task Progress

### Task 1 ✅ — Modello Cliente
- SQLAlchemy model `Cliente` (nome, cognome, codice_fiscale, partita_iva, tipo, email, telefono)
- Schema Pydantic (ClienteCreate, ClienteUpdate, ClienteOut)
- Migrazione Alembic `create_clienti_table`

### Task 2 ✅ — Modello TipoContratto
- SQLAlchemy model `TipoContratto` (nome, descrizione, categoria)
- Schema Pydantic (TipoContrattoCreate, TipoContrattoUpdate, TipoContrattoOut)
- Migrazione Alembic `create_tipi_contratto_table`

### Task 3 ✅ — Modello Contratto
- SQLAlchemy model `Contratto` (cliente_id FK, tipo_contratto_id FK, data_inizio, data_fine, stato, note)
- Schema Pydantic (ContrattoCreate, ContrattoUpdate, ContrattoOut)
- Migrazione Alembic `create_contratti_table`

### Task 4 ✅ — API Clienti (CRUD)
- GET /clienti, POST /clienti, GET /clienti/{id}, PUT /clienti/{id}, DELETE /clienti/{id}
- Filtro per tipo (persona_fisica / azienda)
- Protezione JWT su tutti gli endpoint

### Task 5 ✅ — API TipiContratto (CRUD)
- GET /tipi-contratto, POST /tipi-contratto, GET /tipi-contratto/{id}, PUT /tipi-contratto/{id}, DELETE /tipi-contratto/{id}
- Filtro per categoria
- Protezione JWT

### Task 6 ✅ — API Contratti (CRUD)
- GET /contratti, POST /contratti, GET /contratti/{id}, PUT /contratti/{id}, DELETE /contratti/{id}
- Filtri per cliente_id, tipo_contratto_id, stato
- Protezione JWT

### Task 7 ✅ — Seed Script
- `backend/scripts/seed.py` idempotente
- 1 utente admin (admin@docufiscal.it / admin123)
- 6 TipiContratto: Dichiarazione Redditi, Contabilità Ordinaria, Contabilità Semplificata, Consulenza Fiscale, Gestione Payroll, Consulenza Societaria
- 8 Clienti: 4 persone fisiche + 4 aziende con dati italiani realistici
- 12 Contratti: stati misti (attivo/scaduto/sospeso), date realistiche 2023-2025
- Output colorato ANSI: ✅ creato / ⏭️ skip / ❌ errore
- Eseguibile con: `cd backend && python -m scripts.seed`

### Fix extra ✅ — Sidebar + Layout + bcrypt
- `src/layouts/AppLayout.tsx`: sidebar responsive (desktop fissa, mobile slide-in)
- NavLink con active state, icone SVG, user info + logout
- `src/pages/DashboardPage.tsx`: estratta da App.tsx
- `src/App.tsx`: nested routes con ProtectedRoute wrapping AppLayout
- Layout fullscreen fix: html/body/root height 100%
- `import type` fix per verbatimModuleSyntax in authService.ts
- `postcss.config.js` → `postcss.config.cjs` per compatibilità ESM
- `bcrypt==4.0.1` pinnato in requirements.txt (compatibilità passlib)

## Fase 2 COMPLETATA

## Convenzioni
- Backend: snake_case, type hints, docstrings, SQLAlchemy 2.0
- Frontend: camelCase, functional components, TypeScript strict, no any, import type per type-only
- Frontend hooks: useCallback per fetch, useRef per timer/flags/maps
- API: RESTful, /api/v1/, JSON, HTTPException
- Git: conventional commits
- Workflow: spec in chat → Claude Code implementa → code review → fix → push
