import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # loads OPENAI_API_KEY from .env
client = OpenAI()  # uses env var automatically

def json_chat(model: str, system: str, user: str) -> dict:
    """Call Chat Completions and parse the assistant's JSON."""
    resp = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    text = resp.choices[0].message.content
    return json.loads(text)
