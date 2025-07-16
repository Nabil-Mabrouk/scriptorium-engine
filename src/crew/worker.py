# src/crew/worker.py
import uuid
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionFactory
from src.core.config import settings
from .service import (
    run_part_generation_crew,
    run_chapter_detailing_crew,
    run_chapter_generation_crew,
    run_transition_analysis_crew,
    run_finalization_crew
)
from src.core.task_queue import task_queue

task_queue.configure(settings.REDIS_URL)

async def part_generation_worker(ctx, project_id: uuid.UUID) -> dict:
    """Worker for generating book parts"""
    async with AsyncSessionFactory() as session: # Correct way to manage session
        try:
            success = await run_part_generation_crew(session, project_id)
            return {
                "status": "success" if success else "failure",
                "project_id": str(project_id)
            }
        except Exception as e:
            print(f"❌ Part generation error for project {project_id}: {e}")
            return {
                "status": "error",
                "project_id": str(project_id),
                "error": str(e)
            }


async def chapter_detailing_worker(ctx, part_id: uuid.UUID) -> dict:
    """Worker for generating chapter details"""
    async with AsyncSessionFactory() as session: # Correct way to manage session
        try:
            await run_chapter_detailing_crew(session, part_id)
            return {"status": "success", "part_id": str(part_id)}
        except Exception as e:
            print(f"❌ Chapter detailing error for part {part_id}: {e}")
            return {
                "status": "error",
                "part_id": str(part_id),
                "error": str(e)
            }


async def chapter_generation_worker(ctx, chapter_id: uuid.UUID) -> dict:
    """Worker for generating chapter content"""
    async with AsyncSessionFactory() as session: # Correct way to manage session
        try:
            await run_chapter_generation_crew(session, chapter_id)
            return {"status": "success", "chapter_id": str(chapter_id)}
        except Exception as e:
            print(f"❌ Chapter generation error for {chapter_id}: {e}")
            return {
                "status": "error",
                "chapter_id": str(chapter_id),
                "error": str(e)
            }


async def transition_analysis_worker(ctx, chapter_id: uuid.UUID) -> dict:
    """Worker for analyzing chapter transitions"""
    async with AsyncSessionFactory() as session: # Correct way to manage session
        try:
            await run_transition_analysis_crew(session, chapter_id)
            return {"status": "success", "chapter_id": str(chapter_id)}
        except Exception as e:
            print(f"❌ Transition analysis error for chapter {chapter_id}: {e}")
            return {
                "status": "error",
                "chapter_id": str(chapter_id),
                "error": str(e)
            }


async def finalization_worker(ctx, project_id: uuid.UUID, task_type: str) -> dict:
    """Worker for writing introduction/conclusion"""
    async with AsyncSessionFactory() as session: # Correct way to manage session
        try:
            await run_finalization_crew(session, project_id, task_type)
            return {
                "status": "success",
                "project_id": str(project_id),
                "task": task_type
            }
        except Exception as e:
            print(f"❌ Finalization error ({task_type}) for project {project_id}: {e}")
            return {
                "status": "error",
                "project_id": str(project_id),
                "error": str(e)
            }

class WorkerSettings:
    """ARQ worker settings with all task handlers"""
    functions = [
        part_generation_worker,
        chapter_detailing_worker,
        chapter_generation_worker,
        transition_analysis_worker,
        finalization_worker
    ]
    redis_settings = task_queue.redis_settings