"""
Service for generating text embeddings and interacting with ChromaDB.
"""
import logging
from typing import Any, Dict, List

import chromadb
from chromadb.config import Settings as ChromaSettings
from google import genai
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize ChromaDB Client
# We store the vector DB inside the storage root to persist it alongside files
chroma_path = str(settings.STORAGE_ROOT).replace("documenti", "chroma_db")
try:
    chroma_client = chromadb.PersistentClient(
        path=chroma_path,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    # The collection to store document embeddings
    doc_collection = chroma_client.get_or_create_collection(name="documenti")
    logger.info(f"Initialized ChromaDB at {chroma_path}")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB: {e}")
    doc_collection = None


class SearchResult(BaseModel):
    document_id: int
    score: float
    metadata: Dict[str, Any]


def generate_embedding(text: str) -> List[float]:
    """Generate vector embedding for a given text using Gemini."""
    if not settings.AI_API_KEY:
        logger.warning("AI_API_KEY is missing. Cannot generate embedding.")
        return []

    try:
        client = genai.Client(api_key=settings.AI_API_KEY)
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return []


def index_document(document_id: int, text: str, metadata: Dict[str, Any] = None) -> bool:
    """Generate embedding for the text and store it in ChromaDB."""
    if not doc_collection:
        logger.error("ChromaDB collection is not available.")
        return False

    if not text.strip():
        return False

    embedding = generate_embedding(text)
    if not embedding:
        return False

    try:
        # ChromaDB requires IDs to be strings
        doc_id_str = str(document_id)
        
        # Merge basic metadata
        meta = metadata or {}
        meta["document_id"] = document_id

        # Add or update
        doc_collection.upsert(
            documents=[text],
            embeddings=[embedding],
            metadatas=[meta],
            ids=[doc_id_str]
        )
        logger.info(f"Indexed document {document_id} in ChromaDB")
        return True
    except Exception as e:
        logger.error(f"Failed to index document {document_id}: {e}")
        return False


def search_similar_documents(query: str, n_results: int = 5) -> List[SearchResult]:
    """Search for semantically similar documents."""
    if not doc_collection:
        logger.error("ChromaDB collection is not available.")
        return []

    query_embedding = generate_embedding(query)
    if not query_embedding:
        return []

    try:
        results = doc_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["metadatas", "distances"]
        )

        search_results = []
        if results["ids"] and len(results["ids"]) > 0:
            # results["ids"][0] contains the list of ids for the first query
            for i, doc_id_str in enumerate(results["ids"][0]):
                doc_id = int(doc_id_str)
                # distances in chroma are usually L2 squared or Cosine distance
                # smaller distance = higher similarity. Let's convert to a dummy score.
                distance = results["distances"][0][i]
                score = 1.0 / (1.0 + distance)
                
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                
                search_results.append(
                    SearchResult(
                        document_id=doc_id,
                        score=round(score, 4),
                        metadata=meta
                    )
                )
                
        return search_results
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        return []

def delete_document_embedding(document_id: int) -> bool:
    """Remove a document from the vector index."""
    if not doc_collection:
        return False
        
    try:
        doc_collection.delete(ids=[str(document_id)])
        return True
    except Exception as e:
        logger.error(f"Failed to delete embedding for document {document_id}: {e}")
        return False
