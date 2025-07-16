# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from decimal import Decimal # Import Decimal
from typing import Dict # Import Dict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --- Core Application Settings ---
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # --- LLM Settings ---
    OPENAI_API_KEY: str
    # This will be the DEFAULT model if not specified per agent
    DEFAULT_OPENAI_MODEL_NAME: str #= "gpt-4o-mini" # Renamed from OPENAI_MODEL_NAME

    # NEW: LLM Pricing Configuration
    # This can be loaded from an environment variable as a JSON string,
    # or defined directly with defaults, or loaded from a separate JSON/YAML file.
    # For simplicity, we'll make it a JSON string loaded from env.
    # Example JSON: {"gpt-4o-mini": {"prompt": 0.15, "completion": 0.60}, "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00}}
    LLM_PRICING: Dict[str, Dict[str, Decimal]] = {
        "gpt-4o-mini": {"prompt": Decimal("0.15"), "completion": Decimal("0.60")},
        "gpt-4-turbo": {"prompt": Decimal("10.00"), "completion": Decimal("30.00")},
        "gpt-4": {"prompt": Decimal("30.00"), "completion": Decimal("60.00")},
        "gpt-3.5-turbo-0125": {"prompt": Decimal("0.50"), "completion": Decimal("1.50")},
    }

settings = Settings()

# NOTE: If loading LLM_PRICING from an environment variable (e.g., LLM_PRICING_JSON),
# you'd need a Pydantic validator to parse the JSON string into the Dict[str, Dict[str, Decimal]] format.
# For now, defining it directly with defaults is simplest for demonstration,
# but for production, externalizing this to a file or a complex ENV var is common.