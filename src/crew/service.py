# src/crew/service.py
import asyncio
import uuid
from typing import Any, Dict
from decimal import Decimal

# NEW IMPORT: Circuit Breaker
from circuitbreaker import CircuitBreaker, CircuitBreakerError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete # Ensure delete is imported
from sqlalchemy.orm import selectinload

# NEW IMPORTS for openai-agents
from agents import Runner, RunResult # Make sure 'agents' is correctly importable

# Make sure these are the new Agent instances you defined in agents.py
from .agents import (
    AGENT_INSTANCES,
    architect_part_agent,
    architect_chapter_agent, # Ensure this is imported for chapter detailing
    continuity_editor_agent,
    historian_agent,
    technologist_agent,
    philosopher_agent,
    theorist_agent,
    StringOutput # Your custom Pydantic model for string output
)

from src.core.config import settings
from src.project.models import Project, Part, Chapter
from src.project.service import (
    get_chapter_by_id, get_project_by_id, get_part_by_id,
    get_project_with_details, update_chapter_content,
    update_chapter_status # NEW IMPORT
)
from .schemas import PartListOutline, ChapterListOutline
from .models import CrewRunLog
from .pricing import calculate_cost

# NEW: Configure a circuit breaker for OpenAI API calls
# This will wrap calls to Runner.run
# - failure_threshold: After 3 consecutive failures, the circuit opens.
# - recovery_timeout: The circuit stays open for 60 seconds before attempting a half-open state.
# - expected_exception: The types of exceptions that should trigger a failure.
#   We'll primarily watch for network/connection errors, timeouts.
openai_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60, # seconds
    expected_exception=(
        ConnectionError, # Network issues
        asyncio.TimeoutError, # If requests time out
        # You might add specific exceptions from the openai-agents library if it exposes them for API errors
        # For now, a general Exception catch in _execute_agent_run will trigger the CB for unhandled errors.
    )
)

# NEW: Helper function to execute an agent run, wrapped by the circuit breaker
@openai_circuit_breaker
async def _execute_agent_run(agent_instance: Any, agent_input: str) -> RunResult:
    """Helper function to execute an agent run, wrapped by the circuit breaker."""
    return await Runner.run(agent_instance, agent_input)


