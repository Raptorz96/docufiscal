import chromadb
from pathlib import Path
import os
import sys

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from app.core.config import settings

def check_db():
    chroma_path = str(Path(settings.STORAGE_ROOT).parent / "chroma_db")
    print(f"Checking DB at: {chroma_path}")
    
    if not os.path.exists(chroma_path):
        print("DB path does not exist!")
        return

    client = chromadb.PersistentClient(path=chroma_path)
    collections = client.list_collections()
    print(f"Collections found: {[c.name for c in collections]}")
    
    if "documenti_rag" in [c.name for c in collections]:
        col = client.get_collection("documenti_rag")
        count = col.count()
        print(f"Items in 'documenti_rag': {count}")
        if count > 0:
            peek = col.peek(1)
            print(f"Peek at first item: {peek['ids']}")
    else:
        print("'documenti_rag' collection not found!")

if __name__ == "__main__":
    check_db()
