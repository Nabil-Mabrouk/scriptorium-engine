# src/project/chapter_router.py
import uuid
from fastapi import APIRouter, Depends, status

from src.core.task_queue import task_queue
from src.project.schemas import ChapterRead
from src.crew.schemas import TaskStatus
from src.project.dependencies import valid_chapter_id

# NEW: Import RateLimiter
from fastapi_limiter.depends import RateLimiter

router = APIRouter(prefix="/chapters", tags=["Chapters"])

@router.post(
    "/{chapter_id}/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    summary="Queue Chapter Content Generation",
    dependencies=[Depends(RateLimiter(times=20, seconds=60))] # NEW: 20 requests per minute (can be many chapters)
)
async def queue_chapter_generation(
    chapter: ChapterRead = Depends(valid_chapter_id),
):
    """
    Queues a background job to write the content for a specific chapter
    using the dynamically selected AI agent.
    """
    job = await task_queue.enqueue("chapter_generation_worker", chapter.id)
    return TaskStatus(job_id=job.job_id, status="queued")


# --- NEW ENDPOINT ---
@router.post(
    "/{chapter_id}/analyze-transition",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    summary="Queue Transition Analysis",
    dependencies=[Depends(RateLimiter(times=30, seconds=60))] # NEW: Higher rate for analysis
)
async def queue_transition_analysis(
    chapter: ChapterRead = Depends(valid_chapter_id),
):
    """
    Queues a background job for the Continuity Editor AI to analyze the
    narrative flow between this chapter and the one preceding it.
    The feedback is saved directly to the chapter in the database.
    """
    job = await task_queue.enqueue("transition_analysis_worker", chapter.id)
    return TaskStatus(job_id=job.job_id, status="queued")