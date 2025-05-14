# import json
# import requests
#
# def test_openwebui_api():
#     with open("config.json", "r") as f:
#         config = json.load(f)
#     print("Loaded config:", config)
#     url = config["OPENWEBUI_API_URL"]
#     api_key = config["OPENWEBUI_API_KEY"]
#     model = config["OPENWEBUI_MODEL"]
#
#     headers = {
#         "Authorization": f"Bearer {api_key}",
#         "Content-Type": "application/json"
#     }
#     print("Headers:", headers)
#     payload = {
#         "model": model,
#         "messages": [
#             {"role": "user", "content": "Hello! Can you confirm you are working?"}
#         ]
#     }
#     print("Payload:", payload)
#     try:
#         print("Sending request to:", url)
#         response = requests.post(url, headers=headers, json=payload, timeout=30)
#         print("Received response, status code:", response.status_code)
#         response.raise_for_status()
#         data = response.json()
#         print("OpenWebUI API response:", data)
#         print("Assistant says:", data["choices"][0]["message"]["content"])
#     except Exception as e:
#         print("❌ OpenWebUI API test failed:", e)
#
# test_openwebui_api()







import requests
import json

# API URL and key from CodersBoutique
API_URL = "https://owui.codersboutique.com/api/chat/completions"  # The API endpoint for chatting
API_KEY = "sk-932d60c64d98493494f023fc2c20a564"  # Replace with your actual API key

# Payload to send to the API
payload = {
    "model": "gemma3",  # Specify the Gemma3 model version (adjust if needed)
    "messages": [
        {"role": "user", "content": "Hello! Can you confirm you are working?"}
    ],
    "stream": False
}

# Set headers for the request
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Send request to the API
response = requests.post(API_URL, headers=headers, data=json.dumps(payload))

# Check the response
if response.status_code == 200:
    print("Response from OpenWebUI API:")
    print(response.json())
else:
    print(f"Failed to connect. Status code: {response.status_code}")
    print(response.text)



