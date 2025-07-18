# src/crew/service.py
import asyncio
import uuid
from typing import Any, Dict
from decimal import Decimal
import logging # NEW: Import logging module

# NEW IMPORT: Circuit Breaker
from circuitbreaker import CircuitBreaker, CircuitBreakerError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from sqlalchemy.orm import selectinload

# NEW IMPORTS for openai-agents
from agents import Runner, RunResult # Make sure 'agents' is correctly importable

# Make sure these are the new Agent instances you defined in agents.py
from .agents import (
    AGENT_INSTANCES,
    architect_part_agent,
    architect_chapter_agent,
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
    update_chapter_status
)
from .schemas import PartListOutline, ChapterListOutline
from .models import CrewRunLog
from .pricing import calculate_cost

# NEW: Get a logger instance for this module
logger = logging.getLogger(__name__)

# NEW: Configure a circuit breaker for OpenAI API calls
# This will wrap calls to Runner.run
# - failure_threshold: After 3 consecutive failures, the circuit opens.
# - recovery_timeout: The circuit stays open for 60 seconds before attempting a half-open state.
# - expected_exception: The types of exceptions that should trigger a failure.
openai_circuit_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60, # seconds
    expected_exception=(
        ConnectionError, # Network issues
        asyncio.TimeoutError, # If requests time out
        # Consider adding specific exceptions from your 'agents' library if it exposes them for API errors
    )
)