async def log_crew_run(
    session: AsyncSession,
    project_id: uuid.UUID,
    initiating_task_name: str,
    usage_metrics: Any, # This is the full RunResult object now
):
    """Logs the metrics of a completed LLM run."""
    # Ensure we have a valid RunResult object and it has raw_responses
    if not usage_metrics or not hasattr(usage_metrics, 'raw_responses') or not usage_metrics.raw_responses:
        print(f"⚠️ Could not log run for '{initiating_task_name}': Invalid RunResult or no raw_responses found.")
        return

    # Extract the specific response (assuming the first one for simplicity for now)
    response_usage = getattr(usage_metrics.raw_responses[0], 'usage', None)

    if not response_usage:
        print(f"⚠️ Could not log run for '{initiating_task_name}': No usage data found in raw_response.")
        return

    prompt_tokens = 0
    completion_tokens = 0

    if hasattr(response_usage, 'input_tokens'):
        prompt_tokens = response_usage.input_tokens
    if hasattr(response_usage, 'output_tokens'):
        completion_tokens = response_usage.output_tokens

    # Fallback if keys are different (less likely with consistent openai-agents usage)
    elif isinstance(response_usage, dict):
        prompt_tokens = response_usage.get('input_tokens', 0)
        completion_tokens = response_usage.get('output_tokens', 0)
        if prompt_tokens == 0 and completion_tokens == 0:
             prompt_tokens = response_usage.get('prompt_tokens', 0)
             completion_tokens = response_usage.get('completion_tokens', 0)


    total_tokens = prompt_tokens + completion_tokens

    run_cost = calculate_cost(
        model_name=settings.DEFAULT_OPENAI_MODEL_NAME, # Use the model name from settings
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    new_log = CrewRunLog(
        project_id=project_id, initiating_task_name=initiating_task_name,
        model_name=settings.DEFAULT_OPENAI_MODEL_NAME, prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens, total_tokens=total_tokens,
        total_cost=run_cost
    )
    session.add(new_log)

    await session.execute(
        update(Project)
        .where(Project.id == project_id)
        .values(total_cost=Project.total_cost + run_cost)
    )

    await session.commit()
    print(f"📊 Run Logged: '{initiating_task_name}' - Tokens: {total_tokens}, Cost: ${run_cost:.6f}")


async def run_part_generation_crew(session: AsyncSession, project_id: uuid.UUID) -> bool:
    print(f"🚀 Starting Part generation for project: {project_id}")
    project = None
    try:
        project = await get_project_by_id(session, project_id=project_id)
        if not project:
            print(f"❌ Part generation failed: Project {project_id} not found.")
            return False
        if not project.raw_blueprint:
            print(f"❌ Part generation failed: Project {project_id} has no raw blueprint defined.")
            return False

        agent_input = project.raw_blueprint

        print(f"🤖 Architect AI preparing part outline for project {project_id}...")

        try: # NEW: Circuit Breaker try block
            run_result: RunResult = await _execute_agent_run(architect_part_agent, agent_input)
        except CircuitBreakerError:
            print(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Part generation for project {project_id}.")
            if project: # Ensure project is defined before trying to update status
                project.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e: # Catch other direct agent execution errors (e.g., API key invalid)
            print(f"❌ Error during agent execution for Part generation: {str(e)}")
            # Re-raise to be caught by the outer try-except for general error handling and traceback
            raise

        part_list_outline: PartListOutline = run_result.final_output_as(PartListOutline)

        if not part_list_outline.parts:
            print(f"⚠️ Part generation failed: Agent returned an empty 'parts' list despite schema. Retrying or manual intervention may be needed.")
            return False

        if len(part_list_outline.parts) < 3:
            print(f"⚠️ Part generation failed: Agent generated only {len(part_list_outline.parts)} parts, expected at least 3 as per schema. Review agent instructions or model.")
            pass # Continue, but log as warning

        print(f"🔍 Generated {len(part_list_outline.parts)} parts:")
        for i, part_data in enumerate(part_list_outline.parts[:3]):
            print(f"  Part {part_data.part_number}: {part_data.title}")
            print(f"  Summary: {part_data.summary[:100]}...")
            if i == 2 and len(part_list_outline.parts) > 3:
                print(f"  ... and {len(part_list_outline.parts)-3} more parts")

        project.structured_outline = part_list_outline.model_dump()
        project.status = "PARTS_PENDING_VALIDATION"
        await session.commit()
        print(f"✅ Part structure generated for project {project_id}. Status: {project.status}")

        if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
            await log_crew_run(
                session=session,
                project_id=project.id,
                initiating_task_name="Phase 1: Part Generation",
                usage_metrics=run_result
            )
        else:
            print(f"⚠️ No usage metrics available in raw_responses for Part Generation run for project {project_id}.")

        return True

    except Exception as e:
        project_status_message = ""
        if project:
            project.status = "PART_GENERATION_FAILED"
            try:
                await session.commit()
                project_status_message = f" for project {project.id}. Status set to {project.status}."
            except Exception as commit_e:
                print(f"❌ Failed to commit status update for project {project.id}: {commit_e}")
                project_status_message = f" for project {project.id} (status update failed)."

        print(f"🔥 Critical error during Part generation{project_status_message}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_chapter_detailing_crew(session: AsyncSession, part_id: uuid.UUID) -> bool:
    print(f"🚀 Starting chapter detailing for part: {part_id}")
    part = None
    try:
        part = await get_part_by_id(session, part_id=part_id)
        if not part:
            print(f"❌ Chapter detailing failed: Part {part_id} not found.")
            return False
        
        if not part.title or not part.summary:
            print(f"❌ Chapter detailing failed: Part {part_id} is missing title or summary. Cannot detail chapters.")
            return False

        agent_input = (
            f"Generate a detailed chapter outline for a book part. "
            f"The part title is '{part.title}' and its summary is '{part.summary}'.\n\n"
            "Provide a list of chapters, each chapter must have:\n"
            "- chapter_number: Positive integer, sequential.\n"
            "- title: A descriptive chapter title.\n"
            "- brief: A structured brief containing:\n"
            "  - thesis_statement: The central argument (string).\n"
            "  - narrative_arc: The chapter's structure (string).\n"
            "  - required_inclusions: List of key concepts to include (list of strings).\n"
            "  - key_questions_to_answer: List of questions the chapter must answer (list of strings).\n"
            "- suggested_agent: The name of the specialist AI agent best suited to write this chapter (e.g., 'Historian AI', 'Technologist AI', 'Philosopher AI', 'Theorist AI'). "
            "Choose from: 'Historian AI', 'Technologist AI', 'Philosopher AI', 'Theorist AI'."
            "\n\nOutput ONLY JSON matching the ChapterListOutline schema. Ensure at least 3 chapters are generated."
        )

        print(f"🤖 Architect AI preparing chapter outline for part {part.part_number} - '{part.title}'...")

        try: # NEW: Circuit Breaker try block
            run_result: RunResult = await _execute_agent_run(architect_chapter_agent, agent_input)
        except CircuitBreakerError:
            print(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Chapter detailing for part {part_id}.")
            if part:
                part.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            print(f"❌ Error during agent execution for Chapter detailing: {str(e)}")
            raise
        
        chapter_list_outline: ChapterListOutline = run_result.final_output_as(ChapterListOutline)

        if not chapter_list_outline.chapters:
            print(f"⚠️ Chapter detailing failed: Agent returned an empty 'chapters' list.")
            return False
        
        if len(chapter_list_outline.chapters) < 3:
             print(f"⚠️ Chapter detailing warning: Agent generated only {len(chapter_list_outline.chapters)} chapters for part {part.id}. Consider reviewing agent output or instructions.")

        project = part.project

        if project.structured_outline is None:
            project.structured_outline = {}
        
        project.structured_outline[str(part.id)] = chapter_list_outline.model_dump()
        
        part.status = "CHAPTERS_PENDING_VALIDATION"
        
        session.add(project)
        session.add(part)
        await session.commit()
        
        print(f"✅ Chapter structure generated for part {part.id}. Status: {part.status}")

        if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
            await log_crew_run(
                session=session,
                project_id=project.id,
                initiating_task_name=f"Phase 2: Chapter Detailing for Part {part.part_number}",
                usage_metrics=run_result
            )
        else:
            print(f"⚠️ No usage metrics available in raw_responses for Chapter Detailing run for part {part_id}.")
        
        return True

    except Exception as e:
        part_status_message = ""
        if part:
            part.status = "CHAPTER_DETAILING_FAILED"
            try:
                await session.commit()
                part_status_message = f" for part {part.id}. Status set to {part.status}."
            except Exception as commit_e:
                print(f"❌ Failed to commit status update for part {part.id}: {commit_e}")
                part_status_message = f" for part {part.id} (status update failed)."
        
        print(f"🔥 Critical error during Chapter detailing{part_status_message}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_chapter_generation_crew(session: AsyncSession, chapter_id: uuid.UUID) -> bool:
    print(f"🚀 Starting content generation for chapter: {chapter_id}")
    chapter = None
    project_id = None
    try:
        chapter = await get_chapter_by_id(session, chapter_id=chapter_id)
        if not chapter or not chapter.part or not chapter.part.project:
            print(f"❌ Chapter content generation failed: Chapter {chapter_id} not found or is missing relationships.")
            return False

        project_id = chapter.part.project.id
        
        agent_instance = AGENT_INSTANCES.get(chapter.suggested_agent)
        if not agent_instance:
            print(f"❌ Chapter content generation failed: Agent instance not found for '{chapter.suggested_agent}'.")
            chapter.status = "AGENT_NOT_FOUND"
            await session.commit()
            return False

        if not chapter.title or not chapter.brief:
            print(f"❌ Chapter content generation failed: Chapter {chapter_id} is missing title or brief.")
            chapter.status = "BRIEF_MISSING"
            await session.commit()
            return False

        brief_data = chapter.brief
        agent_input = (
            f"Chapter Title: {chapter.title}\n\n"
            f"Brief:\n"
            f"- Thesis Statement: {brief_data.get('thesis_statement', 'N/A')}\n"
            f"- Narrative Arc: {brief_data.get('narrative_arc', 'N/A')}\n"
            f"- Required Inclusions: {', '.join(brief_data.get('required_inclusions', ['N/A']))}\n"
            f"- Key Questions to Answer: {', '.join(brief_data.get('key_questions_to_answer', ['N/A']))}\n\n"
            "Write the full content of this chapter. Ensure it adheres to the brief."
        )
        
        print(f"✍️ {chapter.suggested_agent} generating content for chapter {chapter.chapter_number} - '{chapter.title}'...")

        try:
            run_result: RunResult = await _execute_agent_run(agent_instance, agent_input)
        except CircuitBreakerError:
            print(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Chapter content generation for chapter {chapter_id}.")
            if chapter:
                chapter.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            print(f"❌ Error during agent execution for Chapter content generation: {str(e)}")
            raise
        
        content_output: StringOutput = run_result.final_output_as(StringOutput)
        content = content_output.text if content_output else None

        # Extract token count from run_result.usage
        # This logic needs to be consistent with how log_crew_run extracts it
        generated_token_count = 0
        if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
            response_usage = getattr(run_result.raw_responses[0], 'usage', None)
            if response_usage and hasattr(response_usage, 'total_tokens'): # Or sum input_tokens + output_tokens
                generated_token_count = response_usage.total_tokens
            elif response_usage and hasattr(response_usage, 'input_tokens') and hasattr(response_usage, 'output_tokens'):
                generated_token_count = response_usage.input_tokens + response_usage.output_tokens
            # Fallback to dict if usage is dict-like
            elif isinstance(response_usage, dict):
                generated_token_count = response_usage.get('total_tokens', 0)
                if generated_token_count == 0:
                    generated_token_count = response_usage.get('input_tokens', 0) + response_usage.get('output_tokens', 0)


        if content:
           # 1. Update content and save version
            await update_chapter_content(session, chapter_id=chapter.id, content=content, token_count=generated_token_count)
            # 2. Set the status
            await update_chapter_status(session, chapter_id=chapter.id, new_status="CONTENT_GENERATED")
            print(f"✅ Content generated successfully for chapter: {chapter_id}. Status set to CONTENT_GENERATED.")
            
            # Log token usage via log_crew_run (this is separate but important)
            if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
                task_name = f"Chapter: Ch {chapter.chapter_number} - {chapter.title[:30]}..."
                await log_crew_run(
                    session=session,
                    project_id=project_id,
                    initiating_task_name=task_name,
                    usage_metrics=run_result
                )
            else:
                print(f"⚠️ No usage metrics available in raw_responses for Chapter Content Generation run for chapter {chapter_id}.")
            return True
        else:
            print(f"❌ Content generation failed for chapter: {chapter_id}. Agent returned no content.")
            await update_chapter_status(session, chapter_id=chapter.id, new_status="CONTENT_GEN_FAILED") # Use helper for consistency
            return False

    except Exception as e:
        chapter_status_message = ""
        if chapter:
            await update_chapter_status(session, chapter_id=chapter.id, new_status="CONTENT_GEN_ERROR") # Use helper
            chapter_status_message = f" for chapter {chapter.id}. Status set to CONTENT_GEN_ERROR."
            try:
                await session.commit()
                chapter_status_message = f" for chapter {chapter.id}. Status set to {chapter.status}."
            except Exception as commit_e:
                print(f"❌ Failed to commit status update for chapter {chapter.id}: {commit_e}")
                chapter_status_message = f" for chapter {chapter.id} (status update failed)."
        
        print(f"🔥 Critical error during Chapter content generation{chapter_status_message}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_transition_analysis_crew(session: AsyncSession, chapter_id: uuid.UUID) -> bool:
    print(f"🚀 Starting transition analysis for chapter: {chapter_id}")
    current_chapter = None
    project_id = None
    try:
        current_chapter = await get_chapter_by_id(session, chapter_id=chapter_id)
        if not current_chapter or not current_chapter.part:
            print(f"❌ Transition analysis failed: Could not load chapter {chapter_id} or its part.")
            return False

        project_id = current_chapter.part.project_id

        part_chapters_stmt = select(Chapter).where(
            Chapter.part_id == current_chapter.part_id
        ).order_by(Chapter.chapter_number)
        
        result = await session.execute(part_chapters_stmt)
        chapters_in_part = result.scalars().all()
        
        try:
            current_index = [c.id for c in chapters_in_part].index(current_chapter.id)
        except ValueError:
            print(f"❌ Transition analysis failed: Could not find chapter {chapter_id} in its part's list.")
            return False

        if current_index == 0:
            print(f"ℹ️ Chapter {chapter_id} is the first in its part. No transition analysis needed.")
            current_chapter.transition_feedback = "First chapter - no transition needed."
            current_chapter.status = "TRANSITION_DONE"
            await session.commit()
            return True

        preceding_chapter = chapters_in_part[current_index - 1]

        if not current_chapter.content:
            error_msg = f"❌ Transition analysis failed: Current chapter {current_chapter.id} content is missing."
            print(error_msg)
            current_chapter.status = "CONTENT_MISSING_FOR_TRANSITION"
            await session.commit()
            raise ValueError(error_msg)
        
        if not preceding_chapter.content:
            error_msg = f"❌ Transition analysis failed: Preceding chapter {preceding_chapter.id} content is missing."
            print(error_msg)
            current_chapter.status = "CONTENT_MISSING_FOR_TRANSITION"
            await session.commit()
            raise ValueError(error_msg)

        agent_instance = continuity_editor_agent

        agent_input = (
            f"Analyze the transition between two chapters and provide actionable feedback to improve narrative flow.\n\n"
            f"Previous Chapter Ending (last 500 chars):\n{preceding_chapter.content[-500:]}\n\n"
            f"Current Chapter Beginning (first 500 chars):\n{current_chapter.content[:500]}"
        )
        
        print(f"✂️ Continuity Editor AI analyzing transition for chapter {current_chapter.chapter_number}...")

        try: # NEW: Circuit Breaker try block
            run_result: RunResult = await _execute_agent_run(agent_instance, agent_input)
        except CircuitBreakerError:
            print(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Transition analysis for chapter {chapter_id}.")
            if current_chapter:
                current_chapter.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            print(f"❌ Error during agent execution for Transition analysis: {str(e)}")
            raise
        
        feedback_output: StringOutput = run_result.final_output_as(StringOutput)
        feedback = feedback_output.text if feedback_output else None

        if feedback:
            current_chapter.transition_feedback = feedback
            current_chapter.status = "TRANSITION_ANALYZED"
            await session.commit()
            print(f"✅ Transition analysis complete for chapter: {chapter_id}. Feedback saved.")
            
            if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
                task_name = f"Transition: Ch {current_chapter.chapter_number}"
                await log_crew_run(
                    session=session,
                    project_id=project_id,
                    initiating_task_name=task_name,
                    usage_metrics=run_result
                )
            else:
                print(f"⚠️ No usage metrics available in raw_responses for Transition Analysis run for chapter {chapter_id}.")
            return True
        else:
            print(f"❌ Transition analysis failed for chapter: {chapter_id}. Agent returned no feedback.")
            current_chapter.status = "TRANSITION_ANALYSIS_FAILED"
            await session.commit()
            return False

    except Exception as e:
        chapter_status_message = ""
        if current_chapter:
            current_chapter.status = "TRANSITION_ANALYSIS_ERROR"
            try:
                await session.commit()
                chapter_status_message = f" for chapter {current_chapter.id}. Status set to {current_chapter.status}."
            except Exception as commit_e:
                print(f"❌ Failed to commit status update for chapter {current_chapter.id}: {commit_e}")
                chapter_status_message = f" for chapter {current_chapter.id} (status update failed)."
        
        print(f"🔥 Critical error during Transition analysis{chapter_status_message}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def run_finalization_crew(session: AsyncSession, project_id: uuid.UUID, task_type: str) -> bool:
    print(f"🚀 Starting Finalization Task ({task_type}) for project: {project_id}")
    project = None
    try:
        project = await get_project_with_details(session, project_id=project_id)
        if not project:
            print(f"❌ Finalization failed: Project {project_id} not found.")
            return False

        full_book_content = ""
        has_content = False
        for part in sorted(project.parts, key=lambda p: p.part_number):
            full_book_content += f"\n\n--- PART {part.part_number}: {part.title} ---\n"
            full_book_content += f"Summary: {part.summary}\n"
            for chapter in sorted(part.chapters, key=lambda c: c.chapter_number):
                if chapter.content:
                    full_book_content += f"\n### CHAPTER {chapter.chapter_number}: {chapter.title} ###\n"
                    full_book_content += chapter.content
                    has_content = True

        if not has_content:
            print(f"❌ Finalization failed: No content found for project {project_id} to generate {task_type}.")
            project.status = "NO_CONTENT_FOR_FINALIZATION"
            await session.commit()
            return False

        agent_instance = theorist_agent

        agent_input = (
            f"You are writing the {task_type} for a book.\n"
            f"The full content of the book is provided below. Synthesize it into a compelling {task_type}.\n\n"
            f"Book Content:\n{full_book_content}"
        )
        
        print(f"🎓 Theorist AI generating {task_type} for project {project_id}...")

        try: # NEW: Circuit Breaker try block
            run_result: RunResult = await _execute_agent_run(agent_instance, agent_input)
        except CircuitBreakerError:
            print(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Finalization ({task_type}) for project {project_id}.")
            if project:
                project.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            print(f"❌ Error during agent execution for Finalization: {str(e)}")
            raise
        
        result_text_output: StringOutput = run_result.final_output_as(StringOutput)
        result_text = result_text_output.text if result_text_output else None

        if result_text:
            if task_type.lower() == 'introduction':
                part_number = 0
                chapter_number = 1
                title = "Introduction"
            elif task_type.lower() == 'conclusion':
                part_number = max((p.part_number for p in project.parts), default=0) + 1
                chapter_number = 1
                title = "Conclusion"
            else:
                print(f"❌ Finalization failed: Invalid task_type '{task_type}'. Must be 'introduction' or 'conclusion'.")
                return False

            final_part = next((p for p in project.parts if p.part_number == part_number), None)
            if not final_part:
                final_part = Part(
                    project_id=project.id,
                    part_number=part_number,
                    title=f"The Book's {title}",
                    summary=f"This part contains the book's {task_type}."
                )
                session.add(final_part)
                await session.flush()

            new_chapter = Chapter(
                part_id=final_part.id,
                chapter_number=chapter_number,
                title=title,
                content=result_text,
                status="COMPLETE",
                suggested_agent="Theorist AI"
            )
            session.add(new_chapter)
            project.status = "COMPLETE"
            await session.commit()
            print(f"✅ {task_type} created successfully for project {project_id}. Project status: {project.status}.")

            if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
                await log_crew_run(
                    session=session,
                    project_id=project.id,
                    initiating_task_name=f"Phase 5: {task_type} Generation",
                    usage_metrics=run_result
                )
            else:
                print(f"⚠️ No usage metrics available in raw_responses for {task_type} Generation run for project {project_id}.")
            return True
        else:
            print(f"❌ {task_type} generation failed for project: {project_id}. Agent returned no content.")
            project.status = f"{task_type.upper()}_GEN_FAILED"
            await session.commit()
            return False

    except Exception as e:
        project_status_message = ""
        if project:
            project.status = f"{task_type.upper()}_GEN_ERROR"
            try:
                await session.commit()
                project_status_message = f" for project {project.id}. Status set to {project.status}."
            except Exception as commit_e:
                print(f"❌ Failed to commit status update for project {project.id}: {commit_e}")
                project_status_message = f" for project {project.id} (status update failed)."
        
        print(f"🔥 Critical error during {task_type} generation{project_status_message}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False