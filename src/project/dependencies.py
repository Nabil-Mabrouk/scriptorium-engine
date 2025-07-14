import uuid
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from . import service

from .schemas import ProjectRead, ChapterRead

async def valid_project_id(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session)
) -> ProjectRead:
    """
    Dependency that validates a project exists and returns it.
    Raises a 404 HTTPException if the project is not found.
    """
    project = await service.get_project_by_id(session=session, project_id=project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID {project_id} not found."
        )
    return project

async def valid_chapter_id(
    chapter_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session)
) -> ChapterRead:
    """
    Dependency that validates a chapter exists and returns it.
    Raises a 404 HTTPException if the chapter is not found.
    """
    chapter = await service.get_chapter_by_id(session=session, chapter_id=chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with ID {chapter_id} not found."
        )
    return chapter