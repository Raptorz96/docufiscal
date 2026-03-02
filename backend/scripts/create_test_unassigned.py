import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.models.documento import Documento, TipoDocumento
from app.storage import storage_service
from fastapi import UploadFile
import io

def create_unassigned_doc():
    db = SessionLocal()
    try:
        # Create a dummy file in storage
        dummy_content = b"Dummy PDF content for manual assignment test"
        dummy_file = UploadFile(
            filename="test_unassigned.pdf",
            file=io.BytesIO(dummy_content)
        )
        
        # Save as unassigned
        file_path, file_size = storage_service.save_file(dummy_file, None, None)
        
        doc = Documento(
            cliente_id=None,
            contratto_id=None,
            tipo_documento=TipoDocumento.altro,
            file_name="test_unassigned.pdf",
            file_path=file_path,
            file_size=file_size,
            mime_type="application/pdf",
            verificato_da_utente=False,
            note="Documento creato per test assignment manuale"
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        print(f"Created unassigned document ID: {doc.id}")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_unassigned_doc()
