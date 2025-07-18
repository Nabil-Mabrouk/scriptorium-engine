# src/crew/worker.py
import uuid
import logging # NEW: Import logging module
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
from src.core.task_queue import task_queue # Ensure task_queue is imported and configured


# NEW: Get a logger instance for this module
logger = logging.getLogger(__name__)

# Configure task_queue when the worker module is imported, before WorkerSettings uses it
# This ensures redis_settings is available for ARQ.
task_queue.configure(settings.REDIS_URL)


async def part_generation_worker(ctx, project_id: uuid.UUID) -> dict:
    """Worker for generating book parts"""
    logger.info(f"Worker received part_generation job for project {project_id}")
    async with AsyncSessionFactory() as session:
        try:
            success = await run_part_generation_crew(session, project_id)
            status_msg = "success" if success else "failure"
            logger.info(f"Part generation job for project {project_id} finished with status: {status_msg}")
            return {
                "status": status_msg,
                "project_id": str(project_id)
            }
        except Exception as e:
            logger.exception(f"❌ Part generation worker encountered an error for project {project_id}: {e}")
            return {
                "status": "error",
                "project_id": str(project_id),
                "error": str(e)
            }


async def chapter_detailing_worker(ctx, part_id: uuid.UUID) -> dict:
    """Worker for generating chapter details"""
    logger.info(f"Worker received chapter_detailing job for part {part_id}")
    async with AsyncSessionFactory() as session:
        try:
            success = await run_chapter_detailing_crew(session, part_id)
            status_msg = "success" if success else "failure"
            logger.info(f"Chapter detailing job for part {part_id} finished with status: {status_msg}")
            return {"status": status_msg, "part_id": str(part_id)}
        except Exception as e:
            logger.exception(f"❌ Chapter detailing worker encountered an error for part {part_id}: {e}")
            return {
                "status": "error",
                "part_id": str(part_id),
                "error": str(e)
            }


async def chapter_generation_worker(ctx, chapter_id: uuid.UUID) -> dict:
    """Worker for generating chapter content"""
    logger.info(f"Worker received chapter_generation job for chapter {chapter_id}")
    async with AsyncSessionFactory() as session:
        try:
            success = await run_chapter_generation_crew(session, chapter_id)
            status_msg = "success" if success else "failure"
            logger.info(f"Chapter generation job for chapter {chapter_id} finished with status: {status_msg}")
            return {"status": status_msg, "chapter_id": str(chapter_id)}
        except Exception as e:
            logger.exception(f"❌ Chapter generation worker encountered an error for {chapter_id}: {e}")
            return {
                "status": "error",
                "chapter_id": str(chapter_id),
                "error": str(e)
            }


async def transition_analysis_worker(ctx, chapter_id: uuid.UUID) -> dict:
    """Worker for analyzing chapter transitions"""
    logger.info(f"Worker received transition_analysis job for chapter {chapter_id}")
    async with AsyncSessionFactory() as session:
        try:
            success = await run_transition_analysis_crew(session, chapter_id)
            status_msg = "success" if success else "failure"
            logger.info(f"Transition analysis job for chapter {chapter_id} finished with status: {status_msg}")
            return {"status": status_msg, "chapter_id": str(chapter_id)}
        except Exception as e:
            logger.exception(f"❌ Transition analysis worker encountered an error for chapter {chapter_id}: {e}")
            return {
                "status": "error",
                "chapter_id": str(chapter_id),
                "error": str(e)
            }


async def finalization_worker(ctx, project_id: uuid.UUID, task_type: str) -> dict:
    """Worker for writing introduction/conclusion"""
    logger.info(f"Worker received finalization job ({task_type}) for project {project_id}")
    async with AsyncSessionFactory() as session:
        try:
            success = await run_finalization_crew(session, project_id, task_type)
            status_msg = "success" if success else "failure"
            logger.info(f"Finalization job ({task_type}) for project {project_id} finished with status: {status_msg}")
            return {
                "status": status_msg,
                "project_id": str(project_id),
                "task": task_type
            }
        except Exception as e:
            logger.exception(f"❌ Finalization worker ({task_type}) encountered an error for project {project_id}: {e}")
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