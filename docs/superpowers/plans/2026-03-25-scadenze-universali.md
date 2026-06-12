# Scadenze Universali + Pagina Scadenze — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Estrai scadenze da qualsiasi documento (non solo contratti), tipizzale con badge colorati, e aggiungi una pagina Scadenze dedicata con filtri.

**Architecture:** La tabella `scadenze_contratto` viene rinominata in `scadenze` e arricchita con `tipo_scadenza` e `descrizione`. Un nuovo extractor generico (deadline_extractor) gira su tutti i documenti uploadati; l'extractor contrattuale arricchisce con dati aggiuntivi solo i contratti. Un nuovo router `/scadenze` espone la lista filtrata; una nuova pagina frontend mostra badge colorati per tipo.

**Tech Stack:** Python/FastAPI, SQLAlchemy 2.x (Mapped columns), Alembic (batch_alter_table), Pydantic v2, React/TypeScript, Tailwind CSS.

---

## File Map

### Backend — Modificati
- `backend/alembic/versions/e4f5a6b7c8d9_rename_scadenze_add_tipo.py` — NUOVO: rinomina tabella, aggiunge colonne
- `backend/app/models/scadenza_contratto.py` → `backend/app/models/scadenza.py` — rinominato + nuovi campi
- `backend/app/schemas/scadenza_contratto.py` → `backend/app/schemas/scadenza.py` — rinominato + nuovi campi
- `backend/app/models/__init__.py` — aggiornato import
- `backend/app/api/dashboard.py` — usa `Scadenza`, aggiunge tipo_scadenza/descrizione
- `backend/app/api/documenti.py` — nuovo flusso dual-extraction
- `backend/app/api/contratti.py` — usa `Scadenza`, setta tipo_scadenza="canone"
- `backend/app/api/chat.py` — usa `Scadenza`, aggiorna keywords + testo strutturato
- `backend/app/schemas/dashboard.py` — aggiunge tipo_scadenza/descrizione a ScadenzaDashboardOut
- `backend/app/ai/prompts.py` — aggiunge build_deadline_extraction_prompt()
- `backend/app/main.py` — registra scadenze_router
- `backend/app/api/__init__.py` — esporta scadenze_router
- `backend/tests/conftest.py` — aggiorna import ScadenzaContratto → Scadenza

### Backend — Nuovi
- `backend/app/ai/deadline_extractor.py` — extractor generico
- `backend/app/api/scadenze.py` — endpoint GET /scadenze con filtri

### Frontend — Modificati
- `frontend/src/types/dashboard.ts` — aggiunge tipo_scadenza/descrizione a ScadenzaDashboard
- `frontend/src/pages/DashboardPage.tsx` — badge tipo, mostra descrizione
- `frontend/src/layouts/AppLayout.tsx` — aggiunge voce Scadenze nella sidebar
- `frontend/src/App.tsx` — aggiunge route /scadenze

### Frontend — Nuovi
- `frontend/src/types/scadenza.ts` — interfacce Scadenza, ScadenzaFilters
- `frontend/src/services/scadenzeService.ts` — getScadenze()
- `frontend/src/pages/ScadenzePage.tsx` — pagina completa con filtri + tabella

---

## Task 1 — Migration: rinomina tabella + nuovi campi

**Files:**
- Create: `backend/alembic/versions/e4f5a6b7c8d9_rename_scadenze_add_tipo.py`

- [ ] **Step 1: Crea il file migration**

```python
"""rename scadenze_contratto to scadenze, add tipo_scadenza and descrizione

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-03-25 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rinomina la tabella
    op.rename_table('scadenze_contratto', 'scadenze')

    # 2. Aggiunge nuove colonne (batch per SQLite compat)
    with op.batch_alter_table('scadenze', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'tipo_scadenza',
                sa.String(50),
                nullable=False,
                server_default='contratto',
            )
        )
        batch_op.add_column(
            sa.Column(
                'descrizione',
                sa.Text(),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('scadenze', schema=None) as batch_op:
        batch_op.drop_column('descrizione')
        batch_op.drop_column('tipo_scadenza')
    op.rename_table('scadenze', 'scadenze_contratto')
```

- [ ] **Step 2: Applica la migration e verifica**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m alembic upgrade head
```

Expected: `Running upgrade d3e4f5a6b7c8 -> e4f5a6b7c8d9`

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/e4f5a6b7c8d9_rename_scadenze_add_tipo.py
git commit -m "feat: migration — rename scadenze_contratto→scadenze, add tipo_scadenza+descrizione"
```

---

## Task 2a — Rinomina model Scadenza

**Files:**
- Create: `backend/app/models/scadenza.py` (contenuto del vecchio + nuovi campi)
- Delete: `backend/app/models/scadenza_contratto.py`

- [ ] **Step 1: Crea il nuovo file `backend/app/models/scadenza.py`**

```python
"""Scadenza model — deadline extracted from any document or manual contract."""
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Scadenza(Base):
    """Deadline extracted by AI from any document, or from a manual contract."""

    __tablename__ = "scadenze"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    documento_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("documenti.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )

    contratto_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("contratti.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )

    cliente_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clienti.id", ondelete="CASCADE"),
        nullable=False,
    )

    tipo_scadenza: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="contratto",
        doc="Tipo: pagamento, incasso, canone, adempimento, rinnovo, generico, contratto"
    )
    descrizione: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        doc="AI-generated description of the deadline"
    )

    data_inizio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_scadenza: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    durata: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rinnovo_automatico: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    preavviso_disdetta: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    canone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    parti_coinvolte: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    clausole_chiave: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    verificato: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    documento: Mapped[Optional["Documento"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Documento", back_populates="scadenza_contratto"
    )
    contratto: Mapped[Optional["Contratto"]] = relationship("Contratto")  # type: ignore[name-defined]  # noqa: F821
    cliente: Mapped["Cliente"] = relationship("Cliente")  # type: ignore[name-defined]  # noqa: F821
```

**NOTA sulla unique constraint**: `unique=True` su `documento_id` è corretto — la constraint esisteva già nella tabella `scadenze_contratto` (migration `a1b2c3d4e5f6`) e viene preservata automaticamente da `op.rename_table`. Non è necessario ricrearla nella nuova migration. La logica dual-phase del Task 5 è safe: Phase A inserisce e commita, Phase B trova il record esistente e lo aggiorna (non inserisce un secondo record, il branch `else` non viene eseguito).

