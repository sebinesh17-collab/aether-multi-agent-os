from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Aether Multi-Agent OS"
    app_env: str = "production"
    app_base_url: str = "http://localhost:8080"
    api_prefix: str = "/api"
    jwt_secret: str
    jwt_expire_minutes: int = 720
    vault_master_key: str
    owner_email: str = "owner@example.com"
    owner_password: str = ""
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    upload_dir: str = "/data/uploads"
    artifact_dir: str = "/data/artifacts"
    max_upload_mb: int = 100
    min_tasks_per_project: int = 1000
    max_tasks_per_project: int = 5000
    worker_concurrency: int = 2
    default_provider: str = "openai"
    default_model: str = "gpt-4.1"
    llm_timeout_seconds: int = 120
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    firebase_storage_bucket: str = ""
    firebase_service_account_json: str = ""
    sandbox_enabled: bool = False
    sandbox_api_url: str = ""
    sandbox_api_token: str = ""
    sandbox_timeout_seconds: int = 60
    cors_origins: str = "http://localhost:8080"
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

@lru_cache
def get_settings(): return Settings()
settings = get_settings()
