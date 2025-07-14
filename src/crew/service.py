# src/crew/service.py
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from crewai import Crew
from typing import Any

from .models import CrewRunLog
from src.project.models import Project, Part, Chapter
from .pricing import calculate_cost
from src.core.config import settings
from .agents import create_architect_agent, AGENT_FACTORIES
# We no longer need format_blueprint_as_text
from .tasks import create_outline_task, create_chapter_writing_task
from src.project.service import get_project_by_id, get_chapter_by_id, update_chapter_content
from .schemas import BookOutline

# --- log_crew_run function remains the same ---
async def log_crew_run(
    session: AsyncSession,
    project_id: uuid.UUID,
    initiating_task_name: str,
    usage_metrics: Any,
):
    # ... (This function is unchanged)
    if not usage_metrics: return
    prompt_tokens = getattr(usage_metrics, 'prompt_tokens', 0)
    completion_tokens = getattr(usage_metrics, 'completion_tokens', 0)
    total_tokens = getattr(usage_metrics, 'total_tokens', 0)
    run_cost = calculate_cost(
        model_name=settings.OPENAI_MODEL_NAME,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )
    new_log = CrewRunLog(
        project_id=project_id, initiating_task_name=initiating_task_name,
        model_name=settings.OPENAI_MODEL_NAME, prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens, total_tokens=total_tokens,
        total_cost=run_cost
    )
    session.add(new_log)
    update_stmt = (
        Project.__table__.update().where(Project.id == project_id)
        .values(total_cost=Project.total_cost + run_cost)
    )
    await session.execute(update_stmt)
    await session.commit()
    print(f"📊 Crew Run Logged for '{initiating_task_name}'")


async def run_outline_generation_crew(session: AsyncSession, project_id: uuid.UUID) -> None:
    """Assembles and runs the crew for generating a book outline from raw text."""
    print(f"🚀 Starting architect-driven outline generation for project: {project_id}")
    project = await get_project_by_id(session, project_id=project_id)
    if not project: return

    architect = create_architect_agent(project_data=project)
    task = create_outline_task(agent=architect)
    crew = Crew(agents=[architect], tasks=[task], verbose=True)

    # The input is now the raw text blueprint directly from the project.
    inputs = {'blueprint_text': project.blueprint}

    crew_result = await asyncio.to_thread(crew.kickoff, inputs=inputs)
    structured_outline = crew_result.pydantic

    if isinstance(structured_outline, BookOutline):
        print(f"✅ Pydantic outline generated successfully for project: {project_id}")
        for part_outline in structured_outline.parts:
            new_part = Part(project_id=project.id, part_number=part_outline.part_number, title=part_outline.title, summary=part_outline.summary)
            session.add(new_part)
            await session.flush()
            for chapter_outline in part_outline.chapters:
                new_chapter = Chapter(
                    part_id=new_part.id,
                    chapter_number=chapter_outline.chapter_number,
                    title=chapter_outline.title,
                    brief=chapter_outline.brief.model_dump(),
                    suggested_agent=chapter_outline.suggested_agent
                )
                session.add(new_chapter)
        await session.commit()
        print(f"✅ Database updated with new structure for project: {project_id}")

        token_usage = getattr(crew_result, 'token_usage', None) or getattr(crew_result, 'usage_metrics', None)
        if token_usage:
            task_name = "Book Outline Generation (Architect)"
            await log_crew_run(session=session, project_id=project.id,  initiating_task_name=task_name, usage_metrics=token_usage)
    else:
        print(f"❌ Outline generation failed or returned unexpected type: {type(structured_outline)}")


# --- run_chapter_generation_crew remains the same ---
async def run_chapter_generation_crew(session: AsyncSession, chapter_id: uuid.UUID) -> None:
    # ... (This function is unchanged)
    print(f"🚀 Starting content generation for chapter: {chapter_id}")
    chapter = await get_chapter_by_id(session, chapter_id=chapter_id)
    if not chapter or not chapter.part or not chapter.part.project: return
    project = chapter.part.project
    agent_factory = AGENT_FACTORIES.get(chapter.suggested_agent)
    if not agent_factory: return
    agent_to_use = agent_factory(project_data=project)
    task = create_chapter_writing_task(agent=agent_to_use, chapter_data=chapter)
    crew = Crew(agents=[agent_to_use], tasks=[task], verbose=True)
    result = await asyncio.to_thread(crew.kickoff)
    crew_output = result.raw
    if isinstance(crew_output, str):
        await update_chapter_content(session, chapter_id=chapter.id, content=crew_output)
        print(f"✅ Content generated successfully for chapter: {chapter_id}")
        token_usage = getattr(result, 'token_usage', None) or getattr(result, 'usage_metrics', None)
        if token_usage:
            task_name = f"Chapter Generation: Ch {chapter.chapter_number} - {chapter.title[:30]}..."
            await log_crew_run(
                session=session,
                project_id=project.id,
                initiating_task_name=task_name,
                usage_metrics=token_usage
            )
    else:
        print(f"❌ Content generation failed for chapter: {chapter_id}.")