

## Part 1: High-Level Backend Specification (The "Why")

This section outlines the core philosophy and architectural principles that will guide all your future backend projects.

### 1. Project Goal

To establish a standardized, highly reusable, scalable, and resilient backend architecture for AI-powered automation applications, built on modern Python frameworks and best practices. This specification aims to accelerate development, improve code quality, and reduce the learning curve for new team members.

### 2. Core Architectural Principles

*   **Modularity & Separation of Concerns (Hexagonal/Onion Architecture Inspired):**
    *   **Why:** Each component should have a single, well-defined responsibility. This reduces coupling, makes code easier to understand, test, and maintain. Changes in one area (e.g., database) should ideally not necessitate changes in another (e.g., AI logic).
    *   **Implementation:** Clear division into `core`, `domain-specific`, and `external-service-orchestration` layers.
*   **Asynchronous-First Design:**
    *   **Why:** Most modern web applications, especially those interacting with external APIs (like LLMs or other services), are I/O-bound. Asynchronous programming (async/await) allows the server to handle many requests concurrently without blocking, leading to higher throughput and better responsiveness.
    *   **Implementation:** FastAPI, SQLAlchemy's async engine, Redis async client, ARQ for background tasks.
*   **Resilience & Fault Tolerance:**
    *   **Why:** External dependencies (like LLM APIs) can be unreliable (rate limits, downtime, errors). The system must gracefully handle these failures without crashing or accumulating errors.
    *   **Implementation:** Circuit breakers, intelligent retry mechanisms (via ARQ), rate limiting.
*   **Scalability:**
    *   **Why:** Applications must be able to handle increasing load without significant re-architecture. This involves horizontal scaling of both the web server and background workers.
    *   **Implementation:** Stateless FastAPI application, background task queues (ARQ), independent scaling of web and worker processes, robust database.
*   **Observability (Logging, Monitoring, Cost Tracking):**
    *   **Why:** It's crucial to understand what the application is doing, diagnose issues, and monitor resource consumption (especially LLM costs).
    *   **Implementation:** Standard Python `logging`, structured logs, dedicated `RunLog` models for external API usage.
*   **Testability:**
    *   **Why:** Well-tested code is reliable code. A modular design naturally lends itself to easier unit and integration testing.
    *   **Implementation:** Clear service layers, dependency injection.
*   **Data Integrity & Versioning:**
    *   **Why:** Critical data should be consistently stored, and important generated/edited content should have a history.
    *   **Implementation:** SQLAlchemy models, explicit versioning tables for generated content.
*   **Reusability:**
    *   **Why:** Reduce boilerplate, accelerate development of new projects, and maintain consistency.
    *   **Implementation:** Centralized `core` utilities, generalized `orchestration` patterns for external services.

### 3. Standardized Technology Stack

*   **Web Framework:** FastAPI (with Uvicorn) - High performance, Pydantic integration, automatic OpenAPI docs.
*   **Database ORM:** SQLAlchemy 2.0 (Async) - Robust, flexible, widely adopted.
*   **Database Migrations:** Alembic - Essential for managing schema changes.
*   **Data Validation/Serialization:** Pydantic - First-class data validation, integrated with FastAPI.
*   **Background Task Queue:** ARQ (with Redis) - Simple, performant, asynchronous task queue.
*   **Caching/Messaging:** Redis - Used by ARQ, can also be used for caching or pub/sub.
*   **Rate Limiting:** `fastapi-limiter` (with Redis) - API rate limiting.
*   **Circuit Breaker:** `circuitbreaker` library - For external API call resilience.
*   **HTTP Client (Optional but recommended):** `httpx` - Fully async HTTP client.
*   **Python Version:** Python 3.9+ (Leveraging newer features like `Union` syntax `|`).

### 4. High-Level Project Structure

```
.
├── src/
│   ├── core/                  # Core application utilities (reusable across ALL projects)
│   │   ├── __init__.py
│   │   ├── config.py          # Environment settings
│   │   ├── database.py        # SQLAlchemy engine, session factory, Base
│   │   ├── exceptions.py      # Custom exception definitions
│   │   ├── logging.py         # Standardized logging configuration
│   │   ├── schemas.py         # Common API schemas (e.g., TaskStatus, HealthCheck)
│   │   ├── security.py        # Authentication/Authorization boilerplate (e.g., JWT setup)
│   │   └── task_queue.py      # ARQ pool manager
│   │
│   ├── <project_domain_1>/    # Domain-specific module (e.g., 'book_writing', 'invoice_processing')
│   │   ├── __init__.py
│   │   ├── models.py          # SQLAlchemy models for this domain
│   │   ├── schemas.py         # Pydantic schemas for this domain's models
│   │   ├── service.py         # Business logic and database interactions for this domain
│   │   ├── router.py          # FastAPI endpoints for this domain's core CRUD/operations
│   │   └── dependencies.py    # FastAPI dependency functions for this domain
│   │
│   ├── external_services_orchestration/ # General purpose module for interacting with external APIs (LLMs, payment, etc.)
│   │   ├── __init__.py
│   │   ├── agents/            # (Conceptual) Generic interface for external AI agents/processors
│   │   │   ├── __init__.py
│   │   │   └── generic_processor.py # Example: An 'Agent' class that takes instructions & uses LLMs
│   │   ├── models.py          # SQLAlchemy models for run logs (e.g., ExternalServiceRunLog)
│   │   ├── pricing.py         # Cost calculation for external services
│   │   ├── router.py          # FastAPI endpoints for triggering and monitoring external service tasks
│   │   ├── schemas.py         # Pydantic schemas for external service requests/responses/status
│   │   ├── service.py         # Orchestration logic (calls external APIs, updates domain models)
│   │   ├── tasks.py           # ARQ worker functions (callable by the queue)
│   │   └── worker.py          # ARQ worker settings for the background process
│   │
│   └── main.py                # Main FastAPI application entry point
├── .env                       # Environment variables
├── Dockerfile                 # For containerization
├── pyproject.toml             # Project dependencies and metadata
└── alembic/                   # Alembic migration environment
    └── env.py
    └── script.py.mako
    └── versions/
```

