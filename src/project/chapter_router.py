# src/project/chapter_router.py
import uuid
from fastapi import APIRouter, Depends, status

from src.core.task_queue import task_queue
from src.project.schemas import ChapterRead
from src.crew.schemas import TaskStatus
# It needs the chapter dependency
from .dependencies import valid_chapter_id 

router = APIRouter(prefix="/chapters", tags=["Chapters"])

@router.post(
    "/{chapter_id}/generate",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    summary="Queue Chapter Content Generation"
)
async def queue_chapter_generation(
    # This is where valid_chapter_id is used
    chapter: ChapterRead = Depends(valid_chapter_id),
):
    """
    Queues a background job to write the content for a specific chapter
    using the dynamically selected AI agent.
    """
    job = await task_queue.enqueue("chapter_generation_worker", chapter.id)
    return TaskStatus(job_id=job.job_id, status="queued")