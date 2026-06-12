# Google Calendar Banner + Fix Contratti Manuali Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere un banner "Connetti Google Calendar" in Dashboard e ScadenzePage, e correggere l'endpoint `from-scadenza` per supportare scadenze da contratti manuali (documento_id = null).

**Architecture:** Il banner è un componente React riutilizzabile che interroga `GET /api/v1/google/status` al mount e si auto-nasconde se l'utente è già connesso. Il fix backend modifica la logica di costruzione del titolo/descrizione dell'evento in `google_calendar.py` per gestire il caso `documento_id = null`.

**Tech Stack:** React + TypeScript (Tailwind CSS), FastAPI + SQLAlchemy (Python)

---

## File Map

| File | Azione | Responsabilità |
|------|--------|----------------|
| `frontend/src/components/GoogleCalendarBanner.tsx` | CREA | Banner riutilizzabile con fetch status e redirect OAuth |
| `frontend/src/pages/DashboardPage.tsx` | MODIFICA (riga ~327) | Import + render `<GoogleCalendarBanner className="mb-4" />` sopra la griglia scadenze |
| `frontend/src/pages/ScadenzePage.tsx` | MODIFICA (riga ~86) | Import + render `<GoogleCalendarBanner className="mb-4" />` dopo header/filtri |
| `backend/app/api/google_calendar.py` | MODIFICA (righe 77–95) | Fix logica titolo/descrizione per contratti manuali |

---

## Task 1: Creare GoogleCalendarBanner.tsx

**Files:**
- Create: `frontend/src/components/GoogleCalendarBanner.tsx`

- [ ] **Step 1: Creare il componente**

```tsx
// frontend/src/components/GoogleCalendarBanner.tsx
import React, { useEffect, useState } from 'react';
import { getGoogleStatus, getGoogleAuthorizeUrl } from '@/services/googleService';

interface GoogleCalendarBannerProps {
  className?: string;
}

const GoogleCalendarBanner: React.FC<GoogleCalendarBannerProps> = ({ className }) => {
  const [connected, setConnected] = useState<boolean | null>(null); // null = loading

  useEffect(() => {
    getGoogleStatus()
      .then((s) => setConnected(s.connected))
      .catch(() => setConnected(true)); // fail silent: non mostrare banner se errore
  }, []);

  // Non mostrare nulla durante loading o se già connesso
  if (connected !== false) return null;

  const handleConnect = async () => {
    try {
      const url = await getGoogleAuthorizeUrl();
      window.location.href = url;
    } catch {
      // silently ignore
    }
  };

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-4 ${className ?? ''}`}>
      <span className="text-2xl shrink-0" aria-hidden="true">📅</span>
      <p className="text-sm text-blue-800 flex-1">
        Collega Google Calendar per aggiungere le scadenze direttamente al tuo calendario.
      </p>
      <button
        onClick={handleConnect}
        className="shrink-0 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
      >
        Connetti Google Calendar
      </button>
    </div>
  );
};

export default GoogleCalendarBanner;
```

- [ ] **Step 2: Verificare che il file sia stato creato correttamente**

```bash
cat frontend/src/components/GoogleCalendarBanner.tsx | head -5
```
Expected: prima riga `// frontend/src/components/GoogleCalendarBanner.tsx`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/GoogleCalendarBanner.tsx
git commit -m "feat: add GoogleCalendarBanner reusable component"
```

---

## Task 2: Integrare il banner in DashboardPage

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx:1,327`

Stato attuale: il file importa già `getGoogleStatus` e ha `googleConnected` state. Il banner va inserito nella sezione scadenze, sopra la griglia delle card.

- [ ] **Step 1: Aggiungere l'import di GoogleCalendarBanner** (riga 1, dopo gli altri import)

Trovare il blocco import esistente (righe 1–5) e aggiungere l'import:

```tsx
import GoogleCalendarBanner from '@/components/GoogleCalendarBanner';
```