**NOTA sulla relationship**: Il nome dell'attributo Python `scadenza_contratto` in `Documento` rimane invariato (è il nome dell'attributo, non della tabella). MA il tipo e la stringa `relationship(...)` devono essere aggiornati — vedi Task 2c Step 6.

- [ ] **Step 2: Elimina il vecchio file**

```bash
rm /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend/app/models/scadenza_contratto.py
```

---

## Task 2b — Rinomina schema

**Files:**
- Create: `backend/app/schemas/scadenza.py`
- Delete: `backend/app/schemas/scadenza_contratto.py`

- [ ] **Step 1: Crea `backend/app/schemas/scadenza.py`**

```python
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ScadenzaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int | None = None
    contratto_id: int | None = None
    cliente_id: int
    tipo_scadenza: str = "contratto"
    descrizione: str | None = None
    data_inizio: date | None = None
    data_scadenza: date | None = None
    durata: str | None = None
    rinnovo_automatico: bool | None = None
    preavviso_disdetta: str | None = None
    canone: str | None = None
    parti_coinvolte: list[str] | None = None
    clausole_chiave: list[str] | None = None
    confidence_score: float
    verificato: bool
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 2: Elimina il vecchio schema**

```bash
rm /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend/app/schemas/scadenza_contratto.py
```

---

## Task 2c — Aggiorna tutti gli import nel backend

**Files:**
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/api/dashboard.py`
- Modify: `backend/app/api/documenti.py`
- Modify: `backend/app/api/contratti.py`
- Modify: `backend/app/api/chat.py`
- Modify: `backend/app/api/google_calendar.py` (se usa ScadenzaContratto)
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Aggiorna `backend/app/models/__init__.py`**

Cambia:
```python
from .scadenza_contratto import ScadenzaContratto
```
In:
```python
from .scadenza import Scadenza
```

E in `__all__`: sostituisci `"ScadenzaContratto"` con `"Scadenza"`.

- [ ] **Step 2: Aggiorna `backend/app/api/dashboard.py`**

Cambia:
```python
from app.models.scadenza_contratto import ScadenzaContratto
```
In:
```python
from app.models.scadenza import Scadenza
```

Poi sostituisci TUTTE le occorrenze di `ScadenzaContratto` → `Scadenza` nel file.

- [ ] **Step 3: Aggiorna `backend/app/api/chat.py`**

```python
# Da:
from app.models.scadenza_contratto import ScadenzaContratto
# A:
from app.models.scadenza import Scadenza
```

Sostituisci tutte le occorrenze `ScadenzaContratto` → `Scadenza`.

- [ ] **Step 4: Controlla `backend/app/api/google_calendar.py`**

```bash
grep -n "ScadenzaContratto\|scadenza_contratto" backend/app/api/google_calendar.py
```

Se presente, aggiorna gli import. Se assente, salta.

- [ ] **Step 5: Aggiorna `backend/tests/conftest.py`**

```python
# Da:
from app.models.scadenza_contratto import ScadenzaContratto  # noqa: F401 — registers table
# A:
from app.models.scadenza import Scadenza  # noqa: F401 — registers table
```

- [ ] **Step 6: Aggiorna la relationship in `backend/app/models/documento.py` (riga 194)**

Cambia:
```python
scadenza_contratto: Mapped[Optional["ScadenzaContratto"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
    "ScadenzaContratto",
    back_populates="documento",
    uselist=False,
    cascade="all, delete-orphan",
)
```
In:
```python
scadenza_contratto: Mapped[Optional["Scadenza"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
    "Scadenza",
    back_populates="documento",
    uselist=False,
    cascade="all, delete-orphan",
)
```
**ATTENZIONE**: Se non fatto, l'app crasha all'avvio con `InvalidRequestError: mapper 'Mapper[Scadenza(...)]' has no property 'documento'`.

- [ ] **Step 7: Aggiorna `_execute_calendar_action` in `backend/app/api/chat.py`**

La funzione `_execute_calendar_action` (riga ~133) contiene una query diretta a `ScadenzaContratto`:
```python
scadenza = db.query(ScadenzaContratto).filter(ScadenzaContratto.id == scadenza_id).first()
```
Deve diventare:
```python
scadenza = db.query(Scadenza).filter(Scadenza.id == scadenza_id).first()
```
Verifica che il Task 2c Step 3 abbia già aggiornato l'import in cima al file. Se l'import `from app.models.scadenza import Scadenza` è già presente, non aggiungere duplicati.

---

## Task 2d — Aggiorna _upsert_scadenza_from_contratto in contratti.py

**Files:**
- Modify: `backend/app/api/contratti.py`

- [ ] **Step 1: Aggiorna import e logica**

Nel file `backend/app/api/contratti.py`, aggiorna la funzione `_upsert_scadenza_from_contratto`:

```python
def _upsert_scadenza_from_contratto(db: Session, contratto: Contratto) -> None:
    """Auto-create/update a scadenza record from a manual contract."""
    from app.models.scadenza import Scadenza

    existing = db.query(Scadenza).filter(
        Scadenza.contratto_id == contratto.id
    ).first()

    if contratto.data_fine is None:
        if existing:
            db.delete(existing)
        return

    if existing:
        existing.data_inizio = contratto.data_inizio
        existing.data_scadenza = contratto.data_fine
        existing.tipo_scadenza = "canone"
        existing.confidence_score = 1.0
        existing.verificato = True
    else:
        scadenza = Scadenza(
            contratto_id=contratto.id,
            cliente_id=contratto.cliente_id,
            documento_id=None,
            tipo_scadenza="canone",
            data_inizio=contratto.data_inizio,
            data_scadenza=contratto.data_fine,
            confidence_score=1.0,
            verificato=True,
        )
        db.add(scadenza)
```

- [ ] **Step 2: Esegui i test per verificare che non ci siano regressioni**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/ -x -q
```

Expected: tutti i test passano

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/scadenza.py backend/app/models/__init__.py \
        backend/app/schemas/scadenza.py \
        backend/app/api/dashboard.py backend/app/api/contratti.py \
        backend/app/api/chat.py backend/app/api/documenti.py \
        backend/tests/conftest.py
git rm backend/app/models/scadenza_contratto.py backend/app/schemas/scadenza_contratto.py
git commit -m "feat: rename ScadenzaContratto→Scadenza, add tipo_scadenza+descrizione fields"
```