# NEW: Helper function to execute an agent run, wrapped by the circuit breaker
@openai_circuit_breaker
async def _execute_agent_run(agent_instance: Any, agent_input: str) -> RunResult:
    """Helper function to execute an agent run, wrapped by the circuit breaker."""
    logger.debug(f"Attempting agent run for '{agent_instance.name}' with input: {agent_input[:200]}...")
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
        logger.warning(f"Could not log run for '{initiating_task_name}': Invalid RunResult or no raw_responses found.")
        return

    # Extract the specific response (assuming the first one for simplicity for now)
    # The 'usage' object structure can vary slightly by LLM provider/library.
    # Ensure you are correctly extracting 'input_tokens' and 'output_tokens'.
    response_usage = getattr(usage_metrics.raw_responses[0], 'usage', None)

    if not response_usage:
        logger.warning(f"Could not log run for '{initiating_task_name}': No usage data found in raw_response.")
        return

    prompt_tokens = 0
    completion_tokens = 0
    model_name_for_logging = settings.DEFAULT_OPENAI_MODEL_NAME # Default to general setting

    # Attempt to extract tokens and model name from the usage object
    if hasattr(response_usage, 'input_tokens'):
        prompt_tokens = response_usage.input_tokens
    if hasattr(response_usage, 'output_tokens'):
        completion_tokens = response_usage.output_tokens
    if hasattr(response_usage, 'model_name'): # Check if the usage object itself has model_name
        model_name_for_logging = response_usage.model_name
    elif hasattr(usage_metrics.raw_responses[0], 'model'): # Or if raw_response has model
        model_name_for_logging = usage_metrics.raw_responses[0].model
    # Fallback if keys are different (less likely with consistent openai-agents usage)
    elif isinstance(response_usage, dict):
        prompt_tokens = response_usage.get('input_tokens', 0)
        completion_tokens = response_usage.get('output_tokens', 0)
        if prompt_tokens == 0 and completion_tokens == 0:
             prompt_tokens = response_usage.get('prompt_tokens', 0)
             completion_tokens = response_usage.get('completion_tokens', 0)
        model_name_for_logging = response_usage.get('model', model_name_for_logging) # Get model from dict

    total_tokens = prompt_tokens + completion_tokens

    run_cost = calculate_cost(
        model_name=model_name_for_logging, # Use the actual model name for cost
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    new_log = CrewRunLog(
        project_id=project_id, initiating_task_name=initiating_task_name,
        model_name=model_name_for_logging, prompt_tokens=prompt_tokens, # Log the actual model name
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
    logger.info(f"📊 Run Logged: '{initiating_task_name}' ({model_name_for_logging}) - Tokens: {total_tokens}, Cost: ${run_cost:.6f}")

async def run_part_generation_crew(session: AsyncSession, project_id: uuid.UUID) -> bool:
    logger.info(f"🚀 Starting Part generation for project: {project_id}")
    project = None
    try:
        project = await get_project_by_id(session, project_id=project_id)
        if not project:
            logger.error(f"❌ Part generation failed: Project {project_id} not found.")
            return False
        if not project.raw_blueprint:
            logger.error(f"❌ Part generation failed: Project {project_id} has no raw blueprint defined.")
            return False

        agent_input = project.raw_blueprint

        logger.info(f"🤖 Architect AI preparing part outline for project {project_id}...")

        try:
            run_result: RunResult = await _execute_agent_run(architect_part_agent, agent_input)
        except CircuitBreakerError:
            logger.error(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Part generation for project {project_id}.")
            if project:
                project.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            logger.exception(f"❌ Error during agent execution for Part generation for project {project_id}: {e}")
            if project:
                project.status = "PART_GENERATION_FAILED"
                await session.commit()
            raise

        part_list_outline: PartListOutline = run_result.final_output_as(PartListOutline)

        if not part_list_outline.parts:
            logger.warning(f"⚠️ Part generation failed: Agent returned an empty 'parts' list despite schema. Retrying or manual intervention may be needed for project {project_id}.")
            return False

        if len(part_list_outline.parts) < 3:
            logger.warning(f"⚠️ Part generation warning for project {project_id}: Agent generated only {len(part_list_outline.parts)} parts, expected at least 3 as per schema. Review agent instructions or model.")
            pass

        logger.info(f"🔍 Generated {len(part_list_outline.parts)} parts for project {project_id}:")
        for i, part_data in enumerate(part_list_outline.parts[:3]):
            logger.info(f"  Part {part_data.part_number}: {part_data.title} - Summary: {part_data.summary[:100]}...")
            if i == 2 and len(part_list_outline.parts) > 3:
                logger.info(f"  ... and {len(part_list_outline.parts)-3} more parts")

        # --- UPDATED STRATEGIC LOGIC FOR DRAFT OUTLINES ---
        project.draft_parts_outline = part_list_outline.model_dump()
        logger.debug(f"Updated project {project.id} draft_parts_outline.")
        
        # Clear draft_chapters_outline as we are starting a new parts generation cycle
        project.draft_chapters_outline = None
        logger.debug(f"Cleared draft_chapters_outline for project {project.id} during part generation.")
        # --- END UPDATED STRATEGIC LOGIC ---

        project.status = "PARTS_PENDING_VALIDATION"
        session.add(project) # Mark project as dirty
        await session.commit()
        logger.info(f"✅ Part structure generated for project {project_id}. Status: {project.status}")

        if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
            await log_crew_run(
                session=session,
                project_id=project.id,
                initiating_task_name="Phase 1: Part Generation",
                usage_metrics=run_result
            )
        else:
            logger.warning(f"⚠️ No usage metrics available in raw_responses for Part Generation run for project {project_id}.")

        return True

    except Exception as e:
        project_status_message = ""
        if project:
            project.status = "PART_GENERATION_FAILED"
            try:
                await session.commit()
                project_status_message = f" for project {project.id}. Status set to {project.status}."
            except Exception as commit_e:
                logger.error(f"❌ Failed to commit status update for project {project.id}: {commit_e}")
                project_status_message = f" for project {project.id} (status update failed)."

        logger.critical(f"🔥 Critical error during Part generation{project_status_message}: {e}", exc_info=True)
        return False




async def run_chapter_detailing_crew(session: AsyncSession, part_id: uuid.UUID) -> bool:
    logger.info(f"🚀 Starting chapter detailing for part: {part_id}")
    part = None
    try:
        part = await get_part_by_id(session, part_id=part_id)
        if not part:
            logger.error(f"❌ Chapter detailing failed: Part {part_id} not found.")
            return False
        
        if not part.title or not part.summary:
            logger.error(f"❌ Chapter detailing failed: Part {part_id} is missing title or summary. Cannot detail chapters.")
            return False

        project = part.project
        if not project:
            logger.error(f"❌ Chapter detailing failed: Project for part {part_id} not found.")
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
            "  - key_questions_to_answer: List of specific questions the chapter must answer (list of strings).\n"
            "- suggested_agent: The name of the specialist AI agent best suited to write this chapter (e.g., 'Historian AI', 'Technologist AI', 'Philosopher AI', 'Theorist AI'). "
            "Choose from: 'Historian AI', 'Technologist AI', 'Philosopher AI', 'Theorist AI'."
            "\n\nOutput ONLY JSON matching the ChapterListOutline schema. Ensure at least 3 chapters are generated."
        )

        logger.info(f"🤖 Architect AI preparing chapter outline for part {part.part_number} - '{part.title}'...")

        try:
            run_result: RunResult = await _execute_agent_run(architect_chapter_agent, agent_input)
        except CircuitBreakerError:
            logger.error(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Chapter detailing for part {part_id}.")
            if part:
                part.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            logger.exception(f"❌ Error during agent execution for Chapter detailing for part {part_id}: {e}")
            if part:
                part.status = "CHAPTER_DETAILING_FAILED"
                await session.commit()
            raise
        
        chapter_list_outline: ChapterListOutline = run_result.final_output_as(ChapterListOutline)

        if not chapter_list_outline.chapters:
            logger.warning(f"⚠️ Chapter detailing failed: Agent returned an empty 'chapters' list for part {part_id}.")
            return False
        
        if len(chapter_list_outline.chapters) < 3:
             logger.warning(f"⚠️ Chapter detailing warning for part {part.id}: Agent generated only {len(chapter_list_outline.chapters)} chapters. Consider reviewing agent output or instructions.")


        # --- CRITICAL FIX FOR ACCUMULATING DRAFT CHAPTERS OUTLINE ---
        # Get the current draft_chapters_outline. If null, initialize to an empty dict.
        # IMPORTANT: Make a SHALLOW COPY if project.draft_chapters_outline is already an object.
        # This forces SQLAlchemy to recognize a new object assignment.
        current_draft_chapters_map = project.draft_chapters_outline.copy() if project.draft_chapters_outline is not None else {}
        
        # Store ChapterListOutline under the part's UUID in the map
        current_draft_chapters_map[str(part.id)] = chapter_list_outline.model_dump()
        logger.debug(f"Added/updated draft chapters for part {part.id} in map.")
        
        # Assign the updated map back to the project's draft_chapters_outline
        project.draft_chapters_outline = current_draft_chapters_map
        logger.debug(f"Assigned updated draft_chapters_outline to project {project.id}.")
        
        # Clear draft_parts_outline as this is a new chapter detailing cycle
        project.draft_parts_outline = None
        logger.debug(f"Cleared draft_parts_outline for project {project.id} during chapter detailing.")
        # --- END CRITICAL FIX ---

        part.status = "CHAPTERS_PENDING_VALIDATION"
        
        session.add(project) # Mark project as dirty (draft_chapters_outline changed)
        session.add(part) # Mark part as dirty (status changed)
        await session.commit()
        
        logger.info(f"✅ Chapter structure generated for part {part.id}. Status: {part.status}")

        if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
            await log_crew_run(
                session=session,
                project_id=project.id,
                initiating_task_name=f"Phase 2: Chapter Detailing for Part {part.part_number}",
                usage_metrics=run_result
            )
        else:
            logger.warning(f"⚠️ No usage metrics available in raw_responses for Chapter Detailing run for part {part_id}.")
        
        return True

    except Exception as e:
        part_status_message = ""
        if part:
            part.status = "CHAPTER_DETAILING_FAILED"
            try:
                await session.commit()
                part_status_message = f" for part {part.id}. Status set to {part.status}."
            except Exception as commit_e:
                logger.error(f"❌ Failed to commit status update for part {part.id}: {commit_e}")
                part_status_message = f" for part {part.id} (status update failed)."
        
        logger.critical(f"🔥 Critical error during Chapter detailing{part_status_message}: {e}", exc_info=True)
        return False
    
async def run_chapter_generation_crew(session: AsyncSession, chapter_id: uuid.UUID) -> bool:
    logger.info(f"🚀 Starting content generation for chapter: {chapter_id}")
    chapter = None
    project_id = None
    try:
        # Load chapter with part and project relationships
        chapter = await get_chapter_by_id(session, chapter_id=chapter_id)
        if not chapter or not chapter.part or not chapter.part.project:
            logger.error(f"❌ Chapter content generation failed: Chapter {chapter_id} not found or is missing relationships.")
            return False

        project_id = chapter.part.project.id
        
        agent_instance = AGENT_INSTANCES.get(chapter.suggested_agent)
        if not agent_instance:
            logger.error(f"❌ Chapter content generation failed: Agent instance not found for '{chapter.suggested_agent}'.")
            chapter.status = "AGENT_NOT_FOUND" # Set status
            await session.commit()
            return False

        if not chapter.title or not chapter.brief:
            logger.error(f"❌ Chapter content generation failed: Chapter {chapter_id} is missing title or brief.")
            chapter.status = "BRIEF_MISSING" # Set status
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
        
        logger.info(f"✍️ {chapter.suggested_agent} generating content for chapter {chapter.chapter_number} - '{chapter.title}'...")

        try:
            run_result: RunResult = await _execute_agent_run(agent_instance, agent_input)
        except CircuitBreakerError:
            logger.error(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Chapter content generation for chapter {chapter_id}.")
            if chapter:
                chapter.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            logger.exception(f"❌ Error during agent execution for Chapter content generation for chapter {chapter_id}: {e}")
            raise
        
        content_output: StringOutput = run_result.final_output_as(StringOutput)
        content = content_output.text if content_output else None

        # Extract token count from run_result.usage
        generated_token_count = 0
        # More robust extraction logic
        response_usage = getattr(run_result, 'raw_responses', [None])[0] # Get the first raw response
        if response_usage and hasattr(response_usage, 'usage'):
            usage_data = getattr(response_usage, 'usage')
            if hasattr(usage_data, 'total_tokens'):
                generated_token_count = usage_data.total_tokens
            elif hasattr(usage_data, 'input_tokens') and hasattr(usage_data, 'output_tokens'):
                generated_token_count = usage_data.input_tokens + usage_data.output_tokens
            # Fallback to dict if usage is dict-like
            elif isinstance(usage_data, dict):
                generated_token_count = usage_data.get('total_tokens', 0)
                if generated_token_count == 0:
                    generated_token_count = usage_data.get('input_tokens', 0) + usage_data.get('output_tokens', 0)


        if content:
           # 1. Update content and save version
            await update_chapter_content(session=session, chapter_id=chapter.id, content=content, token_count=generated_token_count)
            # 2. Set the status
            await update_chapter_status(session=session, chapter_id=chapter.id, new_status="CONTENT_GENERATED")
            logger.info(f"✅ Content generated successfully for chapter: {chapter_id}. Status set to CONTENT_GENERATED.")
            
            # Log token usage via log_crew_run
            if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
                task_name = f"Chapter: Ch {chapter.chapter_number} - {chapter.title[:30]}..."
                await log_crew_run(
                    session=session,
                    project_id=project_id,
                    initiating_task_name=task_name,
                    usage_metrics=run_result
                )
            else:
                logger.warning(f"⚠️ No usage metrics available in raw_responses for Chapter Content Generation run for chapter {chapter_id}.")
            return True
        else:
            logger.error(f"❌ Content generation failed for chapter: {chapter_id}. Agent returned no content.")
            await update_chapter_status(session=session, chapter_id=chapter.id, new_status="CONTENT_GEN_FAILED")
            return False

    except Exception as e:
        chapter_status_message = ""
        if chapter:
            # Note: update_chapter_status also commits session implicitly
            await update_chapter_status(session=session, chapter_id=chapter.id, new_status="CONTENT_GEN_ERROR")
            chapter_status_message = f" for chapter {chapter.id}. Status set to CONTENT_GEN_ERROR."
            # The commit for setting status happens inside update_chapter_status,
            # so we don't need another try-except for commit here.
        
        logger.critical(f"🔥 Critical error during Chapter content generation{chapter_status_message}: {e}", exc_info=True)
        return False

async def run_transition_analysis_crew(session: AsyncSession, chapter_id: uuid.UUID) -> bool:
    logger.info(f"🚀 Starting transition analysis for chapter: {chapter_id}")
    current_chapter = None
    project_id = None
    try:
        current_chapter = await get_chapter_by_id(session, chapter_id=chapter_id)
        if not current_chapter or not current_chapter.part:
            logger.error(f"❌ Transition analysis failed: Could not load chapter {chapter_id} or its part.")
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
            logger.error(f"❌ Transition analysis failed: Could not find chapter {chapter_id} in its part's list.")
            return False

        if current_index == 0:
            logger.info(f"ℹ️ Chapter {chapter_id} is the first in its part. No transition analysis needed.")
            current_chapter.transition_feedback = "First chapter - no transition needed."
            current_chapter.status = "TRANSITION_DONE"
            await session.commit()
            return True

        preceding_chapter = chapters_in_part[current_index - 1]

        if not current_chapter.content:
            error_msg = f"❌ Transition analysis failed: Current chapter {current_chapter.id} content is missing."
            logger.error(error_msg)
            current_chapter.status = "CONTENT_MISSING_FOR_TRANSITION"
            await session.commit()
            raise ValueError(error_msg)
        
        if not preceding_chapter.content:
            error_msg = f"❌ Transition analysis failed: Preceding chapter {preceding_chapter.id} content is missing."
            logger.error(error_msg)
            current_chapter.status = "CONTENT_MISSING_FOR_TRANSITION"
            await session.commit()
            raise ValueError(error_msg)

        agent_instance = continuity_editor_agent

        agent_input = (
            f"Analyze the transition between two chapters and provide actionable feedback to improve narrative flow.\n\n"
            f"Previous Chapter Ending (last 500 chars):\n{preceding_chapter.content[-500:]}\n\n"
            f"Current Chapter Beginning (first 500 chars):\n{current_chapter.content[:500]}"
        )
        
        logger.info(f"✂️ Continuity Editor AI analyzing transition for chapter {current_chapter.chapter_number}...")

        try:
            run_result: RunResult = await _execute_agent_run(agent_instance, agent_input)
        except CircuitBreakerError:
            logger.error(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Transition analysis for chapter {chapter_id}.")
            if current_chapter:
                current_chapter.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            logger.exception(f"❌ Error during agent execution for Transition analysis for chapter {chapter_id}: {e}")
            raise
        
        feedback_output: StringOutput = run_result.final_output_as(StringOutput)
        feedback = feedback_output.text if feedback_output else None

        if feedback:
            current_chapter.transition_feedback = feedback
            current_chapter.status = "TRANSITION_ANALYZED"
            await session.commit()
            logger.info(f"✅ Transition analysis complete for chapter: {chapter_id}. Feedback saved.")
            
            if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
                task_name = f"Transition: Ch {current_chapter.chapter_number}"
                await log_crew_run(
                    session=session,
                    project_id=project_id,
                    initiating_task_name=task_name,
                    usage_metrics=run_result
                )
            else:
                logger.warning(f"⚠️ No usage metrics available in raw_responses for Transition Analysis run for chapter {chapter_id}.")
            return True
        else:
            logger.error(f"❌ Transition analysis failed for chapter: {chapter_id}. Agent returned no feedback.")
            current_chapter.status = "TRANSITION_ANALYSIS_FAILED"
            await session.commit()
            return False

    except Exception as e:
        chapter_status_message = ""
        if current_chapter:
            await update_chapter_status(session=session, chapter_id=current_chapter.id, new_status="TRANSITION_ANALYSIS_ERROR")
            chapter_status_message = f" for chapter {current_chapter.id}. Status set to TRANSITION_ANALYSIS_ERROR."
            # The commit for setting status happens inside update_chapter_status,
            # so we don't need another try-except for commit here.
        
        logger.critical(f"🔥 Critical error during Transition analysis{chapter_status_message}: {e}", exc_info=True)
        return False


async def run_finalization_crew(session: AsyncSession, project_id: uuid.UUID, task_type: str) -> bool:
    logger.info(f"🚀 Starting Finalization Task ({task_type}) for project: {project_id}")
    project = None
    try:
        project = await get_project_with_details(session, project_id=project_id)
        if not project:
            logger.error(f"❌ Finalization failed: Project {project_id} not found.")
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
            logger.error(f"❌ Finalization failed: No content found for project {project_id} to generate {task_type}.")
            project.status = "NO_CONTENT_FOR_FINALIZATION"
            await session.commit()
            return False

        agent_instance = theorist_agent

        agent_input = (
            f"You are writing the {task_type} for a book.\n"
            f"The full content of the book is provided below. Synthesize it into a compelling {task_type}.\n\n"
            f"Book Content:\n{full_book_content}"
        )
        
        logger.info(f"🎓 Theorist AI generating {task_type} for project {project_id}...")

        try:
            run_result: RunResult = await _execute_agent_run(agent_instance, agent_input)
        except CircuitBreakerError:
            logger.error(f"🔴 Circuit breaker is OPEN for OpenAI API. Cannot perform Finalization ({task_type}) for project {project_id}.")
            if project:
                project.status = "API_CIRCUIT_OPEN"
                await session.commit()
            return False
        except Exception as e:
            logger.exception(f"❌ Error during agent execution for Finalization ({task_type}) for project {project_id}: {e}")
            raise
        
        result_text_output: StringOutput = run_result.final_output_as(StringOutput)
        result_text = result_text_output.text if result_text_output else None

        if result_text:
            # Determine part and chapter numbers for introduction/conclusion
            if task_type.lower() == 'introduction':
                part_number = 0 # Convention for introduction part
                chapter_number = 1
                title = "Introduction"
                # Check if an introduction part already exists (part_number 0)
                final_part = next((p for p in project.parts if p.part_number == part_number), None)
            elif task_type.lower() == 'conclusion':
                # Find the maximum existing part number and add 1
                max_part_number = max((p.part_number for p in project.parts), default=0)
                part_number = max_part_number + 1
                chapter_number = 1
                title = "Conclusion"
                # Check if a conclusion part with this number already exists
                final_part = next((p for p in project.parts if p.part_number == part_number), None)
            else:
                logger.error(f"❌ Finalization failed: Invalid task_type '{task_type}'. Must be 'introduction' or 'conclusion'.")
                return False

            if not final_part:
                # Create a new part for introduction/conclusion if it doesn't exist
                final_part = Part(
                    project_id=project.id,
                    part_number=part_number,
                    title=f"The Book's {title}",
                    summary=f"This part contains the book's {task_type}."
                )
                session.add(final_part)
                await session.flush() # Flush to get an ID for the new part immediately

            # Check if a chapter with this title already exists in the (new or existing) final_part
            existing_chapter = next((c for c in final_part.chapters if c.title == title), None)

            if existing_chapter:
                # Update existing chapter
                logger.info(f"Updating existing {task_type} chapter: {existing_chapter.id}")
                new_chapter = existing_chapter # Use the existing chapter object
                new_chapter.content = result_text
                new_chapter.status = "COMPLETE" # Mark as complete
                # No new ChapterVersion is created by direct update, if needed, call update_chapter_content
                # For simplicity, we'll directly update here, assuming update_chapter_content is for user reviews primarily
            else:
                # Create a new chapter
                new_chapter = Chapter(
                    part_id=final_part.id,
                    chapter_number=chapter_number,
                    title=title,
                    content=result_text,
                    status="COMPLETE",
                    suggested_agent="Theorist AI"
                )
                session.add(new_chapter)

            project.status = "COMPLETE" # Project is considered complete after finalization
            await session.commit()
            logger.info(f"✅ {task_type} created/updated successfully for project {project_id}. Project status: {project.status}.")

            if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
                await log_crew_run(
                    session=session,
                    project_id=project.id,
                    initiating_task_name=f"Phase 5: {task_type} Generation",
                    usage_metrics=run_result
                )
            else:
                logger.warning(f"⚠️ No usage metrics available in raw_responses for {task_type} Generation run for project {project_id}.")
            return True
        else:
            logger.error(f"❌ {task_type} generation failed for project: {project_id}. Agent returned no content.")
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
                logger.error(f"❌ Failed to commit status update for project {project.id}: {commit_e}")
                project_status_message = f" for project {project.id} (status update failed)."
        
        logger.critical(f"🔥 Critical error during {task_type} generation{project_status_message}: {e}", exc_info=True)
        return False