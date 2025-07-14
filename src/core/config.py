# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Load settings from the .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Core Application Settings ---
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # --- CrewAI / LLM Settings ---
    # These are now part of the main settings object to avoid conflicts.
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "o4-mini-2025-04-16"

# Create a single, importable instance of the settings
settings = Settings()