import ollama

def generate_answer(question, resume_data):
    prompt = f"""
You are a helpful assistant helping to fill job application forms.

Resume:
{resume_data}

Question:
{question}

Answer concisely and professionally.
"""
    response = ollama.chat(
        model="llama2",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response['message']['content']
