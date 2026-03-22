import asyncio
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.ai.vector_store import vector_store
from app.ai import text_extraction_service
import anyio

async def reindex_all():
    db = SessionLocal()
    try:
        documenti = db.query(Documento).all()
        print(f"Found {len(documenti)} documents to index.")
        
        for doc in documenti:
            print(f"Indexing document {doc.id}: {doc.file_name}...")
            
            # Extract text
            try:
                text = await anyio.to_thread.run_sync(
                    text_extraction_service.extract_text, doc.file_path, doc.mime_type
                )
                
                if text.strip():
                    success = await vector_store.add_document(
                        text=text,
                        document_id=doc.id,
                        file_name=doc.file_name,
                        cliente_id=doc.cliente_id,
                        macro_categoria=doc.macro_categoria,
                        anno_competenza=doc.anno_competenza
                    )
                    if success:
                        print(f"  Successfully indexed {doc.id}")
                    else:
                        print(f"  Failed to index {doc.id}")
                else:
                    print(f"  No text extracted for {doc.id}")
            except Exception as e:
                print(f"  Error extracting text for {doc.id}: {e}")
                
        print("Re-indexing complete.")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(reindex_all())
