"""
Vector store service for RAG using ChromaDB and sentence-transformers.
"""
import logging
import anyio
from typing import Any, Dict, List, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Singleton class to manage ChromaDB connection and local embeddings.
    """
    _instance: Optional['VectorStore'] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        try:
            # We store the vector DB inside the storage root
            self.chroma_path = str(Path(settings.STORAGE_ROOT).parent / "chroma_db")
            self.client = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(name="documenti_rag")
            
            # Use the requested lightweight model (lazy loaded)
            self.model_name = "all-MiniLM-L6-v2"
            self._model = None
            
            logger.info(f"VectorStore client initialized at {self.chroma_path}")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {e}")
            self.collection = None
            self._model = None

    @property
    def model(self):
        if self._model is None:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully.")
        return self._model

    async def add_document(
        self, 
        text: str, 
        document_id: int,
        file_name: Optional[str] = None,
        cliente_id: Optional[int] = None, 
        macro_categoria: Optional[str] = None, 
        anno_competenza: Optional[int] = None
    ) -> bool:
        """
        Add a document to the vector store with metadata.
        """
        if not self._initialized or self.collection is None or self.model is None:
            logger.error("VectorStore not initialized.")
            return False

        if not text.strip():
            return False

        try:
            # Embeddings generation (blocking)
            embedding = await anyio.to_thread.run_sync(self.model.encode, text)
            
            # Metadata preparation
            metadata = {
                "document_id": document_id,
            }
            if file_name:
                metadata["file_name"] = file_name
            if cliente_id is not None:
                metadata["cliente_id"] = cliente_id
            if macro_categoria:
                metadata["macro_categoria"] = macro_categoria
            if anno_competenza is not None:
                metadata["anno_competenza"] = anno_competenza

            # Upsert document (safe for re-indexing)
            await anyio.to_thread.run_sync(
                lambda: self.collection.upsert(
                    documents=[text],
                    embeddings=[embedding.tolist()],
                    metadatas=[metadata],
                    ids=[str(document_id)]
                )
            )
            
            logger.info(f"Indexed document {document_id} in VectorStore")
            return True
        except Exception as e:
            logger.error(f"Failed to add document {document_id} to VectorStore: {e}")
            return False

    async def update_metadata(
        self,
        document_id: int,
        file_name: Optional[str] = None,
        cliente_id: Optional[int] = None,
        macro_categoria: Optional[str] = None,
        anno_competenza: Optional[int] = None,
    ) -> bool:
        """Update only metadata for an existing document (no re-embedding)."""
        if not self._initialized or self.collection is None:
            logger.error("VectorStore not initialized.")
            return False
        try:
            metadata: Dict[str, Any] = {"document_id": document_id}
            if file_name:
                metadata["file_name"] = file_name
            if cliente_id is not None:
                metadata["cliente_id"] = cliente_id
            if macro_categoria:
                metadata["macro_categoria"] = macro_categoria
            if anno_competenza is not None:
                metadata["anno_competenza"] = anno_competenza

            await anyio.to_thread.run_sync(
                lambda: self.collection.update(
                    ids=[str(document_id)],
                    metadatas=[metadata],
                )
            )
            logger.info(f"Updated metadata for document {document_id} in VectorStore")
            return True
        except Exception as e:
            logger.error(f"Failed to update metadata for document {document_id}: {e}")
            return False

    async def delete_document(self, document_id: int) -> bool:
        """Remove a document from the vector store by ID."""
        if not self._initialized or self.collection is None:
            logger.error("VectorStore not initialized.")
            return False
        try:
            await anyio.to_thread.run_sync(
                lambda: self.collection.delete(ids=[str(document_id)])
            )
            logger.info(f"Deleted document {document_id} from VectorStore")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from VectorStore: {e}")
            return False

    async def search_documents(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None, 
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks using vector similarity and metadata filters.
        """
        if not self._initialized or self.collection is None or self.model is None:
            logger.error("VectorStore not initialized.")
            return []

        try:
            # Embeddings for query
            query_embedding = await anyio.to_thread.run_sync(self.model.encode, query)
            
            # Robust filter handling
            where_filter = filters if filters and len(filters) > 0 else None
            
            # Search with filters
            results = await anyio.to_thread.run_sync(
                lambda: self.collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=n_results,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"]
                )
            )

            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "document_id": int(results["ids"][0][i]),
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i]
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

# Singleton export
vector_store = VectorStore()
