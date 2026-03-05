from typing import List, Dict, Any, Optional
import logging
import json
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from google import genai

from app.ai.vector_store import vector_store
from app.ai.prompts import build_rag_chat_prompt
from app.api.deps import get_current_user
from app.models.user import User
from app.core.config import settings

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

@router.post("/query", response_model=ChatResponse)
async def chat_query_endpoint(
    queryByBody: ChatQuery = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    RAG-based chat endpoint.
    Retrieves context from VectorStore and generates a response.
    """
    query = queryByBody.query
    filters = queryByBody.filters
    
    # 1. Search VectorStore for relevant context
    active_filters = {k: v for k, v in filters.items() if v is not None} if filters else None
    if not active_filters: active_filters = None

    context_chunks = await vector_store.search_documents(
        query=query,
        filters=active_filters,
        n_results=5
    )
    
    # 2. LOG CHUNKS AS REQUESTED BY USER
    print("\n" + "#"*80)
    print("#" + " "*78 + "#")
    print(f"#   RAG CONTEXT RETRIEVED FOR QUERY: '{query[:50]}...'" + " "*(23 - min(53, len(query))) + "#")
    print("#" + " "*78 + "#")
    print("#"*80)
    
    if not context_chunks:
        print("\n!!! NO CHUNKS FOUND IN VECTOR STORE !!!\n")
    else:
        for i, chunk in enumerate(context_chunks):
            doc_id = chunk.get("document_id")
            score = chunk.get("distance")
            text = chunk.get("text")
            meta = chunk.get("metadata", {})
            fname = meta.get("file_name", "UNKNOWN")
            print(f"\n[CHUNK {i+1}] | Doc ID: {doc_id} | File: {fname} | Distance: {score:.4f}")
            print("-" * 40)
            print(text[:1000] + ("..." if len(text) > 1000 else ""))
            print("-" * 40)
    print("\n" + "#"*80 + "\n")
    
    # 3. Prepare AI Prompt
    prompt = build_rag_chat_prompt(query, context_chunks)
    
    try:
        provider = settings.AI_PROVIDER.lower()
        full_answer = ""

        if provider == "gemini":
            # 4a. Call Gemini
            api_key = settings.GEMINI_API_KEY or settings.AI_API_KEY
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=settings.AI_MODEL,
                contents=prompt
            )
            full_answer = response.text
        elif provider == "openai":
            # 4b. Call OpenAI
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
        
        # 5. Extract JSON array of IDs from the response
        # The prompt asks for it after '--- CITATIONS ---'
        referenced_doc_ids = []
        answer = full_answer
        
        if "--- CITATIONS ---" in full_answer:
            parts = full_answer.split("--- CITATIONS ---")
            answer = parts[0].strip()
            citation_text = parts[1].strip()
            try:
                # Find JSON array in the citation text
                import re
                match = re.search(r"\[.*\]", citation_text)
                if match:
                    referenced_doc_ids = json.loads(match.group(0))
            except Exception:
                logger.warning("Failed to parse referenced_doc_ids from AI response.")
        
        # Fallback: if AI didn't return IDs, find them in the text like [ID: 123]
        if not referenced_doc_ids:
            import re
            matches = re.findall(r"\[ID: (\d+)\]", full_answer)
            referenced_doc_ids = list(set(int(m) for m in matches))

        # 6. Build final references list with filenames
        references_list = []
        for doc_id in referenced_doc_ids:
            # Find the corresponding filename from context chunks
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
        import traceback
        print(f"!!! AI CALL FAILED: {str(e)}")
        print(traceback.format_exc())
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
