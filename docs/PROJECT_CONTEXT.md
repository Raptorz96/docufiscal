# Contesto di progetto — DocuFiscal

Questo documento è il riferimento canonico per orientarsi nella codebase dopo la migrazione da Claude a ChatGPT/Codex. Descrive lo stato corrente del repository; in caso di conflitto con documentazione precedente, prevalgono codice, migrazioni e test, seguiti da questo documento.

## 1. Scopo del progetto

DocuFiscal è un'applicazione per studi professionali e commercialisti che centralizza clienti, contratti, documenti e scadenze. Automatizza classificazione, associazione e ricerca dei documenti, estrae scadenze e dati contrattuali tramite AI e offre consultazione semantica con riferimenti alle fonti.

- Repository: `Raptorz96/docufiscal`.
- Branch canonico: `main`.

## 2. Baseline verificata

La baseline corrente verificata è:

- backend: **80/80 test passing**;
- frontend lint: **0 errori, 0 warning**;
- frontend build: **PASS**;
- Node.js: **22.22.2**;
- npm: **10.9.7**;
- `.nvmrc` presente nella root con la versione Node canonica.

## 3. Stack e architettura

- Frontend: React 19, TypeScript, Vite e Tailwind CSS.
- Backend: FastAPI, SQLAlchemy 2.x e Alembic.
- Database: SQLite nello sviluppo locale; PostgreSQL nello stack Docker/produzione.
- Persistenza documenti: filesystem, con percorsi relativi salvati nel database.
- AI documentale: un provider configurabile selezionato da `AI_PROVIDER`.
- RAG: ChromaDB persistente e embedding locali `all-MiniLM-L6-v2`.
- API protette: JWT bearer tramite dipendenze FastAPI.

Il frontend consuma API REST FastAPI. Il backend coordina database relazionale, storage filesystem, provider AI, indice vettoriale e Google Calendar.

## 4. Dominio

Le entità persistenti principali sono:

- `Cliente`: anagrafica con CF/P.IVA opzionali e un `short_id` numerico univoco, usato per il routing rapido da filename.
- `TipoContratto`: catalogo dei tipi e delle categorie contrattuali.
- `Contratto`: contratto manuale associato a cliente e tipo contratto.
- `Documento`: file caricato, classificazione, metadata e associazioni opzionali a cliente e contratto. `Documento.cliente_id` può essere `null`, quindi sono supportati documenti non assegnati.
- `Scadenza`: modello universale per date e informazioni estratte. Può derivare da un documento (`documento_id`) oppure da un contratto manuale (`contratto_id`).
- `User`: account applicativo autenticato.
- `GoogleToken`: credenziali OAuth Google Calendar per utente.

## 5. Pipeline documentale e AI

L'upload segue questo ordine logico:

1. routing deterministico tramite short ID numerico estratto dal filename;
2. salvataggio del file e routing regex tramite CF/P.IVA estratti dal testo;
3. classificazione con il provider LLM configurato;
4. se il cliente non è ancora noto, matching locale su CF/P.IVA restituiti dall'AI;
5. eventuale ricollocazione del file e persistenza del record `Documento`;
6. indicizzazione del testo nel RAG;
7. estrazione generica della scadenza per i documenti assegnati;
8. arricchimento specifico per documenti contrattuali.

`AI_PROVIDER` seleziona un solo provider: non esiste una fallback chain automatica Gemini → Claude → OpenAI. Gemini è il default corrente; sono implementati classifier Gemini, Claude e OpenAI. La soglia di confidenza determina quando la classificazione proposta sostituisce automaticamente il tipo generico scelto in upload.

Gemini, Claude e OpenAI catturano normalmente gli errori delle chiamate di classificazione e restituiscono un risultato degradato (`altro`, confidence `0`). Questo non rende però l'intero upload sempre best-effort: le eccezioni precedenti alla chiamata, incluse quelle di `get_classifier()`, non sono completamente isolate.

## 6. Scadenze

`Scadenza` è il modello unico per scadenze documentali e contratti manuali. Può contenere data iniziale/finale, tipo, descrizione, importo o canone, durata, rinnovo automatico, preavviso, parti, clausole, confidenza e stato di verifica.

- I documenti assegnati possono produrre una scadenza generica tramite estrazione AI.
- `documento_id` e `contratto_id` sono nullable ma unique: un singolo `Documento` e un singolo `Contratto` possono avere ciascuno al massimo una `Scadenza` associata.
- I documenti contrattuali ricevono un secondo passaggio di estrazione strutturata, che arricchisce la scadenza già creata dall'estrazione generica quando esiste, invece di crearne una seconda.
- La creazione o modifica di un `Contratto` manuale sincronizza una scadenza verificata quando è presente `data_fine`; la rimuove se la data finale viene eliminata.
- L'API scadenze espone elenco, ricerca e filtri su cliente, tipo, intervallo date e verifica.

## 7. Vector search e RAG

- Collection ChromaDB: `documenti_rag`.
- Embedding: Sentence Transformers `all-MiniLM-L6-v2`.
- Persistenza: directory `chroma_db` accanto alla root dello storage documentale.
- Indicizzazione: testo completo e metadata disponibili del documento.
- Ricerca: similarità vettoriale, con filtri metadata opzionali.

Il chatbot recupera contesto documentale da ChromaDB. Per query riconosciute come pertinenti alle scadenze aggiunge anche un contesto strutturato proveniente dal database. La risposta può includere ID e nomi dei documenti citati. Per richieste pertinenti al calendario, se l'utente ha collegato Google Calendar, il chatbot può interpretare ed eseguire azioni di creazione evento.

Gli aggiornamenti dei metadata ChromaDB devono continuare a distinguere un valore assente da un valore falso o numericamente nullo, usando controlli `is not None`.

## 8. Autenticazione

- Autenticazione OAuth2 password flow con JWT bearer.
- Il claim JWT `sub` contiene l'email dell'utente.
- Le rotte protette risolvono l'utente cercando l'email contenuta in `sub`.
- Un cambio email rende quindi invalido il token corrente. Il frontend effettua intenzionalmente il logout e richiede un nuovo login.
- Il cambio password aggiorna l'hash bcrypt ma non invalida automaticamente JWT già emessi.

## 9. Google Calendar

Google Calendar è un'integrazione opzionale per utente. Il backend conserva access token, refresh token, scadenza e scope in `GoogleToken`, rinnova le credenziali quando possibile e permette eventi personalizzati o derivati da una `Scadenza`.

Lo `state` OAuth è attualmente conservato nel dizionario in-memory `_pending_states`. La scelta è compatibile con un processo single-instance, ma va rivalutata prima di scaling, multi-processo o multi-instance, dove servirebbe uno store condiviso con scadenza esplicita.

## 10. Frontend e UX

Le aree applicative correnti sono:

- Dashboard;
- Scadenze;
- Clienti;
- Contratti;
- Documenti;
- Profilo.

L'interfaccia include inoltre:

- Omnibox globale per ricerca semantica;
- PDF drawer con ciclo di vita controllato degli Object URL;
- chatbot RAG;
- dark mode class-based con preferenza persistita localmente;
- eliminazione bulk di documenti;
- eliminazione bulk di contratti;
- gestione della classificazione e dei documenti non assegnati;
- connessione opzionale a Google Calendar dal profilo.

## 11. Deploy e persistenza

Lo stack `docker-compose.yml` comprende PostgreSQL, backend e frontend:

- tutti i servizi usano `restart: always`;
- PostgreSQL usa un volume persistente dedicato;
- il backend usa un volume persistente per storage documenti e ChromaDB;
- database, backend e frontend sono pubblicati su `127.0.0.1`;
- il backend applica le migrazioni Alembic prima di avviare Uvicorn.

L'hosting production effettivo è **da confermare**: la documentazione storica è incoerente tra una VM Ubuntu su Unraid e un generico VPS Ubuntu. Non assumere una delle due descrizioni come stato corrente senza verifica esterna.

## 12. Decisioni architetturali da preservare

- Eseguire routing deterministico e matching locale prima di delegare l'identificazione all'AI.
- Se una chiamata AI o un'elaborazione è sincrona e bloccante, eseguirla fuori dall'event loop tramite thread offload quando necessario.
- Aggiornare i metadata ChromaDB con controlli espliciti `is not None`.
- Mantenere `Scadenza` come modello universale per documenti e contratti manuali.
- Conservare il logout intenzionale dopo il cambio email, coerente con `sub=email`.
- Mantenere Google Calendar opzionale e non necessario al funzionamento principale.
- Conservare la dark mode Tailwind basata sulla classe `dark`.
- Mantenere un solo provider AI selezionato dalla configurazione; non documentare né presumere fallback automatici inesistenti.

## 13. Debiti e incongruenze note

- L'upload AI non è completamente isolato dagli errori. Le implementazioni dei classifier degradano normalmente a `altro` con confidence `0`, ma `get_classifier()` può fallire prima di `aclassify()`, per esempio con `AI_PROVIDER` non supportato. Poiché il file fisico viene scritto prima della classificazione, questo percorso può interrompere l'upload e lasciare un file orfano.
- `CONFIDENCE_THRESHOLD` vale `0.80` nel default applicativo ma `0.75` in `backend/.env.example`.
- `_pending_states` per Google OAuth è in-memory e non adatto senza revisione a deployment multi-instance.
- Restano commenti e docstring Claude-centrici anche se Gemini è il provider predefinito.
- Il file `.env.example` nella root è obsoleto e incompleto rispetto all'architettura AI corrente: documenta ancora solo `CLAUDE_API_KEY` tra le API esterne e non espone variabili correnti come `AI_PROVIDER`, `AI_MODEL`, `AI_API_KEY` e le configurazioni Gemini/OpenAI.
- `backend/requirements.txt` non contiene il package `openai`, anche se `backend/app/ai/openai_classifier.py` importa `OpenAI` e `AsyncOpenAI`. In un'installazione pulita il provider OpenAI non è quindi garantito funzionante.
- Alcuni `eslint-disable-next-line react-hooks/exhaustive-deps` restano in `ClientiPage.tsx` e `DocumentiPage.tsx`; richiedono un audit separato, non una rimozione meccanica.
- La build frontend passa ma segnala dati Browserslist obsoleti, `documentoService.ts` importato sia dinamicamente sia staticamente e un chunk JavaScript superiore a 500 kB.
- Le vulnerabilità npm eventualmente segnalate devono essere valutate separatamente, senza applicare automaticamente `npm audit fix` o aggiornamenti indiscriminati.
- La baseline canonica usa Node 22.22.2, mentre il Dockerfile frontend usa ancora `node:20-alpine`.
- Il deployment production reale è da confermare.

## 14. Documentazione storica

La documentazione, il precedente Project Knowledge e i piani e le roadmap Claude restano disponibili nella storia Git. Possono descrivere funzionalità non ancora implementate, già superate o configurazioni non più correnti e non costituiscono una fonte canonica corrente. Dopo la migrazione non devono prevalere su `docs/PROJECT_CONTEXT.md` e sulla codebase verificata dai test.
