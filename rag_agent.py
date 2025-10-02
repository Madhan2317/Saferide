import os
import ollama
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load model name from .env (default = llama3.1:8b)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

def rag_chatbot(query):
    """RAG chatbot for helmet/no-helmet detections"""
    prompt = f"""
    You are a Road Safety Assistant chatbot.
    Only answer questions based on helmet and no-helmet detection data.
    If the user asks something outside this scope, reply:
    "I can only answer about helmet detections."

    Question: {query}
    """

    try:
        resp = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp["message"]["content"]

    except Exception as e:
        return f"⚠️ Error using Ollama model {OLLAMA_MODEL}: {e}"
