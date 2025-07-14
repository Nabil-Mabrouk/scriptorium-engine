# src/project/service.py
import uuid
import re # Import the regular expression module
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, subqueryload
import re
from .models import Project, Part, Chapter # Ensure Chapter is imported if needed later
from .schemas import ProjectCreate

async def create_project(session: AsyncSession, project_data: ProjectCreate) -> Project:
    new_project = Project(**project_data.model_dump())
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return new_project

async def get_project_by_id(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalars().first()

async def update_project_summary_outline(session: AsyncSession, project_id: uuid.UUID, outline: str) -> Project | None:
    project = await get_project_by_id(session, project_id)
    if project:
        project.summary_outline = outline
        await session.commit()
        await session.refresh(project)
    return project

async def get_chapter_by_id(session: AsyncSession, chapter_id: uuid.UUID) -> Chapter | None:
    """Retrieves a single chapter by its ID, and pre-loads the project relationship."""
    result = await session.execute(
        select(Chapter).options(
            # This tells SQLAlchemy to fetch the related Part,
            # and from that Part, fetch its related Project in one go.
            selectinload(Chapter.part).selectinload(Part.project)
        ).where(Chapter.id == chapter_id)
    )
    return result.scalars().first()

async def update_chapter_content(session: AsyncSession, chapter_id: uuid.UUID, content: str) -> Chapter | None:
    """Updates the content of a specific chapter and sets its status to 'Complete'."""
    chapter = await get_chapter_by_id(session, chapter_id)
    if chapter:
        chapter.content = content
        chapter.status = "Complete" # Update status upon successful generation
        await session.commit()
        await session.refresh(chapter)
    return chapter

async def get_project_with_details(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Retrieves a project and eagerly loads its parts and their chapters."""
    result = await session.execute(
        select(Project).options(
            # Use subqueryload for the one-to-many relationships for efficiency
            subqueryload(Project.parts).subqueryload(Part.chapters)
        ).where(Project.id == project_id)
    )
    return result.scalars().first()