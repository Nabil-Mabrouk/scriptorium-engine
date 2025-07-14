# src/crew/pricing.py
from decimal import Decimal

# Prices per 1,000,000 tokens
MODEL_PRICING = {
    "gpt-4-turbo-preview": {"prompt": Decimal("10.00"), "completion": Decimal("30.00")},
    "gpt-4-turbo": {"prompt": Decimal("10.00"), "completion": Decimal("30.00")},
    "gpt-4": {"prompt": Decimal("30.00"), "completion": Decimal("60.00")},
    "gpt-3.5-turbo-0125": {"prompt": Decimal("0.50"), "completion": Decimal("1.50")},
}

def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
    """Calculates the cost of an LLM call based on token usage."""
    pricing = MODEL_PRICING.get(model_name)
    if not pricing:
        # Fallback for unknown models to avoid errors
        return Decimal("0.0")
    
    prompt_cost = (Decimal(prompt_tokens) / Decimal(1_000_000)) * pricing["prompt"]
    completion_cost = (Decimal(completion_tokens) / Decimal(1_000_000)) * pricing["completion"]
    
    return prompt_cost + completion_cost