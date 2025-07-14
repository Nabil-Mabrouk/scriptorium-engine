# src/crew/worker.py
import uuid
from arq.connections import RedisSettings # Import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionFactory
from src.core.config import settings
from .service import run_outline_generation_crew, run_chapter_generation_crew # Import new service

# Import the task_queue instance
from src.core.task_queue import task_queue


# Configure the task queue with the global settings when this module is loaded
task_queue.configure(settings.REDIS_URL)

async def outline_generation_worker(ctx, project_id: uuid.UUID) -> dict:
    """
    ARQ worker function to generate a book outline.
    This function is called by the ARQ process, not the main API.
    """
    session: AsyncSession = AsyncSessionFactory()
    try:
        await run_outline_generation_crew(session, project_id=project_id)
        return {"status": "success", "project_id": str(project_id)}
    except Exception as e:
        # Basic error handling
        print(f"Error during outline generation for project {project_id}: {e}")
        return {"status": "error", "project_id": str(project_id), "error": str(e)}
    finally:
        await session.close()

async def chapter_generation_worker(ctx, chapter_id: uuid.UUID) -> dict:
    """ARQ worker function to generate content for a single chapter."""
    session: AsyncSession = AsyncSessionFactory()
    try:
        await run_chapter_generation_crew(session, chapter_id=chapter_id)
        return {"status": "success", "chapter_id": str(chapter_id)}
    except Exception as e:
        print(f"Error during chapter generation for {chapter_id}: {e}")
        return {"status": "error", "chapter_id": str(chapter_id), "error": str(e)}
    finally:
        await session.close()

class WorkerSettings:
    """
    Defines the settings for the ARQ worker.
    This class is referenced when starting the worker from the command line.
    """
    # List of functions that the worker can execute.
    functions = [outline_generation_worker, chapter_generation_worker]
    # Connection settings for Redis.
    # Reference the centrally configured RedisSettings object
    redis_settings = task_queue.redis_settings