# src/core/logging.py
import logging
import os # Import os to get environment variables

def configure_logging():
    """
    Configures application-wide logging using Python's standard logging module.
    Log level is determined by the ENVIRONMENT environment variable.
    """
    # Get environment from settings if available, otherwise fallback to os.environ
    # To avoid circular import, we'll directly read from os.environ here.
    # In a real app, you might pass settings.ENVIRONMENT to this function
    # or ensure settings is loaded before this function is called.
    environment = os.getenv("ENVIRONMENT", "development").lower()

    log_level = logging.INFO
    if environment == "development":
        log_level = logging.DEBUG

    # Basic configuration. For production, consider structured logging (e.g., loguru, json logging)
    # and external log management/aggregation.
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler() # Outputs to console (stdout/stderr)
            # logging.FileHandler("app.log") # Uncomment for file logging in specific setups
        ]
    )

    # Suppress chatty loggers from libraries if needed for cleaner output
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("arq").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING) # Set to INFO for DB query logging if debugging
    logging.getLogger("fastapi_limiter").setLevel(logging.WARNING) # Suppress limiter logs unless needed
    logging.getLogger("httpx").setLevel(logging.WARNING) # If using httpx for external calls

    # Ensure circuitbreaker logs are visible if not already
    logging.getLogger("circuitbreaker").setLevel(logging.INFO)

    # Optional: Log a message indicating logging is configured
    logging.getLogger(__name__).info(f"Logging configured for '{environment}' environment at level {logging.getLevelName(log_level)}")