# src/project/service.py
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, subqueryload
from sqlalchemy import delete
from sqlalchemy.orm import selectinload, subqueryload # Ensure this is present
from sqlalchemy import delete, select # Ensure delete and select are present
from .models import Project, Part, Chapter
from .schemas import ProjectCreate
from src.crew.schemas import PartListOutline, ChapterListOutline
async def create_project(session: AsyncSession, project_data: ProjectCreate) -> Project:
    """Creates a new project record from a user's raw text blueprint."""
    new_project = Project(**project_data.model_dump())
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    return new_project

async def get_project_by_id(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Retrieves a single project by its ID."""
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalars().first()

async def get_project_with_details(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Retrieves a project and eagerly loads its parts and their chapters."""
    result = await session.execute(
        select(Project).options(
            subqueryload(Project.parts).subqueryload(Part.chapters)
        ).where(Project.id == project_id)
    )
    return result.scalars().first()

async def get_part_by_id(session: AsyncSession, part_id: uuid.UUID) -> Part | None:
    """Retrieves a single part by its ID, including its parent project."""
    result = await session.execute(
        select(Part).options(selectinload(Part.project)).where(Part.id == part_id)
    )
    return result.scalars().first()

async def get_chapter_by_id(session: AsyncSession, chapter_id: uuid.UUID) -> Chapter | None:
    """Retrieves a single chapter by its ID, and pre-loads its parent part and project."""
    result = await session.execute(
        select(Chapter).options(
            selectinload(Chapter.part).selectinload(Part.project)
        ).where(Chapter.id == chapter_id)
    )
    return result.scalars().first()

async def finalize_part_structure(
    session: AsyncSession, project_id: uuid.UUID, validated_parts: PartListOutline
) -> Project:
    """
    Deletes existing parts for a project and creates new ones based on the
    user-validated structure. Updates the project status.
    """
    project = await get_project_with_details(session, project_id)
    if not project:
        return None

    project.parts.clear()
    await session.flush()

    for part_data in validated_parts.parts:
        new_part = Part(
            project_id=project.id,
            part_number=part_data.part_number,
            title=part_data.title,
            summary=part_data.summary
        )
        project.parts.append(new_part)

    project.status = "PARTS_VALIDATED"
    session.add(project)
    await session.commit()
    await session.refresh(project)

    return project

async def finalize_chapter_structure(
    session: AsyncSession, part_id: uuid.UUID, validated_chapters: ChapterListOutline
) -> Part:
    """
    Deletes existing chapters for a part and creates new ones based on the
    user-validated structure. Updates the part's status.
    """
    part = await get_part_by_id(session, part_id)
    if not part:
        return None

    # Delete existing chapters directly via a query
    await session.execute(
        delete(Chapter).where(Chapter.part_id == part.id)
    )
    # No need for flush here. The commit below will handle the delete before the add.
    # If you were doing more complex operations between delete and add, flush would be good.


    for chapter_data in validated_chapters.chapters:
        new_chapter = Chapter(
            part_id=part.id,
            chapter_number=chapter_data.chapter_number,
            title=chapter_data.title,
            brief=chapter_data.brief.model_dump(),
            suggested_agent=chapter_data.suggested_agent,
            status="BRIEF_COMPLETE"
        )
        session.add(new_chapter)

    part.status = "CHAPTERS_VALIDATED"
    # session.add(part) # No need to add part if it's already a managed object

    await session.commit()

    # NEW: Re-fetch the part, eagerly loading its chapters for the response model
    # This ensures the chapters are loaded within the async session context
    # before the session is yielded/closed by the dependency.
    refreshed_part_stmt = select(Part).options(
        selectinload(Part.chapters)
    ).where(Part.id == part_id)
    
    result = await session.execute(refreshed_part_stmt)
    refreshed_part = result.scalars().first()

    return refreshed_part # Return the eagerly loaded part

async def update_chapter_content(session: AsyncSession, chapter_id: uuid.UUID, content: str) -> Chapter | None:
    """Updates the content of a specific chapter and sets its status to 'Complete'."""
    chapter = await get_chapter_by_id(session, chapter_id)
    if chapter:
        chapter.content = content
        chapter.status = "Complete"
        await session.commit()
        await session.refresh(chapter)
    return chapter

async def update_project_summary_outline(session: AsyncSession, project_id: uuid.UUID, outline: str) -> Project | None:
    """(Legacy) Updates the summary_outline field of a project."""
    project = await get_project_by_id(session, project_id)
    if project:
        project.summary_outline = outline
        await session.commit()
        await session.refresh(project)
    return project