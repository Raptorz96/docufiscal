# DocuFiscal - Progress Fase 3

## Obiettivi Fase 3
Upload & storage documenti con API complete e frontend per gestione/upload.

## Task Progress

### Task 1 ✅ — Modello Documento
- SQLAlchemy model `Documento` (cliente_id FK, contratto_id FK nullable, tipo_documento enum, tipo_documento_raw, file_name, file_path, file_size, mime_type, classificazione_ai JSON, confidence_score, verificato_da_utente, note, created_at, updated_at)
- Enum `TipoDocumento` con 11 categorie: dichiarazione_redditi, fattura, f24, cu, visura_camerale, busta_paga, contratto, bilancio, comunicazione_agenzia, documento_identita, altro
- Schema Pydantic: DocumentoCreate, DocumentoUpdate, DocumentoOut (senza file_path per sicurezza)
- Relationships back_populates su Cliente e Contratto
- Migrazione Alembic `create_documenti_table`
- Export in models/__init__.py e schemas/__init__.py (tutti gli schema presenti)

### Task 2 ✅ — Storage Service
- `backend/app/storage/service.py` con classe `StorageService`
- Metodi: save_file, get_file_path, delete_file, get_mime_type
- Path struttura: `{STORAGE_ROOT}/{cliente_id}/{contratto_id|senza_contratto}/{uuid}_{filename}`
- Path relativo salvato in DB (portabile)
- Chunk-based writing con shutil.copyfileobj (8KB chunks)
- Path traversal protection con `_validate_path()` su get_file_path e delete_file
- delete_file idempotente (non solleva eccezione se file mancante)
- Singleton `storage_service` esportato da `backend/app/storage/__init__.py`
- `STORAGE_ROOT` configurabile in Settings (default: "storage/documenti")
- `storage/` aggiunto a .gitignore

### Task 3 ✅ — API Upload Documenti
- `POST /api/v1/documenti/upload` (multipart form-data)
- Parametri form: cliente_id, contratto_id (opzionale), tipo_documento (default "altro"), note
- Validazioni: cliente exists (404), contratto exists + belongs to cliente (404/400), tipo_documento enum (400), MIME type allowed (400), file size ≤ 50MB (413)
- MIME type detection: filename-based con fallback a content_type
- Cleanup file su errore DB (try/except con rollback + delete_file)
- Cleanup file se troppo grande (delete dopo check)
- Config: MAX_UPLOAD_SIZE = 50MB, ALLOWED_MIME_TYPES = PDF, JPEG, PNG, DOCX, XLSX, DOC, XLS
- Router registrato in main.py, protetto JWT
- Status 201 Created

### Task 4 ✅ — API Documenti CRUD
- `GET /api/v1/documenti/` — Lista con filtri opzionali (cliente_id, contratto_id, tipo_documento), pagination (skip/limit capped 500), order by created_at DESC
- `GET /api/v1/documenti/{id}` — Singolo documento, 404 se non trovato
- `PUT /api/v1/documenti/{id}` — Update metadati (solo campi mutabili via DocumentoUpdate), validazione contratto_id belongs to cliente, partial update con exclude_unset
- `DELETE /api/v1/documenti/{id}` — Elimina record DB prima, poi file da filesystem
- Tutti protetti JWT

### Task 5 ✅ — API Download Documenti
- `GET /api/v1/documenti/{id}/download` — StreamingResponse con file
- Generator function con chunks da 8KB (coerente con StorageService)
- Content-Disposition header con filename sanitizzato (escape virgolette) + filename* RFC 5987 UTF-8 per caratteri non-ASCII
- Content-Type da documento.mime_type, Content-Length da documento.file_size
- 404 se documento non trovato in DB o file mancante su filesystem
- Protetto JWT
- Import: `from urllib.parse import quote`

### Task 6 ✅ — Service API Documenti Frontend
- `frontend/src/services/documentoService.ts` con pattern coerente agli altri service
- Funzioni: getDocumenti(params?), getDocumento(id), uploadDocumento(FormData), updateDocumento(id, data), deleteDocumento(id), downloadDocumento(id, fileName)
- Upload: NO manual Content-Type header (axios gestisce il boundary automaticamente)
- Download: responseType blob, object URL + temporary link click + revokeObjectURL
- `frontend/src/types/documento.ts`: TipoDocumento union type, Documento interface (senza file_path), DocumentoUpdate partial type

### Task 7 ✅ — Pagina Lista Documenti
- `frontend/src/pages/DocumentiPage.tsx` con pattern coerente a ClientiPage/ContrattiPage
- Filtri: Cliente (select), Tipo Documento (select 11 categorie), Contratto (select filtrato per cliente)
- Tabella: Nome file, Tipo Documento (badge colorato), Cliente, Dimensione, Data caricamento, Azioni (Download/Elimina)
- Badge colorati per ogni tipo documento (11 colori distinti)
- Helper formatFileSize e formatDate
- clientiMap e contrattiMap con useRef per lookup O(1)
- Reset contratto filter nell'onChange handler del cliente (no useEffect separato, evita double fetch)
- Route `/documenti` registrata in App.tsx, link in sidebar AppLayout.tsx
- `frontend/src/utils/documentoLabels.ts`: TIPO_LABELS e TIPO_BADGE_CLASSES estratti come modulo condiviso

### Task 8 ✅ — Modale Upload Documento
- `frontend/src/components/UploadDocumentoModal.tsx`
- Campi: Cliente (required), Contratto (opzionale, filtrato per cliente), Tipo Documento (default "altro"), Note (textarea), File (input con accept)
- FormData costruita al submit senza Content-Type manuale
- Loading state su bottone submit, errore inline nella modale (non alert)
- Reset form all'apertura modale, reset contratto al cambio cliente (nell'handler)
- Validazione frontend: file e cliente obbligatori
- Integrata in DocumentiPage: bottone "+ Carica Documento" attivo, onSuccess chiude modale e ricarica lista
- `frontend/src/utils/formatters.ts`: formatFileSize e formatDate estratti come modulo condiviso (eliminata duplicazione)

## Fase 3 COMPLETATA ✅

## Convenzioni
- Backend: snake_case, type hints, docstrings, SQLAlchemy 2.0
- Frontend: camelCase, functional components, TypeScript strict, no any, import type per type-only
- Frontend hooks: useCallback per fetch, useRef per timer/flags/maps
- Frontend utils: moduli condivisi in utils/ per labels, formatters
- API: RESTful, /api/v1/, JSON, HTTPException, JWT protection
- Git: conventional commits
- Workflow: spec in chat → Claude Code implementa → code review → fix → push