### 5. Standardized Workflow for AI/External Service Integration (e.g., LLM Generation)

1.  **Frontend Trigger:** User initiates an action via an API endpoint in `src/external_services_orchestration/router.py`.
2.  **Queue Job:** The router endpoint immediately enqueues a job into `arq` (via `src/core/task_queue.py`) and returns `HTTP 202 Accepted` with a `job_id` (using `src/core/schemas.py::TaskStatus`).
3.  **Worker Picks Up Job:** An `arq` worker process (configured via `src/external_services_orchestration/worker.py`) picks up the job.
4.  **Orchestration Logic:** The worker calls a function in `src/external_services_orchestration/service.py` (e.g., `run_llm_generation`).
5.  **External API Call:** The `service.py` function calls the external API (e.g., OpenAI via a generic `Agent` interface defined in `external_services_orchestration/agents/generic_processor.py`). This call is wrapped by a `circuitbreaker` for resilience.
6.  **Data Updates:** The `service.py` function updates the relevant domain models (e.g., `Project`, `Chapter`) in the database using the service functions from `src/<project_domain_1>/service.py`.
7.  **Logging & Cost Tracking:** Metrics (tokens, cost) are logged to `external_services_orchestration/models.py::ExternalServiceRunLog`.
8.  **Frontend Polls Status:** The frontend periodically polls the `src/external_services_orchestration/router.py::get_job_status` endpoint to track the progress of the background job.
9.  **Human in the Loop:** After AI generation, the frontend might present the generated content for human review, allowing edits and setting a new status via `src/<project_domain_1>/router.py` (e.g., a PUT endpoint for content review). This process updates content and creates versioning records (`ChapterVersion`).

---

## Part 2: Detailed Backend Specification (The "How-To")

This section provides prescriptive guidelines and code structure for each component.

### 1. Root Directory (`./`)

*   **`.env`**: Must exist. Stores sensitive configuration.
    ```env
    DATABASE_URL="postgresql+asyncpg://user:password@db:5432/dbname"
    REDIS_URL="redis://redis:6379"
    APP_VERSION="1.0.0"
    ENVIRONMENT="development"
    # Example for LLMs
    OPENAI_API_KEY="sk-..."
    DEFAULT_OPENAI_MODEL_NAME="gpt-4o-mini"
    # Example for other external service pricing (could be JSON string or external file)
    EXTERNAL_SERVICE_PRICING='{"llm_openai_gpt4": {"input_cost": 10.0, "output_cost": 30.0}, "translation_api_google": {"cost_per_char": 0.0001}}'
    ```
*   **`pyproject.toml` (or `requirements.txt`)**: Defines all project dependencies.
    ```toml
    [project]
    name = "my-awesome-project"
    version = "0.1.0"
    dependencies = [
        "fastapi",
        "uvicorn[standard]",
        "SQLAlchemy[asyncio]",
        "asyncpg",
        "pydantic",
        "pydantic-settings",
        "redis",
        "arq",
        "fastapi-limiter",
        "circuitbreaker",
        "httpx",
        # Your 'agents' or 'task_processors' library if it's a separate package
        # "my-generic-ai-agents-lib",
    ]

    [tool.poetry.dev-dependencies] # If using Poetry
    pytest = "^7.0"
    pytest-asyncio = "^0.21.0"
    alembic = "^1.11.0"
    # ... other dev tools
    ```
*   **`Dockerfile`**: Standardized for FastAPI applications.
    ```dockerfile
    # Use the official Python image as a base image
    FROM python:3.11-slim-buster

    # Set the working directory in the container
    WORKDIR /app

    # Copy the pyproject.toml and poetry.lock files
    # (or requirements.txt if not using poetry)
    COPY pyproject.toml poetry.lock ./

    # Install poetry if not already installed (or pip for requirements.txt)
    RUN pip install poetry

    # Install project dependencies
    RUN poetry install --no-root --no-dev

    # Copy the rest of the application code
    COPY . .

    # Expose the port FastAPI will run on
    EXPOSE 8000

    # Command to run the application using Uvicorn
    # Use --host 0.0.0.0 to make it accessible from outside the container
    # Adjust src.main:app based on your actual main.py path
    CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
    ```
