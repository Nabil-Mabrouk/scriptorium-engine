# src/crew/router.py
import uuid
from fastapi import APIRouter, Depends, status, Body

from src.core.task_queue import task_queue
from src.project.dependencies import valid_project_id, valid_part_id
from src.project.schemas import ProjectRead, PartRead
from src.crew.schemas import TaskStatus, FinalizationRequest

# NEW: Import RateLimiter
from fastapi_limiter.depends import RateLimiter

router = APIRouter(prefix="/crew", tags=["Crew AI"])

# --- Phase 1 Endpoint ---
@router.post(
    "/generate-parts/{project_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    summary="Generate High-Level Part Structure",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))] # NEW: 5 requests per minute
)
async def queue_part_generation(
    project: ProjectRead = Depends(valid_project_id),
):
    """
    Queues a background job for the Architect AI to generate a high-level
    list of Parts and their summaries from the project's raw blueprint.
    """
    job = await task_queue.enqueue("part_generation_worker", project.id)
    return TaskStatus(job_id=job.job_id, status="queued")

# --- NEW: Phase 2 Endpoint ---
@router.post(
    "/generate-chapters/{part_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    summary="Generate Detailed Chapter Outline for a Part",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))] # NEW: 10 requests per minute
)
async def queue_chapter_detailing(
    part: PartRead = Depends(valid_part_id),
):
    """
    Queues a background job to generate a detailed chapter outline for a
    specific part of the book.
    """
    job = await task_queue.enqueue("chapter_detailing_worker", part.id)
    return TaskStatus(job_id=job.job_id, status="queued")

# NEW: Phase 5 Endpoint
@router.post(
    "/projects/{project_id}/finalize", # Note: This path is inconsistent with prefix, but let's follow existing.
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    summary="Generate Introduction or Conclusion",
    dependencies=[Depends(RateLimiter(times=2, seconds=300))] # NEW: 2 requests per 5 minutes (finalization is heavy)
)
async def queue_finalization(
    project: ProjectRead = Depends(valid_project_id),
    request: FinalizationRequest = Body(...)
):
    """
    Queues a background job for the Theorist AI to write the book's
    introduction or conclusion based on the full content.
    """
    job = await task_queue.enqueue(
        "finalization_worker",
        project.id,
        request.task_type
    )
    return TaskStatus(job_id=job.job_id, status="queued")

# backend router
@router.get("/crew/status/{job_id}")
async def job_status(job_id: str):
    job = await task_queue.pool.get_job(job_id)
    return {"status": job.status if job else "error"}