# DocuFiscal - ROADMAP V2.0 (Nuova Fonte di Verità)

Questo documento delinea il percorso di sviluppo futuro di DocuFiscal, integrando i requisiti del "Capitolato delle Specifiche Funzionali V1.0".

---

## 1. Stato Attuale (Fasi 1-7)
Il nucleo di DocuFiscal è robusto e l'esperienza utente è stata notevolmente migliorata.
- ✅ **Anagrafica & CRM:** Gestione completa clienti/contratti.
- ✅ **Storage & PDF Viewer:** Upload, download e visualizzazione integrata via PDF Drawer (Split-Screen).
- ✅ **Motore AI & Feedback:** Classificazione automatica (Tipi, Macro-Categorie) con Human-in-the-loop (Conferma/Correggi).
- ✅ **Archivio Strutturato:** Implementazione `short_id`, `macro_categoria` e `anno_competenza`.
- ✅ **Logica deterministica:** Instradamento rapido via `#ID_` nel nome file (Short Circuit).
- ✅ **UI/UX Avanzata:** Menù laterale a scomparsa, layout full-width ottimizzato e filtri istantanei.
- ✅ **Auth & Scadenziario Base:** JWT Security e monitoraggio scadenze contrattuali lato dashboard.

---

## 2. Gap Analysis (Cosa Manca)
Rispetto alle specifiche, ci concentriamo ora su:
1. **Ingestione Multicanale:** Integrazione Bot (WhatsApp/Telegram).
2. **Ricerca Semantica Full:** Indicizzazione profonda dei contenuti testuali (OCR + Vector Search).
3. **Sincronizzazione Calendario:** Integrazione Google Calendar per scadenze esterne.
4. **Analisi Proattiva:** Estrazione automatica di scadenze da documenti (es. F24) non ancora automatizzata al 100%.

---

## 3. Nuova Pianificazione (Fasi 8-10)

### Fase 8: Ingestione Mobile & Background Tasks (Focus Prossimo)
*Obiettivo: Portare DocuFiscal "On-the-Road" e scalare i caricamenti.*
- **Task 8.1:** Webhook Telegram/WhatsApp per la ricezione file.
- **Task 8.2:** Auth via numero di telefono (solo operatori Studio).
- **Task 8.3:** Migrazione Upload su coda asincrona (Redis/Celery o BackgroundTasks avanzati) per gestire sessioni massive.

### Fase 9: Ricerca NLP & Omnibox
*Obiettivo: Rendere il reperimento dei documenti istantaneo e intuitivo.*
- **Task 9.1:** Omnibox globale (Search Bar intelligente) nel layout principale.
- **Task 9.2:** Query semantiche: "Mostrami le fatture di Rossi del 2023" usando LLM + Vector Search.

### Fase 10: Automazione Scadenze & API Esterne
*Obiettivo: Automatizzare le scadenze dello Studio.*
- **Task 10.1:** Integrazione Google Calendar API.
- **Task 10.2:** Estrazione AI proattiva delle scadenze dai documenti e sincronizzazione automatica.

---

## 4. Prossimi Passi Tecnici
1. **Configurazione Bot Telegram:** Creazione bot e setup webhook.
2. **Refactor Ingestione:** Supporto nativo per flussi asincroni per file grandi o multipli.
3. **Embedding Pipeline:** Inizio indicizzazione dei PDF per la ricerca testuale.