*   **`alembic/`**: Configured for SQLAlchemy migrations.
    *   `alembic.ini`: Standard configuration.
    *   `env.py`: Modify to correctly load your `Base` from `src.core.database`.
        ```python
        # alembic/env.py - crucial part to modify
        from logging.config import fileConfig
        from sqlalchemy import engine_from_config
        from sqlalchemy import pool
        from alembic import context

        # Import your Base here
        from src.core.database import Base # THIS IS THE KEY LINE
        from src.core.config import settings # And your settings

        # ... rest of alembic env.py ...

        # In run_migrations_offline and run_migrations_online, ensure
        # target_metadata is set to Base.metadata
        target_metadata = Base.metadata
        ```

### 2. `src/main.py` (Application Entry Point)

*   **Purpose:** Initializes the FastAPI app, sets up middleware, registers routers, and handles startup/shutdown events.
*   **Mandatory elements:**
    *   `FastAPI` app instance.
    *   `CORSMiddleware` (configurable via `config.py`).
    *   `@app.on_event("startup")`: Database creation (`Base.metadata.create_all`), task queue configuration/connection, rate limiter initialization.
    *   `@app.on_event("shutdown")`: Task queue/rate limiter shutdown.
    *   `app.include_router()` for all top-level routers.
    *   A simple `/health` or `/` endpoint.
*   **Example:**
    ```python
    # src/main.py
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi_limiter import FastAPILimiter
    from redis.asyncio import Redis
    import logging

    from src.core.config import settings
    from src.core.database import Base, engine
    from src.core.task_queue import task_queue
    from src.core.logging import configure_logging # NEW: Standardized logging
    from src.<project_domain_1>.router import router as project_domain_router # Example
    from src.external_services_orchestration.router import router as orchestration_router # Example

    # Configure logging early
    configure_logging()
    logger = logging.getLogger(__name__)

    app = FastAPI(
        title=f"{settings.APP_NAME} - {settings.ENVIRONMENT}",
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(','), # From config
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        logger.info("Application starting up...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database schema ensured.")

        task_queue.configure(settings.REDIS_URL)
        await task_queue.connect()
        logger.info("Task queue connected.")

        redis_client = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis_client)
        logger.info("FastAPILimiter initialized.")
        logger.info("Startup complete.")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutting down...")
        await task_queue.close()
        await FastAPILimiter.close()
        logger.info("Shutdown complete.")

    # Include all domain-specific and orchestration routers
    app.include_router(project_domain_router)
    app.include_router(orchestration_router)

    @app.get("/", tags=["Health Check"])
    async def health_check():
        return {"status": "ok", "version": settings.APP_VERSION}

    ```

### 3. `src/core/` (Reusable Core Components)

*   **`config.py`**:
    *   **Purpose:** Load application settings from environment variables.
    *   **Mandatory:** `BaseSettings`, `SettingsConfigDict`, `DATABASE_URL`, `REDIS_URL`, `APP_VERSION`, `ENVIRONMENT`.
    *   **Recommendation:** Generic `EXTERNAL_SERVICE_PRICING` dictionary, `CORS_ORIGINS` as comma-separated string.
    *   **Example:**
        ```python
        # src/core/config.py
        from pydantic_settings import BaseSettings, SettingsConfigDict
        from decimal import Decimal
        from typing import Dict, Any

        class Settings(BaseSettings):
            model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

            # Core Application
            DATABASE_URL: str
            REDIS_URL: str = "redis://localhost:6379"
            APP_VERSION: str = "0.1.0"
            ENVIRONMENT: str = "development"
            APP_NAME: str = "My Awesome App"
            APP_DESCRIPTION: str = "A standardized backend for AI automation projects."
            CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173" # Comma-separated

            # External Service/LLM Settings
            OPENAI_API_KEY: str | None = None # Make optional if not always used
            DEFAULT_LLM_MODEL_NAME: str = "gpt-4o-mini"
            # Generic pricing for any external service/model. Key is service/model name.
            EXTERNAL_SERVICE_PRICING: Dict[str, Dict[str, Decimal]] = {
                "gpt-4o-mini": {"prompt": Decimal("0.15"), "completion": Decimal("0.60")},
                "gpt-4-turbo": {"prompt": Decimal("10.00"), "completion": Decimal("30.00")},
                "mock_service_A": {"cost_unit": Decimal("0.01")} # Example for non-LLM pricing
            }

        settings = Settings()
        ```
