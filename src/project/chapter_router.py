# src/project/chapter_router.py
# src/project/chapter_router.py
import uuid
# NEW: Import HTTPException
from fastapi import APIRouter, Depends, status, Body, HTTPException
from pydantic import BaseModel, Field

from src.core.task_queue import task_queue
from src.project.schemas import ChapterRead
from src.crew.schemas import TaskStatus
from src.project.dependencies import valid_chapter_id
from fastapi_limiter.depends import RateLimiter
from src.project import service 
# NEW: Import AsyncSession and get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db_session
router = APIRouter(prefix="/chapters", tags=["Chapters"])

class ChapterReviewRequest(BaseModel):
    content: str # Allow human to submit edited content
    status: str = "CONTENT_REVIEWED" # Default status after review

@router.put(
    "/{chapter_id}/review",
    response_model=ChapterRead, # Return the updated chapter
    summary="Review and Finalize Chapter Content"
)
async def review_chapter_content(
    chapter: ChapterRead = Depends(valid_chapter_id),
    review_data: ChapterReviewRequest = Body(...),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Allows a user to review and optionally edit generated chapter content,
    and set its status to 'CONTENT_REVIEWED'. A new version is saved.
    """
    updated_chapter = await service.update_chapter_content(
        session=session,
        chapter_id=chapter.id,
        content=review_data.content # Pass the reviewed/edited content
    )
    # The update_chapter_content already sets status to CONTENT_GENERATED
    # If review_data.status is CONTENT_REVIEWED, we can update it explicitly
    if updated_chapter and review_data.status == "CONTENT_REVIEWED":
        updated_chapter = await service.update_chapter_status(
            session=session,
            chapter_id=updated_chapter.id,
            new_status="CONTENT_REVIEWED"
        )
    if not updated_chapter:
        raise HTTPException(status_code=404, detail="Chapter not found after update")
    return updated_chapter

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

class ChapterReviewRequest(BaseModel):
    content: str = Field(..., description="The reviewed or edited content for the chapter.")
    # Frontend can explicitly send "CONTENT_REVIEWED" or "CONTENT_GENERATED" (if user undoes edits)
    new_status: str = Field("CONTENT_REVIEWED", description="The new status for the chapter after review (e.g., 'CONTENT_REVIEWED').")

@router.put(
    "/{chapter_id}/review",
    response_model=ChapterRead, # Return the updated chapter
    summary="Review and Finalize Chapter Content"
)
async def review_chapter_content(
    chapter: ChapterRead = Depends(valid_chapter_id), # Validates chapter_id and gets ChapterRead object
    review_data: ChapterReviewRequest = Body(...),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Allows a user to review and optionally edit generated chapter content,
    and set its status. A new version of the content is saved.
    """
    # Save the new content (this also creates a new version)
    updated_chapter = await service.update_chapter_content(
        session=session,
        chapter_id=chapter.id,
        content=review_data.content # Pass the reviewed/edited content
        # We don't have token_count here, it's specific to generation, not review
        # You could add a 'source: str' to ChapterVersion to differentiate AI vs Human
    )

    # Update the chapter status based on the request
    if updated_chapter:
        updated_chapter = await service.update_chapter_status(
            session=session,
            chapter_id=updated_chapter.id,
            new_status=review_data.new_status
        )
    
    if not updated_chapter:
        raise HTTPException(status_code=404, detail=f"Chapter with ID {chapter.id} not found or failed to update.")
    
    return updated_chapter

