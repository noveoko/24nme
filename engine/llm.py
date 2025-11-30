import requests
import json
import re

def clean_json_response(response_text: str) -> str:
    """
    Helper: Local LLMs often chat ('Here is the JSON...') or wrap code in markdown.
    This strips the markdown to return raw JSON string.
    """
    # Remove markdown code blocks if present
    match = re.search(r"```(?:json)?\s*(.*)\s*```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return response_text.strip()

def call_ollama(system_prompt: str, user_content: str, model: str = "llama3") -> str:
    """
    The concrete implementation of 'my_local_llm_function' using Ollama.
    """
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "stream": False,
        # 'json' format forces the model to output valid JSON (supported in Llama 3)
        "format": "json" 
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        content = result['message']['content']
        return clean_json_response(content)
    except Exception as e:
        print(f"LLM Call Failed: {e}")
        return "{}"