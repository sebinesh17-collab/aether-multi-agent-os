import requests
from ..config import settings

def execute_remote(command: str, workspace_id: str) -> dict:
    if not settings.sandbox_enabled or not settings.sandbox_api_url or not settings.sandbox_api_token:
        raise RuntimeError("Cloud terminal is disabled. Configure an isolated remote sandbox first.")
    if len(command) > 4000: raise ValueError("Command exceeds 4,000 characters")
    r=requests.post(settings.sandbox_api_url.rstrip("/")+"/execute", headers={"Authorization":f"Bearer {settings.sandbox_api_token}"}, json={"command":command,"workspace_id":workspace_id}, timeout=settings.sandbox_timeout_seconds+10)
    r.raise_for_status(); return r.json()
