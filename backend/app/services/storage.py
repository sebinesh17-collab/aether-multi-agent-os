import json, tempfile, os
from pathlib import Path
from sqlalchemy.orm import Session
from ..config import settings
from ..providers import get_secret

def upload_to_firebase(db: Session, owner_id: int, local_path: str, destination: str) -> str:
    raw = get_secret(db, owner_id, "firebase:service_account_json") or settings.firebase_service_account_json
    bucket_name = get_secret(db, owner_id, "firebase:storage_bucket") or settings.firebase_storage_bucket
    if not raw or not bucket_name: return ""
    import firebase_admin
    from firebase_admin import credentials, storage
    try: app = firebase_admin.get_app("aether")
    except ValueError:
        data = json.loads(raw)
        app = firebase_admin.initialize_app(credentials.Certificate(data), {"storageBucket": bucket_name}, name="aether")
    bucket = storage.bucket(app=app)
    blob = bucket.blob(destination)
    blob.upload_from_filename(local_path)
    return f"gs://{bucket_name}/{destination}"