---

## Task 3 — Nuovo prompt AI per scadenze generiche

**Files:**
- Modify: `backend/app/ai/prompts.py`

- [ ] **Step 1: Aggiungi la funzione `build_deadline_extraction_prompt` a `prompts.py`**

Alla fine del file, dopo `build_rag_chat_prompt`, aggiungi:

```python
def build_deadline_extraction_prompt(text: str, tipo_documento: str) -> str:
    """Build the prompt for extracting a single deadline from any document type."""
    truncated_text = text[:MAX_CONTRACT_TEXT_CHARS]
    if len(text) > MAX_CONTRACT_TEXT_CHARS:
        truncated_text += "\n[... testo troncato ...]"

    return f"""PERSONA:
Sei un Assistente Fiscale Senior esperto in documentazione italiana.

TASK:
Analizza il testo del documento (tipo: {tipo_documento}) e individua la scadenza più
rilevante, se presente. NON tutti i documenti hanno scadenze — se non c'è nessuna scadenza,
rispondi con "has_deadline": false.

TIPI DI SCADENZA POSSIBILI:
- "pagamento": scadenza per un pagamento (F24, tasse, tributi, bollette)
- "incasso": scadenza per incassare un credito (fatture emesse, note di credito)
- "canone": scadenza di un canone ricorrente (affitto, leasing, abbonamento)
- "adempimento": scadenza per un adempimento burocratico (dichiarazioni, comunicazioni)
- "rinnovo": scadenza per rinnovo di un contratto o servizio
- "generico": altra scadenza non classificabile

TESTO DEL DOCUMENTO:
{truncated_text}

Rispondi SOLO con un JSON valido:
{{
  "has_deadline": true/false,
  "tipo_scadenza": "pagamento|incasso|canone|adempimento|rinnovo|generico",
  "data_scadenza": "YYYY-MM-DD or null",
  "data_inizio": "YYYY-MM-DD or null",
  "importo": "string or null (es. '€500', '€1200/mese')",
  "descrizione": "breve descrizione della scadenza in italiano (max 100 caratteri)",
  "confidence": 0.0-1.0
}}
"""
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/ai/prompts.py
git commit -m "feat: add build_deadline_extraction_prompt for generic deadline extraction"
```

---

## Task 4 — Nuovo extractor generico

**Files:**
- Create: `backend/app/ai/deadline_extractor.py`

- [ ] **Step 1: Scrivi il test**

Crea `backend/tests/test_deadline_extractor.py`:

```python
"""Tests for the generic deadline extractor."""
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from app.ai.deadline_extractor import extract_deadline, DeadlineExtractionResult


def _make_classifier(json_response: dict):
    """Return a mock classifier whose raw_json_call returns json_response."""
    mock = MagicMock()
    mock.raw_json_call.return_value = json_response
    return mock


def test_extract_deadline_with_payment():
    """When LLM returns a payment deadline, result is populated correctly."""
    payload = {
        "has_deadline": True,
        "tipo_scadenza": "pagamento",
        "data_scadenza": "2026-06-16",
        "data_inizio": None,
        "importo": "€1.500",
        "descrizione": "Pagamento F24 secondo acconto IRPEF",
        "confidence": 0.92,
    }
    with patch("app.ai.deadline_extractor.get_classifier", return_value=_make_classifier(payload)):
        result = extract_deadline("testo documento f24", "f24")

    assert result.has_deadline is True
    assert result.tipo_scadenza == "pagamento"
    assert result.data_scadenza == date(2026, 6, 16)
    assert result.importo == "€1.500"
    assert result.confidence == pytest.approx(0.92)


def test_extract_deadline_no_deadline():
    """When LLM returns has_deadline=false, result has has_deadline=False."""
    payload = {"has_deadline": False}
    with patch("app.ai.deadline_extractor.get_classifier", return_value=_make_classifier(payload)):
        result = extract_deadline("testo senza scadenza", "busta_paga")

    assert result.has_deadline is False
    assert result.data_scadenza is None


def test_extract_deadline_never_raises():
    """extract_deadline must return a safe default even if the classifier explodes."""
    with patch("app.ai.deadline_extractor.get_classifier", side_effect=RuntimeError("boom")):
        result = extract_deadline("qualsiasi testo", "altro")

    assert isinstance(result, DeadlineExtractionResult)
    assert result.has_deadline is False


def test_extract_deadline_invalid_date():
    """Malformed date strings must not raise — they become None."""
    payload = {
        "has_deadline": True,
        "tipo_scadenza": "generico",
        "data_scadenza": "not-a-date",
        "data_inizio": None,
        "importo": None,
        "descrizione": "descrizione",
        "confidence": 0.5,
    }
    with patch("app.ai.deadline_extractor.get_classifier", return_value=_make_classifier(payload)):
        result = extract_deadline("testo", "altro")

    assert result.has_deadline is True
    assert result.data_scadenza is None


def test_extract_deadline_confidence_clamped():
    """Confidence values outside [0,1] are clamped."""
    payload = {
        "has_deadline": True,
        "tipo_scadenza": "generico",
        "data_scadenza": "2026-12-31",
        "data_inizio": None,
        "importo": None,
        "descrizione": "test",
        "confidence": 99.0,  # out of range
    }
    with patch("app.ai.deadline_extractor.get_classifier", return_value=_make_classifier(payload)):
        result = extract_deadline("testo", "altro")

    assert result.confidence == 1.0
```

- [ ] **Step 2: Esegui il test per verificare che fallisca**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/test_deadline_extractor.py -x -q
```

Expected: FAIL (ModuleNotFoundError: app.ai.deadline_extractor)

- [ ] **Step 3: Crea `backend/app/ai/deadline_extractor.py`**

```python
"""Generic deadline extraction from any document type."""
import logging
from datetime import date

from app.ai.classifier import get_classifier
from app.ai.prompts import build_deadline_extraction_prompt

logger = logging.getLogger(__name__)


