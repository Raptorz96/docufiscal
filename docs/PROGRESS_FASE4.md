# DocuFiscal - Progress Fase 4

## Obiettivi Fase 4
Classificazione AI automatica dei documenti fiscali con supporto multi-provider.

## Decisioni architetturali
- **Provider primario**: Gemini 2.5 Flash (~$0.0004/doc, 30x più economico di Claude Sonnet)
- **Fallback**: Claude Haiku 4.5 come alternativa
- **Esecuzione**: Sincrona sull'upload (2-5s accettabili per v1)
- **Trigger**: Automatico dopo upload, non on-demand
- **Abstraction layer**: Factory pattern per switch provider via .env

## Task Progress

### Task 1 ✅ — Text Extraction Service
- `backend/app/ai/text_extraction.py` con classe `TextExtractionService`
- PDF: PyPDF2 extraction, fallback OCR se <50 chars estratti
- Immagini: pytesseract OCR con lang="ita"
- Lazy imports per evitare crash se tesseract non installato
- ImportError handling per dipendenze OCR mancanti
- Mai blocca l'upload: ritorna "" su errore
- Singleton `text_extraction_service` esportato da `__init__.py`
- Dipendenze: PyPDF2, pytesseract, Pillow, pdf2image
- System deps: tesseract-ocr, tesseract-ocr-ita, poppler-utils

### Task 2 ✅ — Classifier Interface + Config
- `backend/app/ai/classifier.py` con `BaseClassifier` ABC e `ClassificationResult` dataclass
- Dataclass: tipo_documento, tipo_documento_raw, confidence, cliente_suggerito, contratto_suggerito, raw_response
- Factory `get_classifier()` con singleton e lazy imports
- Config aggiunta a `backend/app/core/config.py`: AI_PROVIDER, AI_MODEL, AI_API_KEY, CONFIDENCE_THRESHOLD (0.75)
- `.env.example` aggiornato con sezione AI Classification

### Task 3 ✅ — Gemini Classifier
- `backend/app/ai/gemini_classifier.py` con `GeminiClassifier(BaseClassifier)`
- SDK: `google-genai` (nuovo SDK ufficiale, NON google-generativeai)
- Structured JSON output con `response_mime_type` + `response_schema`
- Validazione tipo_documento con fallback "altro", confidence clamp 0.0-1.0
- Error handling: try/except globale, ritorna `_DEFAULT_RESULT`
- Dipendenza aggiunta a requirements.txt

### Task 4 ✅ — Claude Classifier (fallback)
- `backend/app/ai/claude_classifier.py` con `ClaudeClassifier(BaseClassifier)`
- SDK: `anthropic`
- System prompt "Rispondi SOLO con un JSON valido"
- Error handling specifico: AuthenticationError, RateLimitError + catch generico
- **Refactor**: creato `backend/app/ai/prompts.py` con prompt condiviso
  - `TIPO_DESCRIPTIONS`, `MAX_TEXT_CHARS`, `build_classification_prompt()`
  - Sia Gemini che Claude importano da prompts.py (zero duplicazione)
- `.env.example` aggiornato con commento per configurazione Claude
- Dipendenza `anthropic` aggiunta a requirements.txt

### Task 5 ✅ — Integrazione nell'upload flow
- Modificato `backend/app/api/documenti.py`
- Dopo db.commit() del documento → estrai testo → classifica → aggiorna record
- Logica: extract_text con path assoluto (via storage_service.get_file_path) → query clienti per contesto → classify → update campi AI
- Auto-classificazione SOLO se confidence >= soglia E tipo_documento era "altro" (rispetta scelta manuale utente)
- `classificazione_ai` e `confidence_score` sempre popolati se classificazione ha successo
- NON blocca l'upload: try/except esterno, il documento resta salvato anche se AI fallisce
- Logger aggiunto al file

### Task 6 ✅ — API conferma/override classificazione
- Endpoint già esistente: `PATCH /api/v1/documenti/{id}/classifica` in `backend/app/api/documenti.py`
- Schema `ClassificazioneOverride` in `backend/app/schemas/documento.py`
  - `tipo_documento: Optional[TipoDocumento] = None` — None = conferma pura (solo verificato=True), valore = override tipo
  - `cliente_id`, `contratto_id` (nullable con semantica model_fields_set), `note` opzionali
- Logica endpoint: setta `verificato_da_utente = True`; aggiorna `tipo_documento` solo se fornito; valida cliente/contratto
- `logger.info` aggiunto per tracciabilità (tipo + email utente)
- Test: `backend/tests/conftest.py` (DB SQLite in-memory + StaticPool, fixture user/cliente/documento)
- Test: `backend/tests/test_classifica.py` — 6 test, tutti ✅ PASSED (0.14s)
  - conferma pura, override tipo, override con note, 404, contratto cliente sbagliato (400), non autenticato (401)

### Task 7 ✅ — Frontend classificazione feedback
- `frontend/src/types/documento.ts`: `tipo_documento` opzionale in `ClassificazioneOverride` (allineamento con backend Task 6)
- `frontend/src/services/documentoService.ts`: firma `classificaDocumento` aggiornata a `Partial<ClassificazioneOverride>`
- `frontend/src/pages/DocumentiPage.tsx`:
  - Stato `confirmingId: number | null` per loading individuale per documento
  - `handleConfermaInline(doc)` — PATCH con body `{}` (conferma pura), aggiorna lista in-place senza reload
  - Bottone **verde "✓ Conferma"** affiancato a "Correggi" per tutti i doc con AI non verificata
  - Spinner per bottone durante la conferma, entrambi i bottoni disabilitati
- Componenti preesistenti (nessuna modifica necessaria):
  - `getAiBadge()` — badge colorati per ogni stato (verificato/alta confidence/bassa confidence/no AI)
  - `ClassificazioneModal` — modal completo per override con form tipo/cliente/contratto/note

### Task 8 — Prompt engineering & testing ⬜
- Raffinare prompt con documenti reali
- Tuning soglia confidence

## Struttura modulo AI

```
backend/app/ai/
├── __init__.py              # Export: text_extraction_service, get_classifier, ClassificationResult
├── text_extraction.py       # TextExtractionService (PDF + OCR)
├── classifier.py            # BaseClassifier ABC, ClassificationResult, get_classifier factory
├── prompts.py               # Prompt condiviso: TIPO_DESCRIPTIONS, build_classification_prompt
├── gemini_classifier.py     # GeminiClassifier con structured JSON output
└── claude_classifier.py     # ClaudeClassifier con JSON-only system prompt
```

## Convenzioni
- Backend: snake_case, type hints, docstrings, SQLAlchemy 2.0
- Frontend: camelCase, functional components, TypeScript strict, no any, import type per type-only
- Frontend hooks: useCallback per fetch, useRef per timer/flags/maps
- Frontend utils: moduli condivisi in utils/ per labels, formatters
- API: RESTful, /api/v1/, JSON, HTTPException, JWT protection
- Git: conventional commits
- Workflow: spec in chat → Claude Code implementa → code review → fix → push
