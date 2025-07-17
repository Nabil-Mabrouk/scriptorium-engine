# src/crew/router.py
import uuid
from fastapi import APIRouter, Depends, status, Body

from src.core.task_queue import task_queue
from src.project.dependencies import valid_project_id, valid_part_id
from src.project.schemas import ProjectRead, PartRead
from src.crew.schemas import TaskStatus, FinalizationRequest
from arq.jobs import Job # Import the Job class from arq
# NEW: Import RateLimiter
from fastapi_limiter.depends import RateLimiter
from .schemas import TaskStatus 
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
# The corrected status endpoint
# Replace your existing get_job_status function with this one
@router.get("/status/{job_id}", response_model=TaskStatus, summary="Get Job Status")
async def get_job_status(job_id: str):
    """
    Checks the status of a background job using the direct status() method.
    """
    # 1. Create a Job instance
    job = Job(job_id, task_queue.pool)
    
    # 2. Directly await the status string (e.g., 'in_progress', 'complete')
    status_string = await job.status()
    
    # The job.status() method itself handles cases where the job is not found
    # by returning the string 'not_found'.
    
    # 3. Return the status in the TaskStatus model
    return TaskStatus(job_id=job_id, status=status_string)