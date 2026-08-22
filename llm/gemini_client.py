import os
import json
import urllib.request
from pathlib import Path
from google import genai
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        # Ignorer les clés factices ou placeholders
        if api_key and not api_key.startswith("votre_") and len(api_key) > 20:
            try:
                _client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"[LLM WARNING] Impossible d'initialiser le client Gemini: {e}")
        else:
            _client = None
    return _client

MODELS_FALLBACK = [
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-3.6-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash",
]

def ask_ollama(prompt: str) -> str:
    """
    Appelle le modèle LLM local Ollama si le service est actif.
    """
    import socket
    # Test ultra-rapide si le port Ollama 11434 est ouvert (< 0.2s)
    try:
        with socket.create_connection(('127.0.0.1', 11434), timeout=0.2):
            pass
    except Exception:
        return None

    url = "http://localhost:11434/api/generate"
    models_to_try = ["llama3.2:1b", "llama3.2", "mistral", "llama3"]
    
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=8) as response:
                res_json = json.loads(response.read().decode('utf-8'))
                res_text = res_json.get("response", "").strip()
                if res_text:
                    print(f"[LLM OLLAMA SUCCESS] Réponse générée avec le modèle local Ollama: {model_name}")
                    return res_text
        except Exception:
            continue
    return None

def ask_gemini(prompt: str, fallback_default: str = None) -> str:
    # 1. Priorité au LLM local Ollama (100% gratuit, local, sans quota)
    ollama_res = ask_ollama(prompt)
    if ollama_res:
        return ollama_res

    # 2. Secours Gemini API (si Ollama indisponible)
    client = get_client()
    if client:
        for model_name in MODELS_FALLBACK:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                err_str = str(e)
                print(f"[LLM WARNING] Modèle Gemini {model_name} indisponible : {err_str[:120]}")
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota" in err_str or "404" in err_str:
                    continue

    print("[LLM WARNING] Quota LLM épuisé ou indisponible. Utilisation du fallback déterministe.")
    return fallback_default or '{"event_type": "contrat", "justification": "Évaluation basée sur les règles métier et les garanties contractuelles.", "anomalies": []}'



