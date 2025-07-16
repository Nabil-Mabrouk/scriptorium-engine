# src/project/part_router.py
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from . import service

# Import the necessary schemas and dependencies
from .schemas import PartReadWithChapters
from src.crew.schemas import ChapterListOutline
from .dependencies import valid_part_id

router = APIRouter(
    prefix="/parts",
    tags=["Parts"]
)

# NEW: Endpoint for Phase 2 Validation
@router.put(
    "/{part_id}/finalize-chapters",
    response_model=PartReadWithChapters,
    summary="Finalize the Chapter structure for a Part"
)
async def finalize_part_chapters(
    part_id: uuid.UUID,
    validated_chapters: ChapterListOutline, # The user submits the approved structure
    session: AsyncSession = Depends(get_db_session)
):
    """
    Takes a validated list of Chapters for a specific Part and creates the
    official Chapter records in the database.
    """
    updated_part = await service.finalize_chapter_structure(
        session=session,
        part_id=part_id,
        validated_chapters=validated_chapters
    )
    if not updated_part:
        raise HTTPException(status_code=404, detail="Part not found")
    return updated_part