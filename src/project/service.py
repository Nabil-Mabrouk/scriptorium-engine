# src/project/service.py
import uuid
import logging # NEW: Import logging module
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, subqueryload
from sqlalchemy import delete, update # Ensure update is imported for potential future use

from .models import Project, Part, Chapter, ChapterVersion
from .schemas import ProjectCreate, ProjectRead # Add ProjectRead here if it's not already imported
from src.crew.schemas import PartListOutline, ChapterListOutline # Ensure these are imported
from typing import List # Import List

# NEW: Get a logger instance for this module
logger = logging.getLogger(__name__)


async def get_all_projects(session: AsyncSession) -> List[Project]:
    """Retrieves all projects."""
    logger.debug("Fetching all projects.")
    result = await session.execute(select(Project).order_by(Project.id.desc()))
    projects = result.scalars().all()
    logger.info(f"Retrieved {len(projects)} projects.")
    return projects

async def create_project(session: AsyncSession, project_data: ProjectCreate) -> Project:
    """Creates a new project record from a user's raw text blueprint."""
    new_project = Project(**project_data.model_dump())
    session.add(new_project)
    await session.commit()
    await session.refresh(new_project)
    logger.info(f"New project created with ID: {new_project.id}")
    return new_project

async def get_project_by_id(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Retrieves a single project by its ID."""
    logger.debug(f"Fetching project with ID: {project_id}")
    result = await session.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if project:
        logger.info(f"Project {project_id} found.")
    else:
        logger.warning(f"Project {project_id} not found.")
    return project

async def get_project_with_details(session: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Retrieves a project and eagerly loads its parts and their chapters."""
    logger.debug(f"Fetching project with details for ID: {project_id}")
    result = await session.execute(
        select(Project).options(
            subqueryload(Project.parts).subqueryload(Part.chapters)
        ).where(Project.id == project_id)
    )
    project = result.scalars().first()
    if project:
        logger.info(f"Project {project_id} with details found.")
    else:
        logger.warning(f"Project {project_id} with details not found.")
    return project

async def get_part_by_id(session: AsyncSession, part_id: uuid.UUID) -> Part | None:
    """Retrieves a single part by its ID, including its parent project."""
    logger.debug(f"Fetching part with ID: {part_id}")
    result = await session.execute(
        select(Part).options(selectinload(Part.project)).where(Part.id == part_id)
    )
    part = result.scalars().first()
    if part:
        logger.info(f"Part {part_id} found.")
    else:
        logger.warning(f"Part {part_id} not found.")
    return part

async def get_chapter_by_id(session: AsyncSession, chapter_id: uuid.UUID) -> Chapter | None:
    """Retrieves a single chapter by its ID, and pre-loads its parent part and project."""
    logger.debug(f"Fetching chapter with ID: {chapter_id}")
    result = await session.execute(
        select(Chapter).options(
            selectinload(Chapter.part).selectinload(Part.project)
        ).where(Chapter.id == chapter_id)
    )
    chapter = result.scalars().first()
    if chapter:
        logger.info(f"Chapter {chapter_id} found.")
    else:
        logger.warning(f"Chapter {chapter_id} not found.")
    return chapter

async def finalize_part_structure(
    session: AsyncSession, project_id: uuid.UUID, validated_parts: PartListOutline
) -> Project:
    """
    Deletes existing parts for a project and creates new ones based on the
    user-validated structure. Updates the project status.
    """
    project = await get_project_with_details(session, project_id) # Using get_project_with_details for comprehensive load
    if not project:
        logger.error(f"Cannot finalize parts: Project {project_id} not found.")
        return None

    await session.execute(
        delete(Part).where(Part.project_id == project.id)
    )
    logger.info(f"Existing parts for project {project_id} cleared from database.")
    
    for part_data in validated_parts.parts:
        new_part = Part(
            project_id=project.id,
            part_number=part_data.part_number,
            title=part_data.title,
            summary=part_data.summary,
            status="DEFINED"
        )
        session.add(new_part)
        logger.debug(f"Added new part: {new_part.title} (Part {new_part.part_number}) to project {project_id}")

    project.status = "PARTS_VALIDATED"

    # --- UPDATED STRATEGIC LOGIC: Clear dedicated draft fields after finalization ---
    project.draft_parts_outline = None # Clear draft after it's finalized into real parts
    project.draft_chapters_outline = None # Also clear chapter drafts if re-finalizing parts
    logger.debug(f"Cleared draft_parts_outline and draft_chapters_outline for project {project_id} after parts finalization.")
    # --- END UPDATED STRATEGIC LOGIC ---

    session.add(project) # Mark project as dirty
    await session.commit()
    await session.refresh(project)
    logger.info(f"Part structure finalized for project {project_id}. Status: {project.status}")

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
        logger.error(f"Cannot finalize chapters: Part {part_id} not found.")
        return None

    await session.execute(
        delete(Chapter).where(Chapter.part_id == part.id)
    )
    logger.info(f"Existing chapters for part {part_id} cleared.")

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
        logger.debug(f"Added new chapter: {new_chapter.title} to part {part_id}")

    part.status = "CHAPTERS_VALIDATED"
    
    # --- UPDATED STRATEGIC LOGIC: Clear specific chapter draft after finalization ---
    project = part.project # Need project object to update its draft_chapters_outline
    if project and project.draft_chapters_outline: # Check if the map exists
        current_draft_chapters_map = project.draft_chapters_outline
        if str(part.id) in current_draft_chapters_map:
            del current_draft_chapters_map[str(part.id)]
            logger.debug(f"Cleared draft_chapters_outline for part {part.id} from project {project.id} after chapter finalization.")
            
            # If the map becomes empty, set the entire draft_chapters_outline to None
            if not current_draft_chapters_map:
                project.draft_chapters_outline = None
                logger.debug(f"Set draft_chapters_outline to None as it became empty for project {project.id}.")
            else:
                # Explicitly re-assign if the map itself changed (item deleted)
                project.draft_chapters_outline = current_draft_chapters_map
                logger.debug(f"Re-assigned draft_chapters_outline for project {project.id} after deleting part's entry.")
        
        session.add(project) # Mark project as dirty
    # --- END UPDATED STRATEGIC LOGIC ---

    await session.commit()
    logger.info(f"Chapter structure finalized for part {part_id}. Status: {part.status}")

    refreshed_part_stmt = select(Part).options(
        selectinload(Part.chapters)
    ).where(Part.id == part_id)
    
    result = await session.execute(refreshed_part_stmt)
    refreshed_part = result.scalars().first()
    
    if refreshed_part:
        logger.info(f"Refreshed part {part_id} with {len(refreshed_part.chapters)} new chapters for response.")
    else:
        logger.error(f"Failed to re-fetch part {part_id} after finalizing chapters.")

    return refreshed_part
async def update_project_summary_outline(session: AsyncSession, project_id: uuid.UUID, outline: str) -> Project | None:
    """(Legacy) Updates the summary_outline field of a project."""
    logger.info(f"Attempting to update summary outline for project {project_id}.")
    project = await get_project_by_id(session, project_id)
    if project:
        project.summary_outline = outline
        await session.commit()
        await session.refresh(project)
        logger.info(f"Summary outline updated for project {project_id}.")
    else:
        logger.warning(f"Failed to update summary outline: Project {project_id} not found.")
    return project

async def update_chapter_status(session: AsyncSession, chapter_id: uuid.UUID, new_status: str) -> Chapter | None:
    """Updates the status of a specific chapter."""
    logger.info(f"Updating status for chapter {chapter_id} to '{new_status}'.")
    chapter = await get_chapter_by_id(session, chapter_id)
    if chapter:
        chapter.status = new_status
        await session.commit()
        await session.refresh(chapter)
        logger.info(f"Chapter {chapter_id} status updated to '{new_status}'.")
    else:
        logger.warning(f"Failed to update status: Chapter {chapter_id} not found.")
    return chapter

async def update_chapter_content(session: AsyncSession, chapter_id: uuid.UUID, content: str, token_count: int | None = None) -> Chapter | None:
    """Updates the content of a specific chapter and also creates a new ChapterVersion record."""
    logger.info(f"Updating content for chapter {chapter_id}. Token count: {token_count}")
    chapter = await get_chapter_by_id(session, chapter_id)
    if chapter:
        # Create a new version record
        new_version = ChapterVersion(
            chapter_id=chapter.id,
            content=content,
            token_count=token_count
        )
        session.add(new_version)
        logger.debug(f"Created new version for chapter {chapter_id}.")
        
        chapter.content = content # Update the current content
        await session.commit()
        await session.refresh(chapter)
        logger.info(f"Content and new version saved for chapter {chapter_id}.")
    else:
        logger.warning(f"Failed to update content: Chapter {chapter_id} not found.")
    return chapter