from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Sistema Tickets Competencia - Starter"
    app_env: str = "local"
    app_port: int = 8000
    demo_auth_enabled: bool = True
    database_url: str = "postgresql+psycopg2://tickets_user:tickets_pass@localhost:5432/tickets_db"
    storage_root: str = "./storage/files"
    inbound_path: str = "./data/inbound"
    archive_path: str = "./data/inbound/ARCHIVE"
    error_path: str = "./data/inbound/ERROR"
    max_upload_bytes: int = 15 * 1024 * 1024
    allowed_extensions: str = "pdf,jpg,jpeg,png"

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    @property
    def allowed_extensions_list(self) -> list[str]:
        return [e.strip().lower() for e in self.allowed_extensions.split(",") if e.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
