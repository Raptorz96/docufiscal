# DocuFiscal — Roadmap

## 1. Ruolo del documento

Questa roadmap raccoglie attività ancora aperte e possibili evoluzioni da valutare. Non è la fonte di verità per architettura, stato tecnico, decisioni o debiti: per questi aspetti il riferimento canonico è [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md), verificato rispetto a codebase e test.

Le iniziative indicate come candidate non sono decisioni già prese. Devono essere validate per valore, priorità, costi operativi e impatto sull'architettura.

## 2. Stato funzionale attuale

DocuFiscal dispone già di:

- autenticazione JWT, profilo utente e integrazione opzionale Google OAuth/Calendar;
- gestione di clienti, tipi contratto, contratti, documenti e scadenze;
- upload su filesystem, documenti non assegnati e routing cliente prima deterministico, poi regex e infine AI;
- Short ID ottenuto da un filename che inizia con `#` opzionale, cifre e un separatore `_`, spazio o `-`, confrontato con `Cliente.short_id`;
- classificazione tramite un singolo provider scelto da `AI_PROVIDER`, con Gemini come default e soglia applicativa predefinita `0.80`;
- estrazione AI generica delle scadenze e arricchimento specifico dei contratti;
- ChromaDB tramite `vector_store.py`, indicizzazione on-upload, ricerca semantica e chatbot RAG con citazioni;
- Omnibox globale, PDF drawer, dark mode e operazioni bulk su documenti e contratti;
- creazione di eventi Google Calendar, inclusi eventi derivati da scadenze;
- Docker Compose per PostgreSQL, backend e frontend;
- baseline backend di 80/80 test passing e frontend con lint e build verificati.

Non esiste una fallback chain automatica Gemini → Claude → OpenAI: la configurazione seleziona un solo provider. Non esiste più un modulo legacy `embeddings.py`; `search.py` usa già `vector_store.py`.

## 3. Backlog tecnico confermato

### Robustezza upload e classificazione

- Rendere atomico o compensabile il flusso upload quando la selezione/inizializzazione del classifier o la classificazione falliscono prima della persistenza completa.
- Evitare file orfani e definire chiaramente rollback di filesystem, database e indice vettoriale.
- Aggiungere test mirati sui fallimenti prima di `aclassify()`, sui cleanup e sulla coerenza tra documento persistito e file fisico.

### Test mirati

- Coprire maggiormente endpoint chat/RAG, parsing delle citazioni e azioni Calendar.
- Coprire i flussi Google OAuth/refresh/disconnessione, inclusi state non valido o scaduto.
- Aggiungere test di integrazione sui passaggi upload → persistenza → indicizzazione → scadenza.
- Definire verifiche di recupero o reindicizzazione quando ChromaDB e database non sono allineati.

### Dipendenze e configurazione

- Allineare i file example alla configurazione AI effettiva e risolvere le differenze nei valori predefiniti.
- Rendere installabili e verificabili tutti i provider dichiarati, oppure ridurre esplicitamente quelli supportati.
- Allineare la runtime Node delle immagini di build alla baseline di progetto.
- Valutare separatamente vulnerabilità npm e warning di build, evitando aggiornamenti indiscriminati.

### Qualità operativa

- Introdurre CI per test backend, lint e build frontend, con versioni runtime esplicite.
- Aggiungere controlli di migrazione e packaging alle verifiche automatizzate.
- Definire logging, metriche, gestione errori e procedure di backup/ripristino per database, storage e indice vettoriale.

I dettagli puntuali dei debiti già noti restano in `PROJECT_CONTEXT.md` e non vengono duplicati qui.

## 4. Evoluzioni prodotto da validare

Le seguenti iniziative sono candidate da confermare con requisiti e priorità:

- ingestione mobile tramite Telegram, WhatsApp o un canale alternativo;
- background jobs e coda per upload, OCR, classificazione e batch di grandi dimensioni;
- notifiche delle scadenze via email, push o canali configurabili;
- storage S3-compatible per separare i file dal filesystem della singola istanza;
- evoluzione Google Calendar verso sincronizzazione, aggiornamento o rimozione eventi e gestione più ricca dei reminder;
- eventuali flussi di revisione e assegnazione collaborativa per più operatori.

Prima dell'adozione vanno chiariti sicurezza, privacy, idempotenza, costi, gestione degli errori e modello operativo.

## 5. Deploy e produzione

Docker Compose esiste già e avvia PostgreSQL, backend e frontend con volumi persistenti e binding locale. Questo non equivale a un deployment production verificato: l'hosting effettivo e la procedura operativa corrente restano da confermare.

Attività da pianificare prima di considerare il deploy production-grade:

- CI/CD con build, test, migrazioni e strategia di rilascio/rollback;
- gestione sicura e centralizzata dei segreti e configurazione coerente degli environment;
- terminazione HTTPS, reverse proxy e rate limiting;
- backup e restore verificati per PostgreSQL, filesystem e ChromaDB;
- decisione esplicita tra volume filesystem e storage S3-compatible;
- health check, osservabilità e alerting;
- sostituzione dello state OAuth in-memory con uno store condiviso se si adotta un deployment multi-processo o multi-instance.

## 6. Completato / storico recente

Le seguenti attività sono già operative e non devono tornare nel backlog salvo nuovi requisiti:

- pipeline di routing Short ID → regex CF/P.IVA → classificazione AI → matching locale;
- provider singolo configurabile con Gemini predefinito;
- indicizzazione ChromaDB on-upload e ricerca semantica tramite `vector_store.py`;
- chatbot RAG con contesto scadenze e riferimenti documentali;
- modello universale `Scadenza`, estrazione AI e scadenze da contratti manuali;
- Omnibox globale, PDF drawer, dark mode e bulk delete;
- connessione Google OAuth e creazione eventi Calendar;
- Docker Compose con PostgreSQL e volumi persistenti;
- ampliamento della suite backend a 80 test e azzeramento di errori/warning ESLint nella baseline verificata;
- definizione di Node 22.22.2 tramite `.nvmrc` e aggiornamento della documentazione canonica.

La vecchia pianificazione per fasi resta parte della storia Git; non rappresenta più lo stato corrente del progetto.
