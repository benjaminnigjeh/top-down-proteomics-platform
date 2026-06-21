from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "TDPortal-OS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./tdportal.db"

    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    DATA_DIR: Path = Path("/data")
    UPLOAD_DIR: Path = Path("/data/uploads")
    JOB_DIR: Path = Path("/data/jobs")
    EXAMPLE_DIR: Path = Path("/data/examples")

    MAX_UPLOAD_SIZE_MB: int = 2048
    ALLOWED_EXTENSIONS: list[str] = [".mzml", ".mzxml", ".fasta", ".fa", ".xml", ".json", ".csv", ".tsv"]

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    TOPPIC_BIN: Optional[str] = None
    TOPFD_BIN: Optional[str] = None
    TOPMG_BIN: Optional[str] = None
    MSPATHFINDER_BIN: Optional[str] = None
    FLASHDECONV_BIN: Optional[str] = None

    DEMO_MODE_ENABLED: bool = True

    @property
    def is_toppic_available(self) -> bool:
        from shutil import which
        return bool(self.TOPPIC_BIN and which(self.TOPPIC_BIN)) or bool(which("toppic"))

    @property
    def is_topfd_available(self) -> bool:
        from shutil import which
        return bool(self.TOPFD_BIN and which(self.TOPFD_BIN)) or bool(which("topfd"))

    @property
    def is_mspathfinder_available(self) -> bool:
        from shutil import which
        return bool(self.MSPATHFINDER_BIN and which(self.MSPATHFINDER_BIN)) or bool(which("MSPathFinderT"))

    @property
    def is_flashdeconv_available(self) -> bool:
        from shutil import which
        return bool(self.FLASHDECONV_BIN and which(self.FLASHDECONV_BIN)) or bool(which("FLASHDeconv"))


settings = Settings()
