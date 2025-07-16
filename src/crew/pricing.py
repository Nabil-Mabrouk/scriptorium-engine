# src/crew/pricing.py
from decimal import Decimal
from src.core.config import settings # Import the settings object

# REMOVE THE ENTIRE MODEL_PRICING DICTIONARY BLOCK

def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    """Calculates the cost of an LLM call based on token usage."""
    # Get pricing from the global settings object
    pricing = settings.LLM_PRICING.get(model_name)
    if not pricing:
        # Fallback for unknown models to avoid errors
        print(f"⚠️ Warning: Pricing not found for model '{model_name}'. Cost will be 0.0.")
        return Decimal("0.0")

    # Your previously discussed fix for negative tokens:
    if prompt_tokens < 0 or completion_tokens < 0:
        # This should ideally be caught upstream or indicate an issue with LLM usage reporting.
        print(f"⚠️ Warning: Negative token counts received for model '{model_name}'. Prompt: {prompt_tokens}, Completion: {completion_tokens}. Setting cost to 0.0.")
        return Decimal("0.0") # Return 0.0 for invalid inputs

    prompt_cost = (Decimal(prompt_tokens) / Decimal(1_000_000)) * pricing["prompt"]
    completion_cost = (Decimal(completion_tokens) / Decimal(1_000_000)) * pricing["completion"]

    return prompt_cost + completion_cost