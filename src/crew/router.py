# src/crew/router.py
import uuid
from fastapi import APIRouter, Depends, status

from src.core.task_queue import task_queue
# It only needs the project dependency
from src.project.dependencies import valid_project_id 
from src.project.schemas import ProjectRead
from .schemas import TaskStatus

router = APIRouter(prefix="/crew", tags=["Crew AI"])

@router.post(
    "/generate-outline/{project_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=TaskStatus,
    summary="Generate or Refine Book Outline"
)
async def queue_outline_generation(
    project: ProjectRead = Depends(valid_project_id),
):
    """
    Queues a background job for the Architect AI. This job handles both
    creation from scratch or refinement of an expert blueprint, and populates
    the database with the structured outline.
    """
    job = await task_queue.enqueue("outline_generation_worker", project.id)
    return TaskStatus(job_id=job.job_id, status="queued")