La sezione import diventa:
```tsx
import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getDashboardStats } from '@/services/dashboardService';
import { getGoogleStatus, createEventFromScadenza } from '@/services/googleService';
import type { DashboardStats, ScadenzaDashboard } from '@/types/dashboard';
import GoogleCalendarBanner from '@/components/GoogleCalendarBanner';
```

- [ ] **Step 2: Inserire il banner sopra la griglia scadenze**

Trovare il blocco `{critiche.length > 0 ? (` (riga ~327). Subito prima (dentro il `<div>` della sezione scadenze, dopo il div header con `border-b`), aggiungere il banner:

Il blocco che inizia con:
```tsx
        {critiche.length > 0 ? (
          <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
```

va preceduto da:
```tsx
        <div className="px-6 pt-6">
          <GoogleCalendarBanner />
        </div>
```

In pratica la struttura diventa:
```tsx
        <div className="px-6 pt-6">
          <GoogleCalendarBanner />
        </div>
        {critiche.length > 0 ? (
          <div className="p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
```

- [ ] **Step 3: Verificare che il bottone "Aggiungi a Calendar" appaia per tutti i tipi di scadenza**

Controllare riga 162 di `DashboardPage.tsx`:
```tsx
{googleConnected && s.data_scadenza && (
```
Questa condizione NON dipende da `documento_id` → il bottone appare per tutte le scadenze con data. **Nessuna modifica necessaria.**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx
git commit -m "feat: add GoogleCalendarBanner to DashboardPage scadenze section"
```

---

## Task 3: Integrare il banner in ScadenzePage

**Files:**
- Modify: `frontend/src/pages/ScadenzePage.tsx`

Stato attuale: il file non importa googleService né ha stato Google. Bisogna solo aggiungere il banner (non il bottone nella tabella, come da spec).

- [ ] **Step 1: Aggiungere import del banner**

In cima al file, dopo gli import esistenti (riga 4):

```tsx
import GoogleCalendarBanner from '@/components/GoogleCalendarBanner';
```

La sezione import diventa:
```tsx
import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getScadenze } from '../services/scadenzeService';
import type { Scadenza, ScadenzaFilters } from '../types/scadenza';
import GoogleCalendarBanner from '@/components/GoogleCalendarBanner';
```

- [ ] **Step 2: Inserire il banner nel JSX, dopo il blocco filtri e prima della tabella**

Trovare il blocco `{/* Tabella */}` (riga ~117). Subito prima inserire:

```tsx
            {/* Google Calendar Banner */}
            <GoogleCalendarBanner className="mb-4" />
```

In pratica la struttura diventa:
```tsx
            {/* Google Calendar Banner */}
            <GoogleCalendarBanner className="mb-4" />

            {/* Tabella */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/ScadenzePage.tsx
git commit -m "feat: add GoogleCalendarBanner to ScadenzePage"
```

---

## Task 4: Fix backend — from-scadenza per contratti manuali

**Files:**
- Modify: `backend/app/api/google_calendar.py`

Stato attuale (righe 77–95):
```python
cliente = db.query(Cliente).filter(Cliente.id == scadenza.cliente_id).first()
documento = db.query(Documento).filter(Documento.id == scadenza.documento_id).first()

cliente_nome = f"{cliente.nome} {cliente.cognome}".strip() if cliente else "Sconosciuto"
file_name = documento.file_name if documento else "documento"

summary = f"Scadenza contratto — {cliente_nome}"

desc_parts = [f"Cliente: {cliente_nome}", f"Documento: {file_name}"]
```

Problema: quando `documento_id` è `None`, la query ritorna `None` e `file_name = "documento"` — la descrizione mostra "Documento: documento" per i contratti manuali.

Fix: distinguere i due casi nel titolo e nella descrizione.

- [ ] **Step 1: Aggiungere import Contratto**

Alla riga 11 di `google_calendar.py`, aggiungere l'import del modello Contratto:

```python
from app.models.contratto import Contratto
```

La sezione import diventa:
```python
from app.models.google_token import GoogleToken
from app.models.scadenza import Scadenza
from app.models.cliente import Cliente
from app.models.documento import Documento
from app.models.contratto import Contratto
from app.models.user import User
```

- [ ] **Step 2: Sostituire la logica titolo/descrizione**

Trovare il blocco righe 77–95 e sostituirlo con:

```python
    cliente = db.query(Cliente).filter(Cliente.id == scadenza.cliente_id).first()
    cliente_nome = f"{cliente.nome} {cliente.cognome}".strip() if cliente else "Sconosciuto"

    if scadenza.documento_id:
        documento = db.query(Documento).filter(Documento.id == scadenza.documento_id).first()
        file_name = documento.file_name if documento else "documento"
        summary = f"Scadenza: {file_name}"
        desc_parts = [f"Cliente: {cliente_nome}", f"Documento: {file_name}"]
    elif scadenza.contratto_id:
        contratto = db.query(Contratto).filter(Contratto.id == scadenza.contratto_id).first()
        tipo_nome = contratto.tipo_contratto.nome if contratto and contratto.tipo_contratto else "contratto"
        summary = f"Scadenza contratto: {cliente_nome} — {tipo_nome}"
        desc_parts = [f"Cliente: {cliente_nome}", f"Tipo contratto: {tipo_nome}"]
    else:
        summary = f"Scadenza — {cliente_nome}"
        desc_parts = [f"Cliente: {cliente_nome}"]
```

- [ ] **Step 3: Assicurarsi che il resto della funzione rimanga invariato**

Il codice dopo il blocco sostituito deve restare esattamente:
```python
    if scadenza.canone:
        desc_parts.append(f"Canone: {scadenza.canone}")
    if scadenza.rinnovo_automatico is not None:
        desc_parts.append(f"Rinnovo automatico: {'Sì' if scadenza.rinnovo_automatico else 'No'}")
    if scadenza.preavviso_disdetta:
        desc_parts.append(f"Preavviso disdetta: {scadenza.preavviso_disdetta}")
    if scadenza.clausole_chiave:
        desc_parts.append(f"Clausole: {'; '.join(scadenza.clausole_chiave)}")
    desc_parts.append(f"\nGenerato da DocuFiscal")
    description = "\n".join(desc_parts)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/google_calendar.py
git commit -m "fix: google calendar from-scadenza supports contratti manuali (documento_id=null)"
```

---

## Task 5: Verifica finale

- [ ] **Step 1: Eseguire i test backend**

```bash
cd backend && python -m pytest tests/ -x -q
```
Expected: tutti i test passano, nessun errore.

- [ ] **Step 2: Verifica visiva banner (utente non connesso)**

Con browser dev tools, mockare `GET /api/v1/google/status` a restituire `{"connected": false}`:
- Dashboard: banner blu visibile sopra le card scadenze
- ScadenzePage: banner blu visibile sopra la tabella

- [ ] **Step 3: Verifica visiva banner (utente connesso)**

Con browser dev tools, mockare `GET /api/v1/google/status` a restituire `{"connected": true}`:
- Dashboard: nessun banner
- ScadenzePage: nessun banner

- [ ] **Step 4: Commit finale e push**

```bash
git push origin main
```

---

## Note di contesto

- `getGoogleAuthorizeUrl()` è già definita in `frontend/src/services/googleService.ts:8`
- Il bottone "Aggiungi a Calendar" in `DashboardPage.tsx:162` usa già `{googleConnected && s.data_scadenza && (` — nessun check su `documento_id`, quindi funziona già per i contratti manuali
- `ScadenzePage` non ha bottone Calendar nella tabella — la spec non richiede di aggiungerlo, solo il banner
- Il modello `Contratto` ha `contratto.tipo_contratto` (relationship lazy-loaded) con campo `.nome`
