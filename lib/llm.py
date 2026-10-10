import os
import json
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Lazy-loaded client — reads key at call time so Streamlit Cloud secrets work
_client = None

def _get_client():
    global _client
    if _client is None:
        # Try os.environ first (works for both .env and Streamlit secrets)
        api_key = os.environ.get("GROQ_API_KEY")
        # Fallback: try st.secrets if running inside Streamlit
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("GROQ_API_KEY")
            except Exception:
                pass
        if api_key and api_key != "your_groq_api_key_here":
            _client = Groq(api_key=api_key)
        else:
            raise Exception("GROQ_API_KEY is missing or invalid. Please set it in .env or Streamlit Secrets.")
    return _client

_selected_model = None

def _get_model(client) -> str:
    global _selected_model
    if _selected_model:
        return _selected_model

    # Check env or Streamlit secrets
    env_model = os.environ.get("GROQ_MODEL")
    if not env_model:
        try:
            import streamlit as st
            env_model = st.secrets.get("GROQ_MODEL")
        except Exception:
            pass

    if env_model:
        _selected_model = env_model
        return _selected_model

    # Candidates in preference order
    candidates = [
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    try:
        available_models = [m.id for m in client.models.list().data]
        for c in candidates:
            if c in available_models:
                _selected_model = c
                return _selected_model
        for m in available_models:
            if not any(skip in m for skip in ["whisper", "guard", "audio"]):
                _selected_model = m
                return _selected_model
    except Exception:
        pass

    _selected_model = "openai/gpt-oss-20b"
    return _selected_model

def call_llm(prompt: str, system: str = "", retries: int = 3, response_format: str = "text") -> str:
    client = _get_client()
    model = _get_model(client)
        
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    
    for attempt in range(retries):
        try:
            kwargs = {
                "messages": messages,
                "model": model,
                "temperature": 0.1,
            }
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}
                
            chat_completion = client.chat.completions.create(**kwargs)
            return chat_completion.choices[0].message.content
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(1)


def classify_content(text: str) -> dict:
    prompt = f"""You are an AI assistant that organizes notes using the PARA method.
Analyze the following text and classify it.
Respond ONLY with a valid JSON object containing exactly these three keys:
- "para": exactly one of "Projects", "Areas", "Resources", or "Archives"
- "tags": a list of relevant string tags (max 5)
- "summary": a one-line summary of the text

Text to analyze:
{text}
"""
    system = "You are a helpful assistant that outputs only valid JSON."
    
    try:
        response = call_llm(prompt, system, response_format="json")
        return json.loads(response)
    except Exception as e:
        print(f"LLM Classification error: {e}")
        return {"para": "Archives", "tags": [], "summary": "Failed to classify"}

def synthesize_answer(context: str, question: str) -> str:
    prompt = f"""You are SecondSelf, answering from the user's personal knowledge base. Use ONLY the provided notes. If the answer isn't in the notes, say so.
Cite sources as [note-id].

Notes:
{context}

Question: {question}
"""
    try:
        return call_llm(prompt, system="You are an expert assistant.", response_format="text")
    except Exception as e:
        print(f"LLM Synthesis error: {e}")
        return f"I encountered an error trying to synthesize an answer: {e}"
