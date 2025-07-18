# src/crew/router.py
import uuid
from typing import List # Import List for the new endpoint's response model
from fastapi import APIRouter, Depends, status, Body

from src.core.task_queue import task_queue
from src.project.dependencies import valid_project_id, valid_part_id
from src.project.schemas import ProjectRead, PartRead
from src.crew.schemas import TaskStatus, FinalizationRequest
from arq.jobs import Job
from fastapi_limiter.depends import RateLimiter

# NEW IMPORT: Import AGENT_ROSTER from src.crew.agents
from src.crew.agents import AGENT_ROSTER

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
# Replace your existing get_job_status function with this one# The corrected status endpoint
# Replace your existing get_job_status function with this one
@router.get("/status/{job_id}", response_model=TaskStatus, summary="Get Job Status")
async def get_job_status(job_id: str):
    """
    Checks the status of a background job using the direct status() method.
    """
    job = Job(job_id, task_queue.pool)
    
    status_string = await job.status()
    result_data = None
    error_message = None

    if status_string == 'complete':
        # Retrieve the job result if completed successfully
        try:
            result_data = await job.result()
        except Exception as e:
            # If retrieving the result itself fails, log and consider it an error
            print(f"❌ Error retrieving result for job {job_id}: {e}")
            error_message = f"Failed to retrieve job result: {str(e)}"
            status_string = "error_retrieving_result" # Or change to 'failed' if appropriate
            
    elif status_string == 'failed':
        # Retrieve the exception/error message if the job failed
        try:
            # arq's job.result() on a failed job will return the exception object or message
            error_message = str(await job.result())
        except Exception as e:
            print(f"❌ Error retrieving error message for job {job_id}: {e}")
            error_message = f"Failed to retrieve error details: {str(e)}"
    
    # Check for the double-prefix issue mentioned in analysis:
    # If this endpoint path appears as /crew/crew/status in OpenAPI, the base router
    # prefix might be applied twice. The correct path in router.py would be:
    # router = APIRouter(prefix="/crew", tags=["Crew AI"])
    # @router.get("/status/{job_id}") # This is correct for FastAPI's prefixing.
    # The OpenAPI spec might show /crew/status/{job_id} after FastAPI compiles.
    # If your openapi-typescript output still shows /crew/crew/status/{job_id},
    # it means FastAPI itself is generating that, which is unusual for a simple prefix.
    # Double-check `main.py` if `crew_router` is included multiple times or if
    # the prefix is misconfigured there. For now, we assume `get /crew/status/{job_id}` is correct.

    return TaskStatus(
        job_id=job_id,
        status=status_string,
        result=result_data,
        error=error_message
    )

# NEW ENDPOINT: Get list of available AI agent names
@router.get(
    "/agents",
    response_model=List[str],
    summary="Get Available AI Agent Names",
    dependencies=[Depends(RateLimiter(times=100, seconds=60))] # High rate limit as it's a static list
)
async def get_agent_names():
    """
    Retrieves a list of all defined AI agent names from the AGENT_ROSTER.
    This is used by the frontend to populate dropdowns for suggested agents.
    """
    return list(AGENT_ROSTER.keys())