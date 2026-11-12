import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = Field(default="", description="Telegram Bot API Token")
    ADMIN_TELEGRAM_IDS: str = Field(default="", description="Comma-separated Telegram user IDs of admins")

    # Database
    POSTGRES_DB: str = Field(default="btc_tracker_db")
    POSTGRES_USER: str = Field(default="btc_user")
    POSTGRES_PASSWORD: str = Field(default="btc_secure_password_123")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: str = Field(default="")

    # Binance
    BINANCE_API_URL: str = Field(default="https://api.binance.com")
    PRICE_MONITOR_INTERVAL: int = Field(default=5, description="Interval in seconds for price monitoring")

    # Gemini AI
    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash", description="Gemini model name")
    AI_ANALYSIS_INTERVAL_MINUTES: int = Field(default=60, description="Scheduled AI analysis interval in minutes")
    AI_MANUAL_COOLDOWN_MINUTES: int = Field(default=10, description="Cooldown for manual AI analysis in minutes")

    # Application Defaults
    DEFAULT_TIMEZONE: str = Field(default="Asia/Tashkent")
    LOG_LEVEL: str = Field(default="INFO")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str, values) -> str:
        if v and isinstance(v, str) and len(v.strip()) > 0:
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+psycopg2://", 1)
            return v
        data = values.data if hasattr(values, "data") else {}
        user = data.get("POSTGRES_USER", "btc_user")
        password = data.get("POSTGRES_PASSWORD", "btc_secure_password_123")
        host = data.get("POSTGRES_HOST", "localhost")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "btc_tracker_db")
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

    @property
    def admin_ids(self) -> List[int]:
        if not self.ADMIN_TELEGRAM_IDS:
            return []
        ids = []
        for raw_id in self.ADMIN_TELEGRAM_IDS.split(","):
            raw_id = raw_id.strip()
            if raw_id.isdigit():
                ids.append(int(raw_id))
        return ids


settings = Settings()
