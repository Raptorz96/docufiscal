import requests
import os

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "test_token" # This script assumes a working local dev environment without strict auth for simplicity or uses a known token

def get_headers():
    # Attempt to get token from local storage or env if needed, 
    # but for local dev uvicorn usually runs without complex auth in these test scenarios if configured
    return {"Authorization": "Bearer test"} # Placeholder, adjust if necessary

def test_manual_assignment():
    # 1. Get an unassigned document
    resp = requests.get(f"{BASE_URL}/documenti?unassigned=true", headers=get_headers())
    docs = resp.json()
    if not docs:
        print("No unassigned documents found to test.")
        return

    doc = docs[0]
    doc_id = doc['id']
    old_path = doc['file_path']
    print(f"Testing assignment for Document ID: {doc_id}, Current Path: {old_path}")

    # 2. Get a client to assign to
    resp_clienti = requests.get(f"{BASE_URL}/clienti", headers=get_headers())
    clienti = resp_clienti.json()
    if not clienti:
        print("No clients found to assign to.")
        return
    
    target_cliente = clienti[0]
    target_id = target_cliente['id']
    print(f"Assigning to Client ID: {target_id} ({target_cliente['nome']})")

    # 3. Perform PATCH update
    patch_data = {"cliente_id": target_id}
    resp_patch = requests.patch(f"{BASE_URL}/documenti/{doc_id}", json=patch_data, headers=get_headers())
    
    if resp_patch.status_code == 200:
        updated_doc = resp_patch.json()
        new_path = updated_doc['file_path']
        print(f"SUCCESS: Document updated. New Path: {new_path}")
        
        # 4. Verify physical file relocation (checking relative paths from storage root)
        # Note: the script runs on the same machine, so we can check the storage folder
        storage_root = "../storage/documenti"
        if os.path.exists(os.path.join(storage_root, new_path)):
            print(f"VERIFIED: Physical file exists at new location: {new_path}")
        else:
            print(f"WARNING: Physical file NOT found at {new_path}")
            
        if not os.path.exists(os.path.join(storage_root, old_path)):
            print(f"VERIFIED: Old file at {old_path} was removed.")
        else:
            print(f"WARNING: Old file still exists at {old_path}")
    else:
        print(f"FAILURE: Patch returned {resp_patch.status_code}")
        print(resp_patch.text)

if __name__ == "__main__":
    test_manual_assignment()
