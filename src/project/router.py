import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from . import service
from .schemas import ProjectCreate, ProjectRead, ProjectDetailRead, PartReadWithChapters
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
    """Creates a new project record from a user's 'blueprint'."""
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

