# we need create knowledgebase on the name of user
# save the resume

import requests
import json

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

API_KEY = config["OPENWEBUI_API_KEY"]
RESUME_PATH = config["resume_path"]
BASE_URL = config["OPENWEBUI_API_URL"].replace("/api/chat/completions", "")
USER_NAME = "Manisha Walunj"  # Change as needed
MODEL = "gemma3"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

# Step 1: Upload the resume file
with open(RESUME_PATH, "rb") as f:
    files = {"file": f}
    resp = requests.post(f"{BASE_URL}/api/v1/files/", headers=headers, files=files)
    resp.raise_for_status()
    file_id = resp.json()["id"]
    print(f"Uploaded file. File ID: {file_id}")

# Step 2: Query the LLM with the uploaded file directly
payload = {
    "model": MODEL,
    "messages": [{"role": "user", "content": "Tell me about you."}],
    "files": [{"type": "file", "id": file_id}]
}
resp = requests.post(f"{BASE_URL}/api/chat/completions", headers={**headers, "Content-Type": "application/json"}, json=payload)
print(resp.json())

