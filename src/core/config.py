# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from decimal import Decimal
from typing import Dict, Any # Make sure Any is imported

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Core Application Settings ---
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Scriptorium-Engine" # Added in general spec
    APP_DESCRIPTION: str = "Automates book writing using AI." # Added in general spec
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000" # NEW: Add this line

    # --- LLM Settings ---
    OPENAI_API_KEY: str
    # This will be the DEFAULT model if not specified per agent
    DEFAULT_OPENAI_MODEL_NAME: str #= "gpt-4o-mini" # Renamed from OPENAI_MODEL_NAME

    # NEW: LLM Pricing Configuration
    LLM_PRICING: Dict[str, Dict[str, Decimal]] = {
        "gpt-4o-mini": {"prompt": Decimal("0.15"), "completion": Decimal("0.60")},
        "gpt-4-turbo": {"prompt": Decimal("10.00"), "completion": Decimal("30.00")},
        "gpt-4": {"prompt": Decimal("30.00"), "completion": Decimal("60.00")},
        "gpt-3.5-turbo-0125": {"prompt": Decimal("0.50"), "completion": Decimal("1.50")},
    }

settings = Settings()