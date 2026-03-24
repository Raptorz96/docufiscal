from typing import List, Dict, Any, Optional
import logging
import json
import re
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from google import genai
from sqlalchemy.orm import Session

from app.ai.vector_store import vector_store
from app.ai.prompts import build_rag_chat_prompt
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.google_token import GoogleToken
from app.models.scadenza_contratto import ScadenzaContratto
from app.models.cliente import Cliente
from app.models.documento import Documento
from app.core.config import settings
from app.services.google_calendar import create_calendar_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatQuery(BaseModel):
    query: str
    history: List[ChatMessage] = []
    filters: Optional[Dict[str, Any]] = None


class ChatReference(BaseModel):
    doc_id: int
    file_name: str


class ChatResponse(BaseModel):
    answer: str
    referenced_doc_ids: List[int] = []
    references: List[ChatReference] = []


_SCADENZA_KEYWORDS = {
    "scadenza", "scadenze", "scade", "scaduto", "scaduti",
    "contratto", "contratti", "rinnovo", "rinnova",
    "disdetta", "preavviso", "canone", "affitto",
    "locazione", "clausola", "clausole", "decorrenza",
    "durata", "parti", "contraenti",
}


def _is_scadenza_query(query: str) -> bool:
    """Return True if the query likely concerns contract deadlines."""
    words = set(query.lower().split())
    return bool(words & _SCADENZA_KEYWORDS)


_CALENDAR_KEYWORDS = {
    "calendario", "calendar", "fissa", "fissare", "fissami",
    "appuntamento", "appuntamenti", "riunione", "riunioni",
    "meeting", "reminder", "promemoria", "ricordami", "segna",
    "segnami", "aggiungi", "prenota", "prenotare",
}


def _is_calendar_query(query: str) -> bool:
    words = set(query.lower().split())
    return bool(words & _CALENDAR_KEYWORDS)


def _get_scadenze_context(db: Session) -> str:
    """Query all scadenze_contratto and format as structured text for the LLM."""
    rows = (
        db.query(
            ScadenzaContratto,
            Cliente.nome.label("cliente_nome"),
            Cliente.cognome.label("cliente_cognome"),
            Documento.file_name,
        )
        .join(Cliente, ScadenzaContratto.cliente_id == Cliente.id)
        .join(Documento, ScadenzaContratto.documento_id == Documento.id)
        .order_by(ScadenzaContratto.data_scadenza.asc().nullslast())
        .all()
    )

    if not rows:
        return ""

    lines = []
    for sc, nome, cognome, file_name in rows:
        cliente_full = f"{nome} {cognome}".strip() if nome else "Sconosciuto"
        parts = [f"- [Scadenza ID: {sc.id}] Cliente: {cliente_full} | Documento: {file_name} (Doc ID: {sc.documento_id})"]
        if sc.data_inizio:
            parts.append(f"  Inizio: {sc.data_inizio}")
        if sc.data_scadenza:
            parts.append(f"  Scadenza: {sc.data_scadenza}")
        if sc.durata:
            parts.append(f"  Durata: {sc.durata}")
        if sc.canone:
            parts.append(f"  Canone: {sc.canone}")
        if sc.rinnovo_automatico is not None:
            parts.append(f"  Rinnovo automatico: {'Sì' if sc.rinnovo_automatico else 'No'}")
        if sc.preavviso_disdetta:
            parts.append(f"  Preavviso disdetta: {sc.preavviso_disdetta}")
        if sc.parti_coinvolte:
            parts.append(f"  Parti: {', '.join(sc.parti_coinvolte)}")
        if sc.clausole_chiave:
            parts.append(f"  Clausole chiave: {'; '.join(sc.clausole_chiave)}")
        lines.append("\n".join(parts))

    return "\n\n".join(lines)


def _execute_calendar_action(db: Session, user_id: int, action: dict) -> dict | None:
    """Execute a calendar action parsed from LLM response."""
    action_type = action.get("type")

    if action_type == "from_scadenza":
        scadenza_id = action.get("scadenza_id")
        if not scadenza_id:
            return None

        scadenza = db.query(ScadenzaContratto).filter(ScadenzaContratto.id == scadenza_id).first()
        if not scadenza or not scadenza.data_scadenza:
            return {"success": False, "error": "Scadenza non trovata o senza data"}

        cliente = db.query(Cliente).filter(Cliente.id == scadenza.cliente_id).first()
        documento = db.query(Documento).filter(Documento.id == scadenza.documento_id).first()
        cliente_nome = f"{cliente.nome} {cliente.cognome}".strip() if cliente else "Sconosciuto"

        result = create_calendar_event(
            db=db,
            user_id=user_id,
            summary=f"Scadenza contratto — {cliente_nome}",
            description=f"Cliente: {cliente_nome}\nDocumento: {documento.file_name if documento else 'N/A'}\nGenerato da DocuFiscal",
            event_date=scadenza.data_scadenza.isoformat(),
        )
        if result:
            return {"success": True, "event_link": result.get("htmlLink")}
        return {"success": False, "error": "Errore creazione evento"}

    elif action_type == "custom":
        summary = action.get("summary", "Appuntamento")
        description = action.get("description", "")
        event_date = action.get("event_date")
        start_dt = action.get("start_datetime")
        end_dt = action.get("end_datetime")

        if not event_date and not start_dt:
            return {"success": False, "error": "Nessuna data specificata"}

        result = create_calendar_event(
            db=db,
            user_id=user_id,
            summary=summary,
            description=description,
            event_date=event_date if not start_dt else None,
            start_datetime=start_dt,
            end_datetime=end_dt,
        )
        if result:
            return {"success": True, "event_link": result.get("htmlLink")}
        return {"success": False, "error": "Errore creazione evento"}

    return None


@router.post("/query", response_model=ChatResponse)
async def chat_query_endpoint(
    queryByBody: ChatQuery = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    RAG-based chat endpoint.
    Retrieves context from VectorStore and generates a response.
    """
    query = queryByBody.query
    filters = queryByBody.filters

    # 1. Search VectorStore for relevant context
    active_filters = {k: v for k, v in filters.items() if v is not None} if filters else None
    if not active_filters:
        active_filters = None

    context_chunks = await vector_store.search_documents(
        query=query,
        filters=active_filters,
        n_results=5
    )

    logger.debug("RAG context: %d chunks retrieved for query '%s'", len(context_chunks), query[:50])

    # 2. Inject contract deadline data if query is scadenza-related
    scadenze_context = ""
    if _is_scadenza_query(query):
        scadenze_context = _get_scadenze_context(db)
        if scadenze_context:
            logger.debug("Injecting scadenze context for query '%s'", query[:50])

    # 3. Determine if Google Calendar is enabled for this user
    calendar_enabled = False
    if _is_calendar_query(query):
        token = db.query(GoogleToken).filter(GoogleToken.user_id == current_user.id).first()
        calendar_enabled = token is not None

    # 4. Prepare AI Prompt
    prompt = build_rag_chat_prompt(
        query, context_chunks,
        scadenze_context=scadenze_context,
        calendar_enabled=calendar_enabled,
    )

    try:
        provider = settings.AI_PROVIDER.lower()
        full_answer = ""

        if provider == "gemini":
            api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=settings.AI_MODEL,
                contents=prompt
            )
            full_answer = response.text
        elif provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=settings.AI_MODEL if "gpt" in settings.AI_MODEL else "gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            full_answer = response.choices[0].message.content
        else:
            raise ValueError(f"Unsupported AI provider for chat: {provider}")

        # 4. Strip CALENDAR_ACTION first (it's always the last block)
        calendar_action_json = None
        working_answer = full_answer
        if "--- CALENDAR_ACTION ---" in full_answer:
            cal_parts = full_answer.split("--- CALENDAR_ACTION ---", 1)
            working_answer = cal_parts[0]
            action_text = cal_parts[1].strip()
            try:
                match = re.search(r"\{.*\}", action_text, re.DOTALL)
                if match:
                    calendar_action_json = json.loads(match.group(0))
            except Exception:
                logger.warning("Failed to parse CALENDAR_ACTION from AI response")

        # 5. Extract CITATIONS
        referenced_doc_ids = []
        answer = working_answer

        if "--- CITATIONS ---" in working_answer:
            parts = working_answer.split("--- CITATIONS ---")
            answer = parts[0].strip()
            citation_text = parts[1].strip()
            try:
                match = re.search(r"\[.*\]", citation_text)
                if match:
                    referenced_doc_ids = json.loads(match.group(0))
            except Exception:
                logger.warning("Failed to parse referenced_doc_ids from AI response.")

        # Fallback: find IDs in the text like [ID: 123]
        if not referenced_doc_ids:
            matches = re.findall(r"\[ID: (\d+)\]", full_answer)
            referenced_doc_ids = list(set(int(m) for m in matches))

        # 6. Execute calendar action and append result to answer
        if calendar_action_json and calendar_enabled:
            calendar_result = _execute_calendar_action(db, current_user.id, calendar_action_json)
            if calendar_result:
                if calendar_result.get("success"):
                    link = calendar_result.get("event_link", "")
                    answer += "\n\n✅ **Evento creato su Google Calendar!**"
                    if link:
                        answer += f" [Apri evento]({link})"
                else:
                    error = calendar_result.get("error", "Errore sconosciuto")
                    answer += f"\n\n⚠️ Non è stato possibile creare l'evento: {error}"

        # 7. Build final references list with filenames
        references_list = []
        for doc_id in referenced_doc_ids:
            file_name_found = f"Documento #{doc_id}"
            for chunk in context_chunks:
                if chunk.get("document_id") == doc_id:
                    meta = chunk.get("metadata", {})
                    file_name_found = meta.get("file_name", file_name_found)
                    break
            references_list.append(ChatReference(doc_id=doc_id, file_name=file_name_found))

        return ChatResponse(
            answer=answer,
            referenced_doc_ids=referenced_doc_ids,
            references=references_list
        )

    except Exception as e:
        logger.exception("Chat completion failed: %s", e)
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