class DeadlineExtractionResult:
    def __init__(
        self,
        has_deadline: bool = False,
        tipo_scadenza: str = "generico",
        data_scadenza: date | None = None,
        data_inizio: date | None = None,
        importo: str | None = None,
        descrizione: str | None = None,
        confidence: float = 0.0,
    ) -> None:
        self.has_deadline = has_deadline
        self.tipo_scadenza = tipo_scadenza
        self.data_scadenza = data_scadenza
        self.data_inizio = data_inizio
        self.importo = importo
        self.descrizione = descrizione
        self.confidence = confidence


def _parse_date(value: object) -> date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def extract_deadline(text: str, tipo_documento: str) -> DeadlineExtractionResult:
    """Extract the most relevant deadline from any document. Never raises."""
    try:
        prompt = build_deadline_extraction_prompt(text, tipo_documento)
        classifier = get_classifier()
        data = classifier.raw_json_call(prompt)

        if not data.get("has_deadline", False):
            return DeadlineExtractionResult(has_deadline=False)

        return DeadlineExtractionResult(
            has_deadline=True,
            tipo_scadenza=data.get("tipo_scadenza", "generico"),
            data_scadenza=_parse_date(data.get("data_scadenza")),
            data_inizio=_parse_date(data.get("data_inizio")),
            importo=data.get("importo"),
            descrizione=data.get("descrizione"),
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.0)))),
        )
    except Exception:
        logger.exception("Deadline extraction failed")
        return DeadlineExtractionResult()
```

- [ ] **Step 4: Esegui i test**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/test_deadline_extractor.py -x -q
```

Expected: tutti i test passano

- [ ] **Step 5: Esegui la suite completa**

```bash
python -m pytest tests/ -x -q
```

Expected: tutti i test passano

- [ ] **Step 6: Commit**

```bash
git add backend/app/ai/deadline_extractor.py backend/tests/test_deadline_extractor.py
git commit -m "feat: generic deadline extractor with tests"
```

---

## Task 5 — Upload endpoint: estrazione scadenze universale

**Files:**
- Modify: `backend/app/api/documenti.py`

Il blocco di contract extraction attuale (linee 257–293) va sostituito con il nuovo flusso dual-phase.

- [ ] **Step 1: Sostituisci il blocco di estrazione in `documenti.py`**

Rimuovi il blocco esistente (da `# --- Contract structured extraction` fino alla riga `logger.exception("Contract extraction failed for documento %d, skipping"...)`).

Sostituiscilo con:

```python
        # --- Fase A: Estrazione scadenze generiche (TUTTI i documenti) ---
        if extracted_text.strip() and documento.cliente_id is not None:
            try:
                from app.ai.deadline_extractor import extract_deadline
                from app.models.scadenza import Scadenza
                deadline = extract_deadline(extracted_text, documento.tipo_documento)
                if deadline.has_deadline and deadline.data_scadenza:
                    scadenza = Scadenza(
                        documento_id=documento.id,
                        cliente_id=documento.cliente_id,
                        tipo_scadenza=deadline.tipo_scadenza,
                        data_inizio=deadline.data_inizio,
                        data_scadenza=deadline.data_scadenza,
                        canone=deadline.importo,
                        descrizione=deadline.descrizione,
                        confidence_score=deadline.confidence,
                    )
                    db.add(scadenza)
                    db.commit()
                    logger.info(
                        "Deadline extracted for documento %d (tipo=%s)",
                        documento.id, deadline.tipo_scadenza,
                    )
            except Exception:
                logger.exception("Deadline extraction failed for documento %d, skipping", documento.id)

        # --- Fase B: Estrazione aggiuntiva contratto (solo is_contratto o tipo==contratto) ---
        should_extract_contract = (
            is_contratto
            or documento.tipo_documento == "contratto"
        )
        if should_extract_contract and documento.cliente_id is not None and extracted_text.strip():
            try:
                from app.ai.contract_extractor import extract_contract_data
                from app.models.scadenza import Scadenza
                extraction = await anyio.to_thread.run_sync(
                    lambda: extract_contract_data(extracted_text)
                )
                if extraction.confidence > 0:
                    existing_scadenza = db.query(Scadenza).filter(
                        Scadenza.documento_id == documento.id
                    ).first()
                    if existing_scadenza:
                        existing_scadenza.tipo_scadenza = "canone"
                        existing_scadenza.durata = extraction.durata
                        existing_scadenza.rinnovo_automatico = extraction.rinnovo_automatico
                        existing_scadenza.preavviso_disdetta = extraction.preavviso_disdetta
                        existing_scadenza.parti_coinvolte = extraction.parti_coinvolte
                        existing_scadenza.clausole_chiave = extraction.clausole_chiave
                        if extraction.canone:
                            existing_scadenza.canone = extraction.canone
                        if extraction.data_scadenza and not existing_scadenza.data_scadenza:
                            existing_scadenza.data_scadenza = extraction.data_scadenza
                        if extraction.data_inizio and not existing_scadenza.data_inizio:
                            existing_scadenza.data_inizio = extraction.data_inizio
                        db.commit()
                    else:
                        scadenza = Scadenza(
                            documento_id=documento.id,
                            cliente_id=documento.cliente_id,
                            tipo_scadenza="canone",
                            data_inizio=extraction.data_inizio,
                            data_scadenza=extraction.data_scadenza,
                            durata=extraction.durata,
                            rinnovo_automatico=extraction.rinnovo_automatico,
                            preavviso_disdetta=extraction.preavviso_disdetta,
                            canone=extraction.canone,
                            parti_coinvolte=extraction.parti_coinvolte,
                            clausole_chiave=extraction.clausole_chiave,
                            descrizione="Scadenza contratto",
                            confidence_score=extraction.confidence,
                        )
                        db.add(scadenza)
                        db.commit()
                    logger.info(
                        "Contract extraction saved for documento %d (confidence=%.2f)",
                        documento.id, extraction.confidence,
                    )
            except Exception:
                logger.exception("Contract extraction failed for documento %d, skipping", documento.id)
```

**NOTA**: rimuovi anche l'import `from app.models.scadenza_contratto import ScadenzaContratto` se presente nell'upload function — ora i modelli sono importati inline.

- [ ] **Step 2: Esegui i test**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/ -x -q
```

Expected: tutti i test passano

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/documenti.py
git commit -m "feat: dual-phase deadline extraction on upload (generic + contract)"
```

---

## Task 6 — Dashboard: aggiungi badge tipo_scadenza

### 6a — Backend schema + API

**Files:**
- Modify: `backend/app/schemas/dashboard.py`
- Modify: `backend/app/api/dashboard.py`

- [ ] **Step 1: Aggiorna `ScadenzaDashboardOut` in `backend/app/schemas/dashboard.py`**

Aggiungi due campi:
```python
tipo_scadenza: str = "contratto"
descrizione: str | None = None
```

- [ ] **Step 2: Aggiorna `backend/app/api/dashboard.py`**

Nel file `dashboard.py`:

1. Cambia import `ScadenzaContratto` → `Scadenza` (già fatto nel Task 2c)

2. Nelle query `critiche_rows` e `rows` (get_upcoming_deadlines), aggiungi alla select:
```python
Scadenza.tipo_scadenza,
Scadenza.descrizione,
```

3. Nel costruttore di `ScadenzaDashboardOut` (entrambe le occorrenze), aggiungi:
```python
tipo_scadenza=r.tipo_scadenza,
descrizione=r.descrizione,
```

- [ ] **Step 3: Esegui i test**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/ -x -q
```

- [ ] **Step 4: Commit backend**

```bash
git add backend/app/schemas/dashboard.py backend/app/api/dashboard.py
git commit -m "feat: add tipo_scadenza+descrizione to dashboard scadenze response"
```

### 6b — Frontend: tipo badge + descrizione in ScadenzaCard

**Files:**
- Modify: `frontend/src/types/dashboard.ts`
- Modify: `frontend/src/pages/DashboardPage.tsx`

- [ ] **Step 5: Aggiorna `frontend/src/types/dashboard.ts`**

Aggiungi a `ScadenzaDashboard`:
```typescript
tipo_scadenza: string;
descrizione: string | null;
```

- [ ] **Step 6: Aggiungi helper e badge in `DashboardPage.tsx`**

Aggiungi dopo `scadenzaBadgeLabel()`:

```typescript
function tipoBadge(tipo: string): { label: string; className: string } {
  switch (tipo) {
    case 'pagamento':
      return { label: 'Pagamento', className: 'bg-red-100 text-red-700 ring-1 ring-red-200' };
    case 'incasso':
      return { label: 'Incasso', className: 'bg-green-100 text-green-700 ring-1 ring-green-200' };
    case 'canone':
    case 'contratto':
      return { label: 'Canone', className: 'bg-blue-100 text-blue-700 ring-1 ring-blue-200' };
    case 'adempimento':
      return { label: 'Adempimento', className: 'bg-purple-100 text-purple-700 ring-1 ring-purple-200' };
    case 'rinnovo':
      return { label: 'Rinnovo', className: 'bg-orange-100 text-orange-700 ring-1 ring-orange-200' };
    default:
      return { label: 'Scadenza', className: 'bg-gray-100 text-gray-600' };
  }
}
```

In `ScadenzaCard`, nel blocco header (`<div className="min-w-0">`), aggiungi dopo il `<p>` del `file_name`:

```tsx
{/* Tipo badge */}
<span className={`mt-1 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${tipoBadge(s.tipo_scadenza).className}`}>
  {tipoBadge(s.tipo_scadenza).label}
</span>
{/* Descrizione */}
{s.descrizione && (
  <p className="text-xs text-gray-500 mt-1 leading-snug">{s.descrizione}</p>
)}
```

- [ ] **Step 7: Aggiorna il titolo sezione scadenze (Task 9 accorpato qui)**

Nel componente `DashboardPage`, trova la riga:
```tsx
<h2 className="text-xl font-bold text-gray-900">Scadenze Contratti (AI)</h2>
<p className="text-xs text-gray-400 mt-0.5">Estratte automaticamente dai PDF caricati</p>
```

Cambia in:
```tsx
<h2 className="text-xl font-bold text-gray-900">Scadenze (AI)</h2>
<p className="text-xs text-gray-400 mt-0.5">Estratte automaticamente da documenti e contratti</p>
```

- [ ] **Step 8: Commit frontend**

```bash
git add frontend/src/types/dashboard.ts frontend/src/pages/DashboardPage.tsx
git commit -m "feat: tipo_scadenza color badges and descrizione on dashboard deadline cards"
```

---

## Task 7 — Nuova pagina Scadenze

### 7a — Backend: endpoint dedicato

**Files:**
- Create: `backend/app/api/scadenze.py`
- Modify: `backend/app/schemas/scadenza.py` (aggiunge ScadenzaListOut)
- Modify: `backend/app/api/__init__.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Aggiungi `ScadenzaListOut` a `backend/app/schemas/scadenza.py`**

```python
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class ScadenzaResponse(BaseModel):
    # ... (invariato dal Task 2b)


class ScadenzaListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int | None = None
    contratto_id: int | None = None
    cliente_id: int
    cliente_nome: str
    file_name: str = "Contratto manuale"
    tipo_scadenza: str
    descrizione: str | None = None
    data_scadenza: date | None
    data_inizio: date | None = None
    giorni_rimanenti: int | None = None
    canone: str | None = None
    rinnovo_automatico: bool | None = None
    preavviso_disdetta: str | None = None
    confidence_score: float
    verificato: bool
    is_contratto: bool = False
    created_at: datetime
```

- [ ] **Step 2: Scrivi il test per l'endpoint**

Crea `backend/tests/test_scadenze_endpoint.py`:

```python
"""Tests for the /scadenze list endpoint."""
from datetime import date, timedelta

import pytest

from app.models.scadenza import Scadenza


@pytest.fixture()
def fake_scadenza(db, fake_cliente, fake_documento):
    """Create a Scadenza linked to fake_documento."""
    s = Scadenza(
        documento_id=fake_documento.id,
        cliente_id=fake_cliente.id,
        tipo_scadenza="pagamento",
        data_scadenza=date.today() + timedelta(days=10),
        descrizione="Pagamento test",
        confidence_score=0.9,
        verificato=False,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def test_list_scadenze_returns_all(client, fake_scadenza):
    """GET /scadenze returns all deadlines."""
    response = client.get("/api/v1/scadenze")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["tipo_scadenza"] == "pagamento"
    assert data[0]["descrizione"] == "Pagamento test"


def test_list_scadenze_filter_tipo(client, fake_scadenza):
    """Filtering by tipo_scadenza works."""
    response = client.get("/api/v1/scadenze?tipo_scadenza=pagamento")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/api/v1/scadenze?tipo_scadenza=incasso")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_list_scadenze_filter_cliente(client, fake_scadenza, fake_cliente):
    """Filtering by cliente_id works."""
    response = client.get(f"/api/v1/scadenze?cliente_id={fake_cliente.id}")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/api/v1/scadenze?cliente_id=99999")
    assert response.status_code == 200
    assert len(response.json()) == 0


def test_list_scadenze_requires_auth(fake_scadenza):
    """Endpoint requires authentication."""
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    response = c.get("/api/v1/scadenze")
    assert response.status_code == 401
```

- [ ] **Step 3: Esegui il test per verificare che fallisca**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/test_scadenze_endpoint.py -x -q
```

Expected: FAIL (404 o ImportError)

- [ ] **Step 4: Crea `backend/app/api/scadenze.py`**

```python
"""API endpoint for listing and filtering all scadenze."""
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.cliente import Cliente
from app.models.contratto import Contratto
from app.models.documento import Documento
from app.models.scadenza import Scadenza
from app.models.user import User
from app.schemas.scadenza import ScadenzaListOut

router = APIRouter(prefix="/scadenze", tags=["scadenze"])


@router.get("", response_model=list[ScadenzaListOut])
def list_scadenze(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tipo_scadenza: Optional[str] = Query(None),
    cliente_id: Optional[int] = Query(None),
    da_data: Optional[date] = Query(None, description="Scadenze da questa data"),
    a_data: Optional[date] = Query(None, description="Scadenze fino a questa data"),
    verificato: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
) -> list[ScadenzaListOut]:
    """List all scadenze with optional filters."""
    today = date.today()

    rows = (
        db.query(
            Scadenza.id,
            Scadenza.documento_id,
            Scadenza.contratto_id,
            Scadenza.cliente_id,
            Cliente.nome.label("cliente_nome"),
            Cliente.cognome.label("cliente_cognome"),
            Documento.file_name,
            Documento.is_contratto,
            Scadenza.tipo_scadenza,
            Scadenza.descrizione,
            Scadenza.data_scadenza,
            Scadenza.data_inizio,
            Scadenza.canone,
            Scadenza.rinnovo_automatico,
            Scadenza.preavviso_disdetta,
            Scadenza.confidence_score,
            Scadenza.verificato,
            Scadenza.created_at,
        )
        .join(Cliente, Scadenza.cliente_id == Cliente.id)
        .outerjoin(Documento, Scadenza.documento_id == Documento.id)
        .outerjoin(Contratto, Scadenza.contratto_id == Contratto.id)
    )

    if tipo_scadenza:
        rows = rows.filter(Scadenza.tipo_scadenza == tipo_scadenza)
    if cliente_id is not None:
        rows = rows.filter(Scadenza.cliente_id == cliente_id)
    if da_data is not None:
        rows = rows.filter(Scadenza.data_scadenza >= da_data)
    if a_data is not None:
        rows = rows.filter(Scadenza.data_scadenza <= a_data)
    if verificato is not None:
        rows = rows.filter(Scadenza.verificato == verificato)
    if search:
        term = f"%{search}%"
        rows = rows.filter(
            Cliente.nome.ilike(term) | Cliente.cognome.ilike(term) | Scadenza.descrizione.ilike(term)
        )

    rows = rows.order_by(Scadenza.data_scadenza.asc().nullslast()).offset(skip).limit(limit).all()

    result = []
    for r in rows:
        giorni = (r.data_scadenza - today).days if r.data_scadenza else None
        result.append(
            ScadenzaListOut(
                id=r.id,
                documento_id=r.documento_id,
                contratto_id=r.contratto_id,
                cliente_id=r.cliente_id,
                cliente_nome=f"{r.cliente_nome} {r.cliente_cognome}".strip() if r.cliente_nome else "Non assegnato",
                file_name=r.file_name if r.file_name else "Contratto manuale",
                tipo_scadenza=r.tipo_scadenza,
                descrizione=r.descrizione,
                data_scadenza=r.data_scadenza,
                data_inizio=r.data_inizio,
                giorni_rimanenti=giorni,
                canone=r.canone,
                rinnovo_automatico=r.rinnovo_automatico,
                preavviso_disdetta=r.preavviso_disdetta,
                confidence_score=r.confidence_score,
                verificato=r.verificato,
                is_contratto=r.is_contratto if r.is_contratto is not None else False,
                created_at=r.created_at,
            )
        )
    return result
```

- [ ] **Step 5: Aggiungi il router a `backend/app/api/__init__.py`**

```python
from .scadenze import router as scadenze_router
```

E aggiungilo a `__all__`.

- [ ] **Step 6: Registra il router in `backend/app/main.py`**

```python
from app.api import ..., scadenze_router
...
app.include_router(scadenze_router, prefix="/api/v1")
```

- [ ] **Step 7: Esegui i test**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/ -x -q
```

Expected: tutti i test passano

- [ ] **Step 8: Commit backend**

```bash
git add backend/app/api/scadenze.py backend/app/schemas/scadenza.py \
        backend/app/api/__init__.py backend/app/main.py \
        backend/tests/test_scadenze_endpoint.py
git commit -m "feat: GET /scadenze endpoint with filters + ScadenzaListOut schema"
```

### 7b — Frontend: tipo Scadenza + servizio

**Files:**
- Create: `frontend/src/types/scadenza.ts`
- Create: `frontend/src/services/scadenzeService.ts`

- [ ] **Step 9: Crea `frontend/src/types/scadenza.ts`**

