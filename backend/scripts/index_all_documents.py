import os
import sys

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.documento import Documento
from app.ai.text_extraction import text_extraction_service
from app.ai.embeddings import index_document
from app.storage import storage_service

def main():
    db = SessionLocal()
    try:
        documenti = db.query(Documento).all()
        print(f"Found {len(documenti)} documents to index.")

        for doc in documenti:
            print(f"Processing document {doc.id} ({doc.file_name})...")
            try:
                abs_path = storage_service.get_file_path(doc.file_path)
                extracted_text = text_extraction_service.extract_text(abs_path, doc.mime_type)
                
                if extracted_text.strip():
                    meta = {
                        "file_name": doc.file_name,
                        "tipo_documento": doc.tipo_documento,
                        "macro_categoria": doc.macro_categoria
                    }
                    success = index_document(doc.id, extracted_text, metadata=meta)
                    if success:
                        print(f"  -> Successfully indexed document {doc.id}")
                    else:
                        print(f"  -> Failed to index document {doc.id} (embedding returned False)")
                else:
                    print(f"  -> No text extracted for document {doc.id}, skipping index.")
            except Exception as e:
                print(f"  -> Error processing document {doc.id}: {e}")

        print("Indexing process completed.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
