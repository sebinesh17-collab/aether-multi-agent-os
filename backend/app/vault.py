import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from .config import settings

def _key() -> bytes:
    raw = settings.vault_master_key.strip()
    try:
        decoded = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
        if len(decoded) == 32: return decoded
    except Exception: pass
    if len(raw.encode()) >= 32: return raw.encode()[:32]
    raise RuntimeError("VAULT_MASTER_KEY must be a base64-encoded 32-byte key (recommended)")

def encrypt(value: str) -> str:
    nonce = os.urandom(12)
    cipher = AESGCM(_key()).encrypt(nonce, value.encode(), b"aether-secret-v1")
    return base64.urlsafe_b64encode(nonce + cipher).decode()

def decrypt(value: str) -> str:
    raw = base64.urlsafe_b64decode(value.encode())
    return AESGCM(_key()).decrypt(raw[:12], raw[12:], b"aether-secret-v1").decode()
