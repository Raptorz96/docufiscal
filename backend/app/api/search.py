from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.ai.embeddings import search_similar_documents
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.documento import Documento
from app.models.user import User
from app.schemas.documento import DocumentoOut

router = APIRouter(prefix="/search", tags=["search"])


class SemanticSearchResult(BaseModel):
    documento: DocumentoOut
    score: float


@router.get("/semantic", response_model=List[SemanticSearchResult])
def semantic_search(
    q: str = Query(..., description="Query for semantic search", min_length=1),
    limit: int = Query(10, ge=1, le=50, description="Max number of results to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SemanticSearchResult]:
    """Semantic search against document content."""
    
    # 1. Ask ChromaDB for most similar vectors
    results = search_similar_documents(query=q, n_results=limit)
    
    if not results:
        return []

    # 2. Extract Document IDs
    doc_ids = [res.document_id for res in results]
    
    # 3. Fetch full Document data from DB
    docs_db = db.query(Documento).filter(Documento.id.in_(doc_ids)).all()
    docs_dict = {d.id: d for d in docs_db}

    # 4. Construct response keeping the order and scores from ChromaDB
    final_output = []
    for res in results:
        doc = docs_dict.get(res.document_id)
        if doc:
            final_output.append(
                SemanticSearchResult(
                    documento=DocumentoOut.model_validate(doc),
                    score=res.score
                )
            )
            
    return final_output
