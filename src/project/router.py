# src/project/router.py
import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from . import service

# UPDATED: Import the schemas needed for the new endpoint
from .schemas import ProjectCreate, ProjectRead, ProjectDetailRead
from src.crew.schemas import PartListOutline # This schema is for the request body

from .dependencies import valid_project_id

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book project"
)
async def create_new_project(
    project_data: ProjectCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """Creates a new project record from a user's 'raw_blueprint'."""
    new_project = await service.create_project(session=session, project_data=project_data)
    return new_project

@router.get(
    "/{project_id}",
    response_model=ProjectDetailRead,
    summary="Get Full Project Details"
)
async def get_project_details(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves the full details of a project, including all its
    parts and chapters, for display on a dashboard.
    """
    project = await service.get_project_with_details(session=session, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

# NEW: Endpoint for Phase 1 Validation
@router.put(
    "/{project_id}/finalize-parts",
    response_model=ProjectDetailRead,
    summary="Finalize the Part structure of a book"
)
async def finalize_project_parts(
    project_id: uuid.UUID,
    validated_parts: PartListOutline, # The user submits the approved structure
    session: AsyncSession = Depends(get_db_session)
):
    """
    Takes a validated list of Parts from the user and creates the official
    Part records in the database, finalizing the book's high-level structure.
    """
    updated_project = await service.finalize_part_structure(
        session=session,
        project_id=project_id,
        validated_parts=validated_parts
    )
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project
