# Istruzioni operative per DocuFiscal

## 1. Fonti e precedenza

- Prima di modifiche non banali, leggere `docs/PROJECT_CONTEXT.md`.
- In caso di conflitto, codebase, migrazioni e test prevalgono sulla documentazione.
- `docs/PROJECT_CONTEXT.md` è la fonte canonica per architettura, stato tecnico, decisioni e debiti noti.
- `README.md` descrive l'uso operativo del progetto.
- `docs/ROADMAP_V2.md` raccoglie backlog ed evoluzioni candidate, non lo stato corrente né requisiti già approvati.
- Segnalare le incongruenze rilevate; non correggerle silenziosamente o fuori dallo scope del task.

## 2. Regole architetturali da preservare

- Eseguire routing deterministico e matching locale prima di ricorrere all'AI.
- Usare un solo provider selezionato da `AI_PROVIDER`; non introdurre o presumere una fallback chain automatica.
- Spostare fuori dall'event loop le chiamate AI e le altre operazioni sincrone bloccanti quando necessario.
- Negli aggiornamenti dei metadata ChromaDB distinguere `None` dai valori falsy con controlli espliciti `is not None`.
- Conservare `Scadenza` come modello universale per documenti e contratti manuali.
- Rispettare il vincolo di al massimo una `Scadenza` per `Documento` e una per `Contratto`.
- Nel flusso documentale dual-phase, il passaggio contrattuale deve arricchire la `Scadenza` esistente quando presente, non crearne una seconda.
- Conservare il logout dopo il cambio email, coerente con JWT `sub=email`.
- Mantenere Google Calendar opzionale rispetto al funzionamento principale.
- Conservare la dark mode Tailwind class-based.

Non cambiare decisioni architetturali importanti senza prima segnalarne impatto e alternative e richiedere una discussione esplicita.

## 3. Workflow Git

Workflow preferito:

1. partire da `main` aggiornato e con working tree pulita;
2. creare un branch `codex/<task>`;
3. implementare modifiche focalizzate;
4. eseguire verifiche proporzionate al rischio;
5. creare commit coerenti e facilmente revisionabili, usando conventional commits;
6. eseguire il push del branch, non direttamente di `main`;
7. aprire una draft PR verso `main` quando richiesto;
8. effettuare il merge solo dopo review e approvazione esplicita dell'utente;
9. preferire lo squash merge, salvo diversa indicazione.

Non eseguire push diretto su `main` senza istruzione esplicita. Non creare un commit per ogni micro-step se ciò frammenta inutilmente una singola modifica logica.

## 4. Verifiche

Test backend completo:

```bash
cd backend
python -m pytest tests/ -v
```

Test backend mirato:

```bash
cd backend
python -m pytest tests/percorso_test.py -v
```

Frontend lint e build:

```bash
nvm use
cd frontend
npm run lint
npm run build
```

- Durante lo sviluppo eseguire controlli mirati e proporzionati alla modifica.
- Prima di considerare concluso un task, eseguire tutte le verifiche complete pertinenti.
- Non assumere un numero fisso di test come requisito permanente: riportare il risultato effettivo.
- Non eseguire automaticamente `npm audit fix`, aggiornamenti massivi o upgrade di dipendenze.

## 5. Convenzioni operative

- Nel backend seguire lo stile Python esistente, mantenere type hints e coerenza con FastAPI, SQLAlchemy e Alembic.
- Nel frontend seguire le convenzioni React e TypeScript già adottate dal progetto.
- Usare conventional commits con messaggi che descrivano una singola modifica logica.
- Non versionare file `.env`, credenziali, token o altri segreti.
- Preferire modifiche minime, focalizzate e verificabili.
- Non includere cleanup o refactor non richiesti mentre si risolve un task circoscritto.

## 6. Debiti e aree delicate

Consultare `docs/PROJECT_CONTEXT.md` per i dettagli tecnici e `docs/ROADMAP_V2.md` per il backlog. In particolare:

- il flusso upload/classifier contiene percorsi di errore ancora da rendere atomici o compensabili;
- lo state OAuth è conservato in-memory e richiede revisione per deployment multi-processo o multi-instance;
- il provider OpenAI può non essere installabile usando il solo `backend/requirements.txt` corrente;
- la runtime Node locale canonica e quella usata dal Docker frontend non sono ancora allineate;
- il deployment production effettivo non è confermato.

Non correggere incidentalmente questi punti durante task non correlati.

## 7. Limiti di autonomia

- Implementare autonomamente i task approvati entro lo scope concordato.
- Fermarsi e segnalare impatto e opzioni quando una richiesta introduce una nuova decisione architetturale importante.
- Non trasformare le candidate della roadmap in requisiti o decisioni già approvati.
- Non rimuovere documentazione storica o configurazioni legacy finché la migrazione non è stata verificata e la rimozione non è stata autorizzata.
- Non assumere hosting, topologia, credenziali o altri dettagli production non verificati.
