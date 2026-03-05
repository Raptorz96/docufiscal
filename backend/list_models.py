import os
import sys

# Add backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google import genai
from app.core.config import settings

def main():
    try:
        client = genai.Client(api_key=settings.AI_API_KEY)
        print("Available models containing 'embed':")
        for m in client.models.list():
            if 'embed' in m.name.lower():
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
