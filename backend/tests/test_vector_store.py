import pytest
from app.ai.vector_store import VectorStore
import anyio

@pytest.mark.asyncio
async def test_vector_store_singleton():
    vs1 = VectorStore()
    vs2 = VectorStore()
    assert vs1 is vs2

@pytest.mark.asyncio
async def test_vector_store_add_and_search():
    vs = VectorStore()
    
    # Test data
    doc_id = 9999
    text = "Questo è un documento di test per la ricerca vettoriale del sistema DocuFiscal."
    cliente_id = 123
    macro = "Fiscale"
    anno = 2024
    
    # Index document
    success = await vs.add_document(
        text=text,
        document_id=doc_id,
        cliente_id=cliente_id,
        macro_categoria=macro,
        anno_competenza=anno
    )
    assert success is True
    
    # Search without filters
    results = await vs.search_documents(query="docufiscal ricerca", n_results=1)
    assert len(results) > 0
    assert results[0]["document_id"] == doc_id
    
    # Search with matching filter
    results_filtered = await vs.search_documents(
        query="test", 
        filters={"cliente_id": cliente_id},
        n_results=1
    )
    assert len(results_filtered) > 0
    assert results_filtered[0]["document_id"] == doc_id
    
    # Search with non-matching filter
    results_no_match = await vs.search_documents(
        query="test", 
        filters={"cliente_id": 999},
        n_results=1
    )
    assert len(results_no_match) == 0

@pytest.mark.asyncio
async def test_vector_store_search_metadata_types():
    vs = VectorStore()
    
    # Index with specific metadata
    await vs.add_document(
        text="Dati sensibili del 2023",
        document_id=8888,
        anno_competenza=2023
    )
    
    # Filter by int
    results = await vs.search_documents(query="sensibili", filters={"anno_competenza": 2023})
    assert len(results) > 0
    assert results[0]["document_id"] == 8888
