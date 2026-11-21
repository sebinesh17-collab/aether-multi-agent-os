import requests
from sqlalchemy.orm import Session
from .models import Secret
from .vault import decrypt
from .config import settings

SECRET_PREFIX = "provider:"
def get_secret(db: Session, owner_id: int, name: str) -> str | None:
    item = db.query(Secret).filter_by(owner_id=owner_id, name=name).first()
    return decrypt(item.ciphertext) if item else None

def chat(db: Session, owner_id: int, messages: list[dict], model: str | None = None, temperature: float = 0.2) -> str:
    base = get_secret(db, owner_id, "provider:base_url") or "https://api.openai.com/v1"
    key = get_secret(db, owner_id, "provider:api_key")
    selected_model = model or get_secret(db, owner_id, "provider:model") or settings.default_model
    if not key: raise RuntimeError("Configure an AI provider API key in Settings before starting execution")
    url = base.rstrip("/") + "/chat/completions"
    response = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": selected_model, "messages": messages, "temperature": temperature}, timeout=settings.llm_timeout_seconds)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
