# DocuFiscal - Dashboard Commercialisti

## Panoramica
Dashboard web per commercialisti che gestisce profili clienti, tipologie contrattuali e archiviazione automatica dei documenti tramite classificazione AI (Claude API).

## Stack Tecnologico
- **Frontend**: React (Vite) + TailwindCSS
- **Backend**: Python FastAPI
- **Database**: PostgreSQL (produzione) / SQLite (sviluppo)
- **AI**: Claude API (Sonnet) per classificazione documenti
- **Storage**: File system locale (v1), S3-compatible (v2)
- **Auth**: JWT-based

## Architettura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React UI  │────▶│   FastAPI    │────▶│  PostgreSQL  │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Claude API  │
                    │ (classificaz)│
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   Storage    │
                    │  documenti   │
                    └─────────────┘
```

## Struttura Cartelle

```
docufiscal/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/    # chiamate API
│   │   └── utils/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/         # routes
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # business logic
│   │   ├── ai/          # classificazione Claude
│   │   └── storage/     # gestione file
│   ├── alembic/         # migrazioni DB
│   └── requirements.txt
└── docs/
```

## Modello Dati (Core)

### Cliente
- id, nome, cognome, codice_fiscale, partita_iva
- tipo (persona_fisica | azienda)
- email, telefono
- data_creazione

### TipoContratto
- id, nome, descrizione
- categoria (fiscale | previdenziale | societario | lavoro | altro)

### Contratto
- id, cliente_id, tipo_contratto_id
- data_inizio, data_fine
- stato (attivo | scaduto | sospeso)

### Documento
- id, cliente_id, contratto_id (nullable)
- tipo_documento (da definire le categorie)
- file_path, file_name, file_size
- classificazione_ai (JSON con output Claude)
- confidence_score
- verificato_da_utente (bool)
- data_upload

## Flusso Classificazione AI

1. Commercialista uploada documento (PDF/immagine)
2. Backend estrae testo (PyPDF2 / OCR con pytesseract)
3. Testo inviato a Claude API con prompt di classificazione
4. Claude ritorna: tipo_documento, cliente_suggerito, contratto_suggerito, confidence
5. Se confidence > soglia → archiviazione automatica
6. Se confidence < soglia → richiesta conferma manuale al commercialista

## Piano di Lavoro

### Fase 1 - Setup & Fondamenta
- Inizializzazione progetto (Vite + FastAPI)
- Setup database e modelli base
- Auth base (login commercialista)

### Fase 2 - CRUD Clienti & Contratti
- Gestione profili clienti
- Gestione tipologie contratto
- Associazione clienti-contratti

### Fase 3 - Upload & Storage Documenti
- Sistema upload file
- Storage organizzato per cliente/contratto
- Visualizzazione documenti caricati

### Fase 4 - Classificazione AI
- Integrazione Claude API
- Estrazione testo da PDF
- Prompt engineering per classificazione
- Logica archiviazione automatica

### Fase 5 - Dashboard & UX
- Dashboard riepilogativa
- Ricerca e filtri documenti
- Notifiche scadenze contratti

### Fase 6 - Polish & Deploy
- Testing
- Ottimizzazioni
- Deploy

## Convenzioni Codice
- **Backend**: snake_case, type hints ovunque, docstrings
- **Frontend**: camelCase, componenti funzionali, TypeScript preferito
- **API**: RESTful, versioned (/api/v1/), risposte JSON standard
- **Git**: conventional commits (feat:, fix:, docs:, etc.)

## Organizzazione Chat Claude
- **Chat 1**: Setup progetto e struttura base
- **Chat 2**: Backend - modelli e API
- **Chat 3**: Frontend - componenti e pagine
- **Chat 4**: Integrazione AI - classificazione
- **Chat 5**: Testing e bug fixing
- Usare Claude Code per l'implementazione effettiva