*   **`database.py`**:
    *   **Purpose:** SQLAlchemy engine, session management, base for models.
    *   **Mandatory:** `MetaData` with naming convention, `declarative_base(metadata=...)`, `create_async_engine`, `sessionmaker(class_=AsyncSession, expire_on_commit=False)`, `get_db_session` dependency.
    *   **Example:** (Same as your existing, it's already well-designed)
*   **`exceptions.py`**:
    *   **Purpose:** Centralize custom exceptions for predictable error handling.
    *   **Recommendation:** Define base exceptions and specific ones for common scenarios (e.g., `NotFoundException`, `ConflictException`). Use `HTTPException` in routers.
    *   **Example:**
        ```python
        # src/core/exceptions.py
        from fastapi import HTTPException, status

        class ServiceException(HTTPException):
            """Base exception for service-level errors."""
            pass

        class NotFoundException(ServiceException):
            def __init__(self, detail: str = "Resource not found"):
                super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

        class ConflictException(ServiceException):
            def __init__(self, detail: str = "Resource conflict"):
                super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)

        class BadRequestException(ServiceException):
            def __init__(self, detail: str = "Bad request"):
                super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        class ExternalServiceError(ServiceException):
            def __init__(self, detail: str = "External service error"):
                super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
        ```
*   **`logging.py`**:
    *   **Purpose:** Standardize application-wide logging.
    *   **Recommendation:** Configure basic logger, perhaps based on `ENVIRONMENT`.
    *   **Example:**
        ```python
        # src/core/logging.py
        import logging
        from src.core.config import settings

        def configure_logging():
            # Basic configuration. For production, consider structured logging (e.g., loguru, json logging)
            # and external log management.
            log_level = logging.INFO
            if settings.ENVIRONMENT == "development":
                log_level = logging.DEBUG

            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler() # Outputs to console
                    # logging.FileHandler("app.log") # Uncomment for file logging
                ]
            )
            # Suppress chatty loggers if needed
            logging.getLogger("uvicorn").setLevel(logging.WARNING)
            logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
            logging.getLogger("arq").setLevel(logging.WARNING)
            logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING) # Set to INFO for DB query logging
        ```
*   **`schemas.py`**:
    *   **Purpose:** Common Pydantic schemas for cross-cutting concerns.
    *   **Mandatory:** `TaskStatus` for background jobs.
    *   **Recommendation:** `HealthCheckResponse`.
    *   **Example:**
        ```python
        # src/core/schemas.py
        from pydantic import BaseModel, Field

        class TaskStatus(BaseModel):
            job_id: str = Field(..., description="Unique ID of the background job.")
            status: str = Field(..., description="Current status of the job (e.g., 'queued', 'in_progress', 'complete', 'failed', 'not_found').")
            result: dict | None = Field(None, description="Optional result data if the task is complete.")
            error: str | None = Field(None, description="Optional error message if the task failed.")

        class HealthCheckResponse(BaseModel):
            status: str
            version: str
        ```
*   **`security.py`**:
    *   **Purpose:** Placeholder for authentication/authorization.
    *   **Recommendation:** Integrate JWT or API key authentication.
*   **`task_queue.py`**:
    *   **Purpose:** Singleton wrapper for ARQ Redis connection pool.
    *   **Mandatory:** `configure`, `connect`, `close`, `enqueue`.
    *   **Example:** (Same as your existing, it's already well-designed)

### 4. `src/<project_domain_name>/` (Domain-Specific Module)

This module encapsulates all logic directly related to your specific project's core entities. For your book-writing app, this was `src/project`. For another project, it might be `src/invoice_processing`, `src/chat_bots`, etc.

*   **`models.py`**:
    *   **Purpose:** Define SQLAlchemy ORM models representing the project's data entities.
    *   **Mandatory:** Inherit from `src.core.database.Base`. Define `id` as `UUID(as_uuid=True)`.
    *   **Recommendation:** Use `relationship` for ORM relationships, `cascade="all, delete-orphan"` where appropriate. Implement `Version` tables for crucial content.
    *   **Example:** (Your `Project`, `Part`, `Chapter`, `ChapterVersion` models are perfect examples.)
*   **`schemas.py`**:
    *   **Purpose:** Define Pydantic models for request/response bodies and data validation specific to this domain.
    *   **Mandatory:** `BaseModel`, `ConfigDict(from_attributes=True)` for ORM mode.
    *   **Recommendation:** Separate `Create`, `Read`, `Update` schemas. Use nested schemas for relationships (`ProjectDetailRead` with `PartReadWithChapters`).
    *   **Example:** (Your `ProjectCreate`, `ProjectRead`, `PartRead`, `ChapterRead`, etc., are perfect examples.)
*   **`service.py`**:
    *   **Purpose:** Contains the core business logic and direct database interactions for this domain. This is where most of your `async with session` blocks will reside.
    *   **Mandatory:** All functions should accept `session: AsyncSession` as the first argument. Avoid mixing database logic with external API calls (defer external calls to `external_services_orchestration/service.py`).
    *   **Recommendation:** Helper functions for common CRUD operations (e.g., `get_by_id`, `create`, `update`, `delete`).
    *   **Example:** (Your `get_all_projects`, `create_project`, `update_chapter_content`, `finalize_part_structure` are good examples.)
*   **`router.py`**:
    *   **Purpose:** Define FastAPI endpoints (API routes) for interacting with this domain's entities.
    *   **Mandatory:** `APIRouter`, `Depends(get_db_session)`. Use `HTTPException` for errors.
    *   **Recommendation:** Follow RESTful conventions. Use `status` codes appropriately. Inject dependencies via `src/<project_domain_name>/dependencies.py`.
    *   **Example:** (Your `project_router.py`, `chapter_router.py`, `part_router.py` are good examples.)
*   **`dependencies.py`**:
    *   **Purpose:** Provide reusable FastAPI dependency functions for common object retrieval and validation.
    *   **Mandatory:** Functions that accept `session: AsyncSession` and `id: uuid.UUID` (or other identifiers), perform lookup using `service.py`, and raise `HTTPException` if not found.
    *   **Example:** (Your `valid_project_id`, `valid_part_id`, `valid_chapter_id` are perfect examples.)

### 5. `src/external_services_orchestration/` (General AI/External API Automation)

This module generalizes the concept of your `src/crew` module to handle *any* external service integration that involves long-running tasks, cost tracking, and complex orchestration.

*   **`agents/generic_processor.py`**: (Or `task_processors.py`, `llm_interface.py` etc.)
    *   **Purpose:** Define generic interfaces/classes for interacting with different types of external services (e.g., a base class for LLMs, one for image generation, one for translation). This allows swapping underlying providers.
    *   **Mandatory:** A generic `Processor` or `Agent` class that wraps the actual API calls. It should define `name`, `instructions` (if applicable), and an `output_type`. It should also specify the `model_name` or `service_id` it uses for cost tracking.
    *   **Recommendation:** A `Runner` class (like your `agents` library) to execute these processors and handle input/output parsing.
    *   **Example (Conceptual `Agent`):**
        ```python
        # src/external_services_orchestration/agents/llm_agent.py
        from pydantic import BaseModel, Field
        from typing import Any, Type
        import logging

        logger = logging.getLogger(__name__)

        class LLMOutput(BaseModel):
            text: str = Field(..., description="Generated text content.")
            # Add other common fields like 'usage' from raw response if consistent

        class Agent:
            """Generic agent interface for LLM-based tasks."""
            def __init__(self, name: str, instructions: str, model: str, output_type: Type[BaseModel]):
                self.name = name
                self.instructions = instructions
                self.model = model
                self.output_type = output_type

            async def run(self, input_text: str) -> tuple[BaseModel | None, Any]:
                """
                Executes the agent's task.
                Returns (parsed_output, raw_api_response_object_with_usage).
                Implement actual LLM API call here.
                """
                logger.info(f"Agent '{self.name}' (Model: {self.model}) executing with input: {input_text[:100]}...")
                # --- Placeholder for actual LLM API call (e.g., OpenAI, Anthropic) ---
                # Example with dummy response for illustration
                await asyncio.sleep(0.1) # Simulate API latency

                # This is where your external 'agents' library would be used
                # For example:
                # from your_llm_sdk import LLMClient
                # client = LLMClient(api_key=...)
                # raw_response = await client.chat.completions.create(...)
                # parsed_output = self.output_type.model_validate_json(raw_response.choices[0].message.content) # Assuming JSON output
                # return parsed_output, raw_response

                # Dummy implementation:
                dummy_text = f"This is content generated by {self.name} based on input: '{input_text[:50]}...'"
                dummy_usage = type('Usage', (object,), {
                    'input_tokens': 100,
                    'output_tokens': 200,
                    'total_tokens': 300,
                    'model_name': self.model # Ensure actual model is captured
                })()
                dummy_raw_response = type('RawResponse', (object,), {
                    'usage': dummy_usage,
                    'choices': [type('Choice', (object,), {'message': type('Message', (object,), {'content': dummy_text})})()]
                })()
                
                return self.output_type(text=dummy_text), dummy_raw_response
        ```
*   **`models.py`**:
    *   **Purpose:** Define models for logging the execution and cost of external service calls.
    *   **Mandatory:** `ExternalServiceRunLog` (generalized from `CrewRunLog`).
    *   **Example:**
        ```python
        # src/external_services_orchestration/models.py
        import uuid
        from datetime import datetime
        from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, UUID
        from src.core.database import Base

        class ExternalServiceRunLog(Base):
            __tablename__ = "external_service_run_logs"
            id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
            # Generic ID to link to the source entity (e.g., project_id, chapter_id, invoice_id)
            # You might need multiple FKs or a generic 'entity_id' + 'entity_type' if linking to many tables.
            related_entity_id = Column(UUID(as_uuid=True), nullable=True) # Optional, can be FK or just reference
            related_entity_type = Column(String, nullable=True) # e.g., "Project", "Chapter"

            task_name = Column(String, nullable=False) # e.g., "Part Generation", "Chapter Content"
            service_name = Column(String, nullable=False) # e.g., "OpenAI", "GoogleTranslate"
            model_identifier = Column(String, nullable=False) # e.g., "gpt-4o-mini", "text-bison"

            input_units = Column(Integer, nullable=False) # tokens, chars, image_count etc.
            output_units = Column(Integer, nullable=False) # tokens, chars, image_count etc.
            total_units = Column(Integer, nullable=False) # Sum of input + output

            total_cost = Column(Numeric(10, 8), nullable=False)
            created_at = Column(DateTime, default=datetime.utcnow)
        ```
*   **`pricing.py`**:
    *   **Purpose:** Centralize cost calculation for various external services.
    *   **Mandatory:** A `calculate_cost` function that takes service identifier, input units, output units, and uses `settings.EXTERNAL_SERVICE_PRICING`.
    *   **Example:**
        ```python
        # src/external_services_orchestration/pricing.py
        from decimal import Decimal
        from src.core.config import settings
        import logging

        logger = logging.getLogger(__name__)

        def calculate_cost(service_id: str, input_units: int, output_units: int) -> Decimal:
            """
            Calculates the cost of an external service call based on unit usage.
            `service_id` should match a key in settings.EXTERNAL_SERVICE_PRICING.
            """
            pricing = settings.EXTERNAL_SERVICE_PRICING.get(service_id)
            if not pricing:
                logger.warning(f"Pricing not found for service '{service_id}'. Cost will be 0.0.")
                return Decimal("0.0")

            if input_units < 0 or output_units < 0:
                logger.warning(f"Negative unit counts received for service '{service_id}'. Input: {input_units}, Output: {output_units}. Setting cost to 0.0.")
                return Decimal("0.0")

            cost = Decimal("0.0")
            # This logic will vary based on how each service charges (per token, per char, per call, etc.)
            # Example for LLM-like token pricing:
            if "prompt" in pricing and "completion" in pricing:
                # Assuming pricing is per million units (adjust as per actual pricing schema)
                cost = (Decimal(input_units) / Decimal(1_000_000)) * pricing["prompt"] + \
                       (Decimal(output_units) / Decimal(1_000_000)) * pricing["completion"]
            elif "cost_unit" in pricing: # General cost per unit
                cost = (Decimal(input_units + output_units)) * pricing["cost_unit"]
            else:
                logger.warning(f"Unrecognized pricing structure for service '{service_id}'. Cost will be 0.0.")

            return cost
        ```
*   **`router.py`**:
    *   **Purpose:** Expose API endpoints for *triggering* complex, long-running external service tasks and checking their status.
    *   **Mandatory:** `APIRouter`, `Depends(get_db_session)`. Use `TaskStatus` for responses. Apply `RateLimiter` where tasks are costly.
    *   **Recommendation:** Endpoints that enqueue jobs should return `HTTP 202 Accepted`.
    *   **Example (Generalized from `crew/router.py`):**
        ```python
        # src/external_services_orchestration/router.py
        import uuid
        from fastapi import APIRouter, Depends, status, Body
        from fastapi_limiter.depends import RateLimiter
        from arq.jobs import Job # Import Job class from arq

        from src.core.task_queue import task_queue
        from src.core.schemas import TaskStatus
        from src.<project_domain_1>.dependencies import valid_some_domain_entity_id # Example dependency

        # Placeholder for specific project needs (e.g., ProjectRead from your book app)
        from src.<project_domain_1>.schemas import ProjectRead as SomeDomainEntityRead 

        router = APIRouter(prefix="/orchestrate", tags=["Orchestration Engine"])

        @router.post(
            "/generate-content/{entity_id}",
            status_code=status.HTTP_202_ACCEPTED,
            response_model=TaskStatus,
            summary="Trigger Content Generation for an Entity",
            dependencies=[Depends(RateLimiter(times=5, seconds=60))]
        )
        async def queue_content_generation(
            entity: SomeDomainEntityRead = Depends(valid_some_domain_entity_id),
            # Potentially accept a request body for configuration if needed
        ):
            """
            Queues a background job to generate content for a given domain entity.
            """
            job = await task_queue.enqueue("generate_content_worker", entity.id)
            return TaskStatus(job_id=job.job_id, status="queued")

        @router.get("/status/{job_id}", response_model=TaskStatus, summary="Get Job Status")
        async def get_job_status(job_id: str):
            """Checks the status of a background job."""
            job = Job(job_id, task_queue.pool)
            status_string = await job.status()
            result_data = None
            error_message = None

            if status_string == 'complete':
                try:
                    result_data = await job.result()
                except Exception as e:
                    error_message = f"Failed to retrieve result: {e}"
                    status_string = "failed" # If result retrieval fails, job is effectively failed for client

            elif status_string == 'failed':
                error_message = str(await job.result()) # ARQ job.result() holds exception on failure

            return TaskStatus(
                job_id=job_id,
                status=status_string,
                result=result_data,
                error=error_message
            )
        ```
*   **`schemas.py`**:
    *   **Purpose:** Pydantic schemas specific to the orchestration tasks (e.g., `LLMGenerationRequest`, `TranslationRequest`).
    *   **Example:** (Your `PartListOutline`, `ChapterListOutline`, `FinalizationRequest` were examples of these.)
*   **`service.py`**:
    *   **Purpose:** Contains the complex orchestration logic, makes calls to external APIs (via `agents`), and updates domain models via `src/<project_domain_name>/service.py`.
    *   **Mandatory:** Functions should accept `session: AsyncSession` as the first argument. Wrap external API calls with a `circuitbreaker`. Use `log_external_service_run`.
    *   **Recommendation:** Use Python's `logging` module. Handle specific exceptions from external services.
    *   **Example (Generalized from `crew/service.py`):**
        ```python
        # src/external_services_orchestration/service.py
        import uuid
        import asyncio
        from decimal import Decimal
        import logging
        from circuitbreaker import CircuitBreaker, CircuitBreakerError
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.core.config import settings
        from src.core.exceptions import ExternalServiceError
        from src.external_services_orchestration.models import ExternalServiceRunLog
        from src.external_services_orchestration.pricing import calculate_cost
        from src.external_services_orchestration.agents.llm_agent import Agent, LLMOutput # Example agent

        # Import specific service functions from your domain
        from src.<project_domain_1>.service import update_project_status, get_project_by_id

        logger = logging.getLogger(__name__)

        # Configure a generic circuit breaker
        generic_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=(ConnectionError, asyncio.TimeoutError, ExternalServiceError)
        )

        @generic_circuit_breaker
        async def _execute_external_service_call(processor: Agent, input_data: str) -> tuple[Any, Any]:
            """Helper to execute any external service call through a processor, wrapped by CB."""
            # The 'run' method should return parsed_output and raw_response_with_usage
            return await processor.run(input_data)

        async def log_external_service_run(
            session: AsyncSession,
            related_entity_id: uuid.UUID | None,
            related_entity_type: str | None,
            task_name: str,
            service_name: str,
            model_identifier: str,
            input_units: int,
            output_units: int,
        ):
            """Logs the metrics of a completed external service call."""
            total_units = input_units + output_units
            run_cost = calculate_cost(
                service_id=model_identifier, # Or service_name, depending on your pricing granularity
                input_units=input_units,
                output_units=output_units,
            )

            new_log = ExternalServiceRunLog(
                related_entity_id=related_entity_id,
                related_entity_type=related_entity_type,
                task_name=task_name,
                service_name=service_name,
                model_identifier=model_identifier,
                input_units=input_units,
                output_units=output_units,
                total_units=total_units,
                total_cost=run_cost
            )
            session.add(new_log)
            # You might also update a total cost on the main domain entity here
            # e.g., await session.execute(update(Project).where(Project.id == related_entity_id).values(total_cost=Project.total_cost + run_cost))
            await session.commit()
            logger.info(f"📊 Run Logged: '{task_name}' for {model_identifier} - Units: {total_units}, Cost: ${run_cost:.6f}")

        # Example Orchestration Function
        async def run_content_generation_task(session: AsyncSession, project_id: uuid.UUID) -> bool:
            logger.info(f"🚀 Starting content generation for project: {project_id}")
            project = None
            try:
                project = await get_project_by_id(session, project_id=project_id) # From domain service
                if not project:
                    logger.error(f"❌ Content generation failed: Project {project_id} not found.")
                    return False

                llm_agent = Agent( # Example LLM agent instance
                    name="ContentGenerator",
                    instructions="Generate compelling content.",
                    model=settings.DEFAULT_LLM_MODEL_NAME,
                    output_type=LLMOutput
                )

                input_for_llm = f"Generate content for project blueprint: {project.raw_blueprint}"
                
                try:
                    parsed_output, raw_response = await _execute_external_service_call(llm_agent, input_for_llm)
                except CircuitBreakerError:
                    logger.error(f"🔴 Circuit breaker OPEN for external API. Cannot generate content for project {project_id}.")
                    await update_project_status(session, project_id, "API_CIRCUIT_OPEN") # From domain service
                    return False
                except Exception as e:
                    logger.error(f"❌ Error during agent execution for content generation: {e}", exc_info=True)
                    raise ExternalServiceError(detail=f"Content generation agent failed: {e}")

                generated_content = parsed_output.text if parsed_output else None

                if generated_content:
                    # Update the domain model (via its service)
                    # For example: await update_project_generated_content(session, project.id, generated_content)
                    await update_project_status(session, project_id, "CONTENT_GENERATED")
                    
                    # Extract usage metrics from raw_response (adapt based on actual API client response)
                    usage = getattr(raw_response, 'usage', {})
                    input_tokens = getattr(usage, 'input_tokens', 0)
                    output_tokens = getattr(usage, 'output_tokens', 0)

                    await log_external_service_run(
                        session=session,
                        related_entity_id=project.id,
                        related_entity_type="Project",
                        task_name="Content Generation",
                        service_name="OpenAI", # Or other API name
                        model_identifier=llm_agent.model,
                        input_units=input_tokens,
                        output_units=output_tokens,
                    )
                    logger.info(f"✅ Content generated successfully for project: {project_id}.")
                    return True
                else:
                    logger.error(f"❌ Content generation failed for project: {project_id}. Agent returned no content.")
                    await update_project_status(session, project_id, "CONTENT_GEN_FAILED")
                    return False

            except Exception as e:
                logger.critical(f"🔥 Critical error during content generation for project {project_id}: {e}", exc_info=True)
                if project:
                    await update_project_status(session, project_id, "CRITICAL_ERROR")
                return False
        ```
*   **`tasks.py`**:
    *   **Purpose:** Define the ARQ worker functions that will be enqueued. These functions simply call the actual business logic in `service.py`.
    *   **Mandatory:** Each function must accept `ctx` (ARQ context) as its first argument. Use `AsyncSessionFactory` to get a database session within the worker.
    *   **Example:**
        ```python
        # src/external_services_orchestration/tasks.py
        import uuid
        from src.core.database import AsyncSessionFactory
        from src.external_services_orchestration.service import run_content_generation_task # Example

        async def generate_content_worker(ctx, project_id: uuid.UUID) -> dict:
            """Worker for generic content generation."""
            async with AsyncSessionFactory() as session:
                try:
                    success = await run_content_generation_task(session, project_id)
                    return {
                        "status": "success" if success else "failure",
                        "project_id": str(project_id)
                    }
                except Exception as e:
                    # Log the error, ARQ will also capture it.
                    return {
                        "status": "error",
                        "project_id": str(project_id),
                        "error": str(e)
                    }
        ```
*   **`worker.py`**:
    *   **Purpose:** Define the ARQ worker settings, specifying which tasks it can handle. This file is typically run directly by the ARQ command-line tool.
    *   **Mandatory:** `WorkerSettings` class, `functions` list containing all worker callables, `redis_settings` from `task_queue`.
    *   **Example:**
        ```python
        # src/external_services_orchestration/worker.py
        from arq.connections import RedisSettings
        from src.core.config import settings
        from src.core.task_queue import task_queue # Ensure task_queue is configured
        from .tasks import generate_content_worker # Import all relevant worker functions

        # This ensures the task_queue singleton has its redis_settings attribute set
        # when the worker process starts.
        task_queue.configure(settings.REDIS_URL)

        class WorkerSettings:
            functions = [
                generate_content_worker,
                # Add other worker functions here
            ]
            # Use the redis_settings object stored in the task_queue singleton
            redis_settings = task_queue.redis_settings
            # You might add other ARQ settings here, e.g., max_jobs, job_timeout
            # on_startup = [startup_worker_hook] # If you need worker-specific startup logic
            # on_shutdown = [shutdown_worker_hook]
        ```

---

### 6. General API Design Guidelines

*   **RESTful Endpoints:** Use clear, plural nouns for resources (e.g., `/projects`, `/chapters`). Use HTTP verbs (`GET`, `POST`, `PUT`, `DELETE`) appropriately.
*   **Input/Output Validation:** Always use Pydantic for request bodies and response models.
*   **Error Handling:** Use `raise HTTPException` within routers and dependencies. Service layer functions can raise custom exceptions (from `src/core/exceptions.py`), which are then caught and converted to `HTTPException` in the router.
*   **Status Codes:** Return appropriate HTTP status codes (e.g., `200 OK`, `201 Created`, `202 Accepted`, `204 No Content`, `400 Bad Request`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`).
*   **Rate Limiting:** Apply `FastAPILimiter` to all endpoints that trigger expensive or resource-intensive operations, especially those involving external APIs.
*   **Asynchronous Operations:** For any operation that might block (e.g., external API calls, complex computations), offload to ARQ via the `external_services_orchestration` module.

---

### 7. Deployment Considerations (Brief)

*   **Containerization:** Use Docker (as per `Dockerfile` example).
*   **Orchestration:** Kubernetes or Docker Compose for managing multiple services (FastAPI, Redis, ARQ workers, Database).
*   **Environment Variables:** All sensitive data and configurations must be passed via environment variables, not hardcoded.
*   **Secrets Management:** Use proper secrets management (e.g., Kubernetes Secrets, Vault, environment variables).
*   **Logging:** Ensure logs are aggregated and accessible (e.g., to ELK stack, Datadog).
*   **Monitoring:** Implement health checks and metrics for all services.

---

### 8. Testing Guidelines

*   **Unit Tests:** Focus on individual functions in `service.py` (mocking database calls and external API calls).
*   **Integration Tests:** Test the interaction between `router` and `service`, or `service` and `database`. Use `TestClient` for FastAPI.
*   **End-to-End Tests:** Test the full flow, potentially involving ARQ workers (can be tricky to set up for CI/CD).
*   **Mocking:** Use `unittest.mock` effectively for external dependencies.

---

### 9. Documentation

*   **Automatic OpenAPI/Swagger UI:** FastAPI provides this out of the box. Ensure path operation `summary` and `description` are well-written.
*   **Docstrings:** All modules, classes, and functions should have clear docstrings explaining their purpose, arguments, and return values.
*   **Markdown Docs:** Maintain a `README.md` and potentially a `docs/` directory for architectural decisions, setup guides, and operational procedures.