```typescript
export interface Scadenza {
    id: number;
    documento_id: number | null;
    contratto_id: number | null;
    cliente_id: number;
    cliente_nome: string;
    file_name: string;
    tipo_scadenza: string;
    descrizione: string | null;
    data_scadenza: string | null;
    data_inizio: string | null;
    giorni_rimanenti: number | null;
    canone: string | null;
    rinnovo_automatico: boolean | null;
    preavviso_disdetta: string | null;
    confidence_score: number;
    verificato: boolean;
    is_contratto: boolean;
    created_at: string;
}

export interface ScadenzaFilters {
    tipo_scadenza?: string;
    cliente_id?: number;
    da_data?: string;
    a_data?: string;
    verificato?: boolean;
    search?: string;
}
```

- [ ] **Step 10: Crea `frontend/src/services/scadenzeService.ts`**

```typescript
import api from './api';
import type { Scadenza, ScadenzaFilters } from '../types/scadenza';

export const getScadenze = async (filters?: ScadenzaFilters): Promise<Scadenza[]> => {
    const params: Record<string, string | number | boolean> = {};
    if (filters) {
        if (filters.tipo_scadenza) params.tipo_scadenza = filters.tipo_scadenza;
        if (filters.cliente_id !== undefined) params.cliente_id = filters.cliente_id;
        if (filters.da_data) params.da_data = filters.da_data;
        if (filters.a_data) params.a_data = filters.a_data;
        if (filters.verificato !== undefined) params.verificato = filters.verificato;
        if (filters.search) params.search = filters.search;
    }
    const response = await api.get<Scadenza[]>('/scadenze', { params });
    return response.data;
};
```

### 7c — Frontend: pagina ScadenzePage

**Files:**
- Create: `frontend/src/pages/ScadenzePage.tsx`

- [ ] **Step 11: Crea `frontend/src/pages/ScadenzePage.tsx`**

