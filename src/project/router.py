# src/project/router.py
import uuid
from typing import List # Make sure List is imported
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from . import service
from .schemas import ProjectCreate, ProjectRead, ProjectDetailRead
from src.crew.schemas import PartListOutline
from .dependencies import valid_project_id

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

# This is the endpoint that was likely missing or incorrect
@router.get(
    "", # Correct path for the collection
    response_model=List[ProjectRead],
    summary="Get All Projects"
)
async def get_all_projects(
    session: AsyncSession = Depends(get_db_session)
):
    """Retrieves a list of all projects."""
    #projects = await service.get_all_projects(session=session)

    # # DEBUG STEP: Print what the database returns
    # print(f"--- 2. Raw data from database: {projects} ---")
    db_projects = await service.get_all_projects(session=session)
    # # DEBUG STEP: Try to inspect the attributes of the first project if it exists
    # if projects:
    #     first_project = projects[0]
    #     print(f"--- 3. Attributes of first project object: ---")
    #     # The __dict__ shows the raw internal data of the SQLAlchemy object
    #     print(first_project.__dict__) 
    response_data = [ProjectRead.model_validate(p) for p in db_projects] 
    print(f"--- 2. Raw data from database: {response_data} ---")  
    return response_data

@router.post(
    "", # Correct path for the collection
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
