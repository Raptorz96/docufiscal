import requests
import json

BASE_URL = "http://localhost:8000/api/v1/dashboard/scadenze"

def test_scadenze():
    try:
        # Note: This requires a valid token if auth is enabled
        # For simplicity in this environment, I'll check if the endpoint exists and returns 401/403 vs 404
        response = requests.get(BASE_URL)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_scadenze()