```tsx
import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getScadenze } from '../services/scadenzeService';
import type { Scadenza, ScadenzaFilters } from '../types/scadenza';

const TIPO_OPTIONS = [
    { value: '', label: 'Tutti i tipi' },
    { value: 'pagamento', label: 'Pagamento' },
    { value: 'incasso', label: 'Incasso' },
    { value: 'canone', label: 'Canone' },
    { value: 'adempimento', label: 'Adempimento' },
    { value: 'rinnovo', label: 'Rinnovo' },
    { value: 'generico', label: 'Generico' },
];

function tipoBadge(tipo: string): { label: string; className: string } {
    switch (tipo) {
        case 'pagamento': return { label: 'Pagamento', className: 'bg-red-100 text-red-700' };
        case 'incasso': return { label: 'Incasso', className: 'bg-green-100 text-green-700' };
        case 'canone':
        case 'contratto': return { label: 'Canone', className: 'bg-blue-100 text-blue-700' };
        case 'adempimento': return { label: 'Adempimento', className: 'bg-purple-100 text-purple-700' };
        case 'rinnovo': return { label: 'Rinnovo', className: 'bg-orange-100 text-orange-700' };
        default: return { label: 'Scadenza', className: 'bg-gray-100 text-gray-600' };
    }
}

function urgenzaRowClass(giorni: number | null): string {
    if (giorni === null) return '';
    if (giorni < 0) return 'bg-red-50';
    if (giorni < 7) return 'bg-orange-50';
    if (giorni < 30) return 'bg-yellow-50/50';
    return '';
}

function giorniLabel(giorni: number | null): string {
    if (giorni === null) return '—';
    if (giorni < 0) return `Scaduto da ${Math.abs(giorni)} gg`;
    if (giorni === 0) return 'Oggi';
    return `${giorni} gg`;
}

const ScadenzePage: React.FC = () => {
    const navigate = useNavigate();
    const [scadenze, setScadenze] = useState<Scadenza[]>([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState<ScadenzaFilters>({});
    const [search, setSearch] = useState('');
    const [tipoFilter, setTipoFilter] = useState('');
    const [soloNonVerificati, setSoloNonVerificati] = useState(false);

    const fetchScadenze = useCallback(async () => {
        setLoading(true);
        try {
            const activeFilters: ScadenzaFilters = {};
            if (tipoFilter) activeFilters.tipo_scadenza = tipoFilter;
            if (soloNonVerificati) activeFilters.verificato = false;
            if (search) activeFilters.search = search;
            const data = await getScadenze(activeFilters);
            setScadenze(data);
        } catch (err) {
            console.error('Errore caricamento scadenze:', err);
        } finally {
            setLoading(false);
        }
    }, [tipoFilter, soloNonVerificati, search]);

    useEffect(() => {
        fetchScadenze();
    }, [fetchScadenze]);

    return (
        <div className="p-8 space-y-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Scadenze</h1>
                    <p className="text-gray-500 mt-1">
                        {scadenze.length} scadenz{scadenze.length === 1 ? 'a' : 'e'} totali
                    </p>
                </div>
            </div>

            {/* Barra filtri */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex flex-wrap gap-3 items-center">
                {/* Ricerca */}
                <input
                    type="text"
                    placeholder="Cerca cliente o descrizione..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm flex-1 min-w-[200px] focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
                {/* Tipo */}
                <select
                    value={tipoFilter}
                    onChange={(e) => setTipoFilter(e.target.value)}
                    className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                    {TIPO_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                </select>
                {/* Solo non verificati */}
                <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={soloNonVerificati}
                        onChange={(e) => setSoloNonVerificati(e.target.checked)}
                        className="rounded"
                    />
                    Solo non verificate
                </label>
            </div>

            {/* Tabella */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {loading ? (
                    <div className="flex items-center justify-center p-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                    </div>
                ) : scadenze.length === 0 ? (
                    <div className="p-12 text-center text-gray-500">
                        <p className="font-medium">Nessuna scadenza trovata.</p>
                        <p className="text-sm mt-1">Prova a modificare i filtri.</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="bg-gray-50/50 text-gray-400 text-[10px] uppercase font-bold tracking-widest">
                                    <th className="px-5 py-4">Cliente</th>
                                    <th className="px-5 py-4">Tipo</th>
                                    <th className="px-5 py-4">Descrizione</th>
                                    <th className="px-5 py-4">Data Scadenza</th>
                                    <th className="px-5 py-4">Giorni</th>
                                    <th className="px-5 py-4">Importo</th>
                                    <th className="px-5 py-4">Stato</th>
                                    <th className="px-5 py-4">Documento</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                                {scadenze.map((s) => {
                                    const badge = tipoBadge(s.tipo_scadenza);
                                    return (
                                        <tr
                                            key={s.id}
                                            className={`hover:bg-gray-50/50 transition-colors cursor-pointer ${urgenzaRowClass(s.giorni_rimanenti)}`}
                                            onClick={() => navigate(`/documenti?cliente_id=${s.cliente_id}`)}
                                        >
                                            <td className="px-5 py-3 text-sm font-medium text-gray-900">{s.cliente_nome}</td>
                                            <td className="px-5 py-3">
                                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${badge.className}`}>
                                                    {badge.label}
                                                </span>
                                            </td>
                                            <td className="px-5 py-3 text-sm text-gray-600 max-w-xs truncate">{s.descrizione || '—'}</td>
                                            <td className="px-5 py-3 text-sm text-gray-600">
                                                {s.data_scadenza
                                                    ? new Date(s.data_scadenza).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
                                                    : '—'}
                                            </td>
                                            <td className="px-5 py-3">
                                                <span className={`text-xs font-semibold ${s.giorni_rimanenti !== null && s.giorni_rimanenti < 0 ? 'text-red-600' : s.giorni_rimanenti !== null && s.giorni_rimanenti < 7 ? 'text-orange-600' : 'text-gray-500'}`}>
                                                    {giorniLabel(s.giorni_rimanenti)}
                                                </span>
                                            </td>
                                            <td className="px-5 py-3 text-sm text-gray-600">{s.canone || '—'}</td>
                                            <td className="px-5 py-3">
                                                {s.verificato ? (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-50 text-green-700">
                                                        Verificata
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-50 text-amber-600">
                                                        Non verificata
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-5 py-3 text-xs text-gray-400 max-w-[150px] truncate" title={s.file_name}>
                                                {s.file_name}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default ScadenzePage;
```

### 7d — Routing e sidebar

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/layouts/AppLayout.tsx`

- [ ] **Step 12: Aggiungi route in `App.tsx`**

```tsx
import ScadenzePage from './pages/ScadenzePage';
// ...
<Route path="/scadenze" element={<ScadenzePage />} />
```

- [ ] **Step 13: Aggiungi voce sidebar in `AppLayout.tsx`**

Aggiungi dopo l'item "Dashboard" e prima di "Clienti" nell'array `navItems`:

```tsx
{
    label: 'Scadenze',
    to: '/scadenze',
    icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
    ),
},
```

- [ ] **Step 14: Commit frontend completo**

```bash
git add frontend/src/types/scadenza.ts frontend/src/services/scadenzeService.ts \
        frontend/src/pages/ScadenzePage.tsx \
        frontend/src/App.tsx frontend/src/layouts/AppLayout.tsx
git commit -m "feat: ScadenzePage with filters, tipo badge, sidebar entry, route /scadenze"
```

---

## Task 8 — Chatbot: aggiorna awareness scadenze

**Files:**
- Modify: `backend/app/api/chat.py`

- [ ] **Step 1: Aggiorna keywords e testo strutturato in `chat.py`**

1. Aggiungi keywords alla set `_SCADENZA_KEYWORDS`:
```python
_SCADENZA_KEYWORDS = {
    "scadenza", "scadenze", "scade", "scaduto", "scaduti",
    "contratto", "contratti", "rinnovo", "rinnova",
    "disdetta", "preavviso", "canone", "affitto",
    "locazione", "clausola", "clausole", "decorrenza",
    "durata", "parti", "contraenti",
    # Nuove keyword per scadenze universali:
    "pagamento", "incasso", "fattura", "f24", "tributo",
    "bolletta", "adempimento", "tassa", "imposta",
}
```

2. In `_get_scadenze_context()`, aggiorna il formato della riga per includere tipo e descrizione:

```python
parts = [
    f"- [Scadenza ID: {sc.id}] Tipo: {sc.tipo_scadenza} | "
    f"Cliente: {cliente_full} | Documento: {doc_label} ({doc_ref})"
]
if sc.descrizione:
    parts.append(f"  Descrizione: {sc.descrizione}")
if sc.data_inizio:
    parts.append(f"  Inizio: {sc.data_inizio}")
if sc.data_scadenza:
    parts.append(f"  Scadenza: {sc.data_scadenza}")
if sc.durata:
    parts.append(f"  Durata: {sc.durata}")
if sc.canone:
    parts.append(f"  Importo: {sc.canone}")
# ... resto invariato
```

- [ ] **Step 2: Esegui i test**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/ -x -q
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/chat.py
git commit -m "feat: chatbot — add payment/tax keywords, show tipo+descrizione in scadenze context"
```

---

## Task 9 — Verifica finale e commit generale

- [ ] **Step 1: Verifica suite test completa**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal/backend
python -m pytest tests/ -v
```

Expected: tutti i test passano, nessun warning critico.

- [ ] **Step 2: Verifica che non ci siano import residui a ScadenzaContratto**

```bash
grep -rn "ScadenzaContratto\|scadenza_contratto" \
    backend/app/ backend/tests/ \
    --include="*.py"
```

Expected: nessun risultato (o solo commenti / file eliminati)

- [ ] **Step 3: Commit finale**

```bash
cd /mnt/c/Users/marco/OneDrive/Desktop/DocuFiscal
git add .
git commit -m "feat: universal deadline extraction, typed badges, scadenze page

- Rename scadenze_contratto→scadenze with tipo_scadenza+descrizione
- Generic deadline extractor on all document uploads
- Contract extractor enriches with clauses/parties on contracts only
- Dashboard: color badges per deadline type, updated subtitle
- New /scadenze page with tipo filter, urgency row colors, sidebar entry
- Chatbot: payment/tax keywords, tipo+descrizione in structured context"
git push origin main
```

---

## Checklist di verifica manuale (post-deploy)

1. Upload PDF fattura → badge verde "Incasso" in dashboard
2. Upload PDF F24 → badge rosso "Pagamento" in dashboard
3. Upload PDF contratto → badge blu "Canone", dati clausole presenti
4. Contratto manuale con data_fine → badge blu "Canone"
5. Pagina `/scadenze` → tutte le scadenze visibili, filtri funzionanti
6. Chat "ci sono pagamenti in scadenza?" → risponde correttamente
7. Sidebar mostra voce "Scadenze" con icona calendario
