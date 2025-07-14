# Scriptorium-Engine: Return on Experience (REX)

This document captures key learnings and strategic oversights from the setup and implementation of the Scriptorium-Engine. Its purpose is to create a refined development process that prevents these issues in the future.

## Part 1: Initial Project & Tooling Setup

### Issue 1.1: Platform-Incompatibility of Setup Script

*   **Symptom:** `chmod` command failed on Windows PowerShell.
*   **Lesson Learned:** Setup scripts must be platform-agnostic.
*   **Strategic Resolution:** Use a Python-based setup script (`init_structure.py`) instead of shell scripts.

### Issue 1.2: Incomplete Scaffolding for Alembic

*   **Symptom:** `FileNotFoundError` for `alembic/script.py.mako` and the `alembic/versions/` directory.
*   **Root Cause:** The manual setup script was incomplete.
*   **Lesson Learned:** When manually scaffolding, ensure all required sub-folders and template files for a given tool are created.
*   **Strategic Resolution:** A comprehensive `init_structure.py` must create the full, expected directory structure for all integrated tools.

## Part 2: Configuration & Dependency Management

### Issue 2.1: Missing Database Drivers

*   **Symptom:** `ModuleNotFoundError: No module named 'aiosqlite'`.
*   **Lesson Learned:** Database drivers are not included with SQLAlchemy by default and must be explicitly added to `requirements.txt`.

### Issue 2.2: Pydantic Strictness on Extra Fields

*   **Symptom:** `ValidationError: ... Extra inputs are not permitted`.
*   **Root Cause:** Two separate `Settings` objects were trying to parse the same `.env` file, but neither was aware of all the variables present.
*   **Lesson Learned:** A single source of truth for environment variables is critical.
*   **Strategic Resolution:** Use a single, unified Pydantic `Settings` class in a central location (`src/core/config.py`) that defines *all* expected environment variables for the entire application.

### Issue 2.3: Circular Imports

*   **Symptom:** `ImportError: cannot import name ... from partially initialized module ... (most likely due to a circular import)`.
*   **Root Cause:** Modules had two-way dependencies (e.g., `main.py` imported a router, and the router imported from `main.py`).
*   **Lesson Learned:** A clean, hierarchical dependency graph is non-negotiable. Low-level modules (`core`, services) should never import from high-level modules (`main.py`, routers).
*   **Strategic Resolution:** Use a dedicated, neutral location for shared dependencies (e.g., `src/core/dependencies.py` if needed) or, even better, use abstractions (like the `TaskQueue` service) to decouple modules from each other. The application entrypoint (`main.py`) should assemble components, but components should not depend on it.

## Part 3: Library API Usage & Best Practices

### Issue 3.1: Dialect-Specific Types in Models

*   **Symptom:** `CompileError: ... can't render element of type JSONB` on SQLite.
*   **Lesson Learned:** Use generic SQLAlchemy types (`sa.JSON`) in models to ensure portability between different database backends.

### Issue 3.2: Sync vs. Async Tooling Conflict (Alembic)

*   **Symptom:** `sqlalchemy.exc.MissingGreenlet` when running Alembic.
*   **Root Cause:** The synchronous Alembic tool was configured to use an async database driver.
*   **Lesson Learned:** Synchronous tools require synchronous database drivers.
*   **Strategic Resolution:** Implement URL-rewriting logic in `alembic/env.py` to transparently replace the async driver with a sync equivalent *only* for the migration tool's execution.

### Issue 3.3: Incorrect Library API Arguments (ARQ & CrewAI)

*   **Symptoms:**
    1.  `TypeError: create_pool() got an unexpected keyword argument 'redis_settings'`.
    2.  `AttributeError: type object 'RedisSettings' has no attribute 'from_url'`.
    3.  `ValidationError: ... verbose Input should be a valid boolean`.
*   **Root Cause:** Incorrect usage of the `arq` and `crewai` library APIs.
*   **Lesson Learned:** When fighting with a library's API, do not just patch the error; re-evaluate the strategy. A series of small API errors often points to a larger architectural weakness (like repeated configuration).
*   **Strategic Resolution:**
    1.  **Create Abstraction Layers:** We built a `TaskQueue` abstraction to hide the complexities of `arq`'s API. This provides a stable internal interface and makes the system maintainable and easier to evolve.
    2.  **Verify Data Types:** Always ensure the data types passed to library functions (e.g., boolean for `verbose`) match the documented requirements.

### Issue 3.4: Incorrect Data Handling (CrewAI Output)

*   **Symptom:** `ProgrammingError: type 'CrewOutput' is not supported` when saving to the database.
*   **Root Cause:** The application tried to save a complex Python object (`CrewOutput`) into a simple database text field.
*   **Lesson Learned:** Always inspect the return types of library functions. Do not assume they return primitive types.
*   **Strategic Resolution:** Explicitly extract the primitive data needed from the returned object before passing it to another system (e.g., `crew_output.raw`).

---
## Final Strategic Recommendation for Future Sprints

1.  **Abstract Early:** If a third-party library's configuration or API proves complex or volatile, immediately wrap it in a simple, internal abstraction layer. This pays massive dividends in stability and maintainability.
2.  **Single Source of Truth:** Enforce a single source of truth for all configurations, especially environment variables.
3.  **Validate Data at Boundaries:** Be vigilant about the data types being passed between different parts of the system (API -> Service -> Library -> Database). Extract and validate the specific data needed at each step.