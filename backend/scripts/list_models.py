from google import genai
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))
from app.core.config import settings

def list_mods():
    client = genai.Client(api_key=settings.AI_API_KEY)
    try:
        models = client.models.list()
        print("Available models (filtered):")
        for m in models:
            name = m.name
            if "flash" in name.lower() or "pro" in name.lower():
                print(f" - {name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_mods()
