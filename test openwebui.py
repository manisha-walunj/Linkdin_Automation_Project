import json
import requests

def test_openwebui_api():
    with open("config.json", "r") as f:
        config = json.load(f)
    print("Loaded config:", config)
    url = config["OPENWEBUI_API_URL"]
    api_key = config["OPENWEBUI_API_KEY"]
    model = config["OPENWEBUI_MODEL"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    print("Headers:", headers)
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello! Can you confirm you are working?"}
        ]
    }
    print("Payload:", payload)
    try:
        print("Sending request to:", url)
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print("Received response, status code:", response.status_code)
        response.raise_for_status()
        data = response.json()
        print("OpenWebUI API response:", data)
        print("Assistant says:", data["choices"][0]["message"]["content"])
    except Exception as e:
        print("❌ OpenWebUI API test failed:", e)

test_openwebui_api()


