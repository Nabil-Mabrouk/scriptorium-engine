# Scriptorium-Engine: Return on Experience (REX)

This document captures key learnings and strategic oversights from the setup and implementation of the Scriptorium-Engine. Its purpose is to create a refined development process that prevents these issues in the future.

## Part 1: Initial Project & Tooling Setup

### Issue 1.1: Platform-Incompatibility of Setup Script
*   **Symptom:** `chmod` command failed on Windows PowerShell.
*   **Lesson Learned:** Setup scripts must be platform-agnostic.
*   **Strategic Resolution:** Use a Python-based setup script (`init_structure.py`).

### Issue 1.2: Incomplete Scaffolding for Alembic
*   **Symptom:** `FileNotFoundError` for `alembic/script.py.mako` and the `alembic/versions/` directory.
*   **Lesson Learned:** When manually scaffolding, ensure all required sub-folders and template files for a given tool are created.

## Part 2: Configuration & Dependency Management

### Issue 2.1: Missing Database Drivers
*   **Symptom:** `ModuleNotFoundError: No module named 'aiosqlite'`.
*   **Lesson Learned:** Database drivers must be explicitly declared in `requirements.txt`.

### Issue 2.2: Pydantic Strictness & Startup Conflicts
*   **Symptom:** `ValidationError: ... Extra inputs are not permitted` on startup.
*   **Lesson Learned:** A single source of truth for environment variables is critical.
*   **Strategic Resolution:** Use one unified Pydantic `Settings` class (`src/core/config.py`) that defines *all* expected environment variables.

### Issue 2.3: Circular Imports
*   **Symptom:** `ImportError: cannot import name ... from partially initialized module ...`.
*   **Root Cause:** Two-way dependencies between modules (e.g., `main.py` <=> `router.py`).
*   **Lesson Learned:** Enforce a clean, one-way, hierarchical dependency graph. Low-level modules should never import from high-level modules.
*   **Strategic Resolution:** Use abstractions (like the `TaskQueue` service) and dedicated dependency files (`src/project/dependencies.py`) to decouple modules.

### Issue 2.4: Incorrect Library Imports
*   **Symptom:** `ModuleNotFoundError: No module named 'crewai.kicker'`
*   **Lesson Learned:** Do not assume a library's internal module structure. Always import from the public, top-level API unless the documentation specifies otherwise.
*   **Strategic Resolution:** Corrected the import from `crewai.kicker import CrewOutput` to `from crewai import CrewOutput`.

## Part 3: Library API Usage & Best Practices

### Issue 3.1: Dialect-Specific Types in Models
*   **Symptom:** `CompileError: ... can't render element of type JSONB` on SQLite.
*   **Lesson Learned:** Use generic SQLAlchemy types (`sa.JSON`) in models for portability.

### Issue 3.2: Sync vs. Async Tooling Conflict (Alembic)
*   **Symptom:** `sqlalchemy.exc.MissingGreenlet` when running Alembic.
*   **Lesson Learned:** Synchronous tools require synchronous database drivers.
*   **Strategic Resolution:** Implement URL-rewriting logic in `alembic/env.py` to transparently swap the async driver for a sync one during migration tasks.

### Issue 3.3: Incorrect Library API Arguments (ARQ & CrewAI)
*   **Symptoms:** `TypeError` and `AttributeError` from `arq.create_pool` and `RedisSettings`; `ValidationError` from `crewai.Crew(verbose=2)`.
*   **Lesson Learned:** A series of minor API usage errors often points to a larger architectural weakness (e.g., repeated configuration). When fighting with a library's API, re-evaluate the strategy.
*   **Strategic Resolution:**
    1.  **Abstract Volatile APIs:** We built a `TaskQueue` abstraction to hide the complexities of `arq`'s API, providing a stable internal interface.
    2.  **Verify Data Types:** Always ensure the data types passed to library functions (e.g., `True` for `verbose`, not `2`) match the documented requirements.

### Issue 3.4: Incorrect Data Handling (Return Objects)
*   **Symptom:** `ProgrammingError: type 'CrewOutput' is not supported` when saving to the database.
*   **Lesson Learned:** Do not assume library functions return primitive types. Always inspect the return object.
*   **Strategic Resolution:** Explicitly extract the primitive data needed from the returned object before passing it to another system (e.g., `crew_output.raw`).

### Issue 3.5: Incorrect Worker Registration (ARQ)
*   **Symptom:** `function '...' not found` error in the ARQ worker log.
*   **Root Cause:** A new worker function was defined but not added to the `functions` list in the `WorkerSettings` class.
*   **Lesson Learned:** The list of functions in `WorkerSettings` is the definitive registry of all valid jobs the worker can execute.
*   **Strategic Resolution:** Ensure every new worker function is explicitly added to the `functions` list in `src/crew/worker.py`.

### Issue 3.6: Misplaced Service-Layer Logic
*   **Symptom:** `NameError: name 'Project' is not defined` in `src/crew/service.py`.
*   **Root Cause:** A function responsible for updating the `Project` model was incorrectly placed in the `crew` service layer instead of the `project` service layer, breaking domain separation and causing import errors.
*   **Lesson Learned:** Strictly adhere to domain-driven design. All functions that operate on a specific domain's models should reside within that domain's service file.

---
## Final Strategic Recommendation for Future Sprints

1.  **Abstract Early:** If a third-party library's API is complex, wrap it in a simple, internal abstraction layer.
2.  **Enforce Domain Boundaries:** Strictly maintain the separation of concerns between different domains (e.g., `project` logic stays in the `project` service).
3.  **Single Source of Truth:** Enforce a single source of truth for all configurations.
4.  **Proactive Code Review:** Before testing, perform a quick "dry run" review of the code, specifically checking for `import` statements and API calls, as these have been our most frequent sources of error.
5.  **Verify Data at Boundaries:** Be vigilant about the data types being passed between systems (API -> Service -> Library -> Database).