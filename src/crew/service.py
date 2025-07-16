# src/crew/service.py
import asyncio
import uuid
from typing import Any, Dict
from decimal import Decimal # Needed for log_crew_run's local calculations

# NEW IMPORT: Circuit Breaker
#from circuitbreaker import CircuitBreaker, CircuitBreakerError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select # Use future select for cleaner syntax
from sqlalchemy import update # Use update for project total_cost update
from sqlalchemy.orm import selectinload # For get_part_by_id, get_chapter_by_id

# NEW IMPORTS for openai-agents
from agents import Runner, RunResult # Make sure 'agents' is correctly importable

# Make sure these are the new Agent instances you defined in agents.py
# If you defined architect_chapter_agent, you'd import it here too.
from .agents import (
    AGENT_INSTANCES,
    architect_part_agent,
    architect_chapter_agent, # NEW IMPORT
    continuity_editor_agent,
    historian_agent,
    technologist_agent,
    philosopher_agent,
    theorist_agent,
    StringOutput
)

from src.core.config import settings
from src.project.models import Project, Part, Chapter
from src.project.service import (
    get_chapter_by_id, get_project_by_id, get_part_by_id,
    get_project_with_details, update_chapter_content
)
# REMOVE: from pydantic import BaseModel, Field, validator, ValidationError
from .schemas import PartListOutline, ChapterListOutline # Ensure all required schemas are here

# REMOVE all imports related to tasks.py, e.g.:
# from .tasks import (
#     prepare_part_generation_inputs,
#     prepare_chapter_detailing_inputs,
#     prepare_chapter_writing_inputs,
#     prepare_finalization_inputs,
#     prepare_transition_analysis_inputs
# )
from .models import CrewRunLog
from .pricing import calculate_cost

async def log_crew_run(
    session: AsyncSession,
    project_id: uuid.UUID,
    initiating_task_name: str,
    # This usage_metrics parameter will now always be the raw RunResult object
    # from the calling function (e.g., `run_result`).
    usage_metrics: Any,
):
    """Logs the metrics of a completed LLM run."""
    # Ensure we have a valid RunResult object and it has raw_responses
    if not usage_metrics or not hasattr(usage_metrics, 'raw_responses') or not usage_metrics.raw_responses:
        print(f"⚠️ Could not log run for '{initiating_task_name}': Invalid RunResult or no raw_responses found.")
        return

    # Extract the specific response (assuming the first one for simplicity for now)
    # and get its usage attribute.
    response_usage = getattr(usage_metrics.raw_responses[0], 'usage', None)

    if not response_usage:
        print(f"⚠️ Could not log run for '{initiating_task_name}': No usage data found in raw_response.")
        return

    prompt_tokens = 0
    completion_tokens = 0

    # Now extract from the 'response_usage' object which is of type 'Usage'
    if hasattr(response_usage, 'input_tokens'):
        prompt_tokens = response_usage.input_tokens
    if hasattr(response_usage, 'output_tokens'):
        completion_tokens = response_usage.output_tokens

    # Fallback for older OpenAI API keys if necessary, but input/output_tokens are common in new APIs
    # (This part might be less necessary if openai-agents consistently uses input/output_tokens)
    elif isinstance(response_usage, dict): # In case it's a dict for some reason
        prompt_tokens = response_usage.get('input_tokens', 0)
        completion_tokens = response_usage.get('output_tokens', 0)
        if prompt_tokens == 0 and completion_tokens == 0:
             prompt_tokens = response_usage.get('prompt_tokens', 0)
             completion_tokens = response_usage.get('completion_tokens', 0)


    total_tokens = prompt_tokens + completion_tokens

    # Corrected: Use settings.DEFAULT_OPENAI_MODEL_NAME for the model used in this cost calculation
    run_cost = calculate_cost(
        model_name=settings.DEFAULT_OPENAI_MODEL_NAME,
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

    # Update project total cost
    await session.execute(
        update(Project)
        .where(Project.id == project_id)
        .values(total_cost=Project.total_cost + run_cost)
    )

    await session.commit()
    print(f"📊 Run Logged: '{initiating_task_name}' - Tokens: {total_tokens}, Cost: ${run_cost:.6f}")

async def run_part_generation_crew(session: AsyncSession, project_id: uuid.UUID) -> bool:
    print(f"🚀 Starting Part generation for project: {project_id}")
    project = None # Initialize project outside try to ensure it's defined for except block if needed
    try:
        project = await get_project_by_id(session, project_id=project_id)
        if not project:
            print(f"❌ Part generation failed: Project {project_id} not found.")
            return False
        if not project.raw_blueprint:
            print(f"❌ Part generation failed: Project {project_id} has no raw blueprint defined.")
            return False

        # Direct input for the agent is the raw blueprint string
        agent_input = project.raw_blueprint

        print(f"🤖 Architect AI preparing part outline for project {project_id}...")

        # Execute the agent, expecting PartListOutline as output
        # `final_output_as` performs the Pydantic validation defined in architect_part_agent's output_type
        run_result: RunResult = await Runner.run(architect_part_agent, agent_input)
        part_list_outline: PartListOutline = run_result.final_output_as(PartListOutline)

        # The schema (PartListOutline) has a validator for `len(parts) < 3`.
        # If the output doesn't meet this, `final_output_as` would already have failed.
        # So, the check here becomes primarily for empty list if final_output_as somehow returns it,
        # or for additional business logic not covered by the schema.
        if not part_list_outline.parts: # Check if the list of parts is empty
            print(f"⚠️ Part generation failed: Agent returned an empty 'parts' list despite schema. Retrying or manual intervention may be needed.")
            return False

        # The schema validator for PartListOutline should ensure at least 3 parts.
        # This check confirms that the validation was respected and provides a clear message.
        if len(part_list_outline.parts) < 3:
            print(f"⚠️ Part generation failed: Agent generated only {len(part_list_outline.parts)} parts, expected at least 3 as per schema. Review agent instructions or model.")
            # Depending on strictness, you might return False here if this is a hard requirement
            # even if the Pydantic model didn't catch it (which it should have).
            # For now, it's a strong warning.
            pass # Continue if you want to proceed with fewer than 3, or return False

        # Print success details
        print(f"🔍 Generated {len(part_list_outline.parts)} parts:")
        for i, part_data in enumerate(part_list_outline.parts[:3]):  # Print first 3 parts
            print(f"  Part {part_data.part_number}: {part_data.title}")
            print(f"  Summary: {part_data.summary[:100]}...")
            if i == 2 and len(part_list_outline.parts) > 3:
                print(f"  ... and {len(part_list_outline.parts)-3} more parts")

        # Convert to dictionary and save to project
        # This now correctly dumps the entire PartListOutline object
        project.structured_outline = part_list_outline.model_dump()
        project.status = "PARTS_PENDING_VALIDATION"
        await session.commit()
        print(f"✅ Part structure generated for project {project_id}. Status: {project.status}")

        # NEW Check for usage data within raw_responses
        if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
            await log_crew_run(
                session=session,
                project_id=project.id,
                initiating_task_name="Phase 1: Part Generation",
                usage_metrics=run_result # Pass the entire RunResult object
            )
        else:
            print(f"⚠️ No usage metrics available in raw_responses for Part Generation run for project {project_id}.")

        return True

    except Exception as e:
        # Catch any exceptions during agent execution or Pydantic parsing
        project_status_message = ""
        if project:
            # Update project status to reflect failure
            project.status = "PART_GENERATION_FAILED"
            try: # Commit is crucial here
                await session.commit()
                project_status_message = f" for project {project.id}. Status set to {project.status}."
            except Exception as commit_e:
                print(f"❌ Failed to commit status update for project {project.id}: {commit_e}")
                project_status_message = f" for project {project.id} (status update failed)."

        print(f"🔥 Critical error during Part generation{project_status_message}: {str(e)}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return False


async def run_chapter_detailing_crew(session: AsyncSession, part_id: uuid.UUID) -> bool:
    print(f"🚀 Starting chapter detailing for part: {part_id}")
    part = None # Initialize part for potential error handling later
    try:
        part = await get_part_by_id(session, part_id=part_id)
        if not part:
            print(f"❌ Chapter detailing failed: Part {part_id} not found.")
            return False
        
        if not part.title or not part.summary:
            print(f"❌ Chapter detailing failed: Part {part_id} is missing title or summary. Cannot detail chapters.")
            return False

        # Prepare a single string input for the agent
        # We'll re-use architect_part_agent, ensure its instructions in agents.py
        # are broad enough, or create a specific architect_chapter_agent.
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

        # Execute the agent, expecting ChapterListOutline as output
        run_result: RunResult = await Runner.run(architect_chapter_agent, agent_input) # <--- CRITICAL CHANGE HERE
        
        # Extract the structured output. If output doesn't conform to schema, error will be caught.
        chapter_list_outline: ChapterListOutline = run_result.final_output_as(ChapterListOutline)

        if not chapter_list_outline.chapters:
            print(f"⚠️ Chapter detailing failed: Agent returned an empty 'chapters' list.")
            return False
        
        # This check is less strict than PartListOutline, but good to have a minimum
        if len(chapter_list_outline.chapters) < 3:
             print(f"⚠️ Chapter detailing warning: Agent generated only {len(chapter_list_outline.chapters)} chapters for part {part.id}. Consider reviewing agent output or instructions.")

        project = part.project # Get the related project from the part

        # Update the project's structured_outline with the new chapter data for this part
        if project.structured_outline is None:
            project.structured_outline = {}
        
        # This needs to update the existing part entry in the structured_outline
        # or add it if it somehow wasn't there (though it should be after part generation)
        project.structured_outline[str(part.id)] = chapter_list_outline.model_dump()
        
        part.status = "CHAPTERS_PENDING_VALIDATION"
        
        session.add(project) # Ensure project is marked for update
        session.add(part)    # Ensure part is marked for update
        await session.commit()
        
        print(f"✅ Chapter structure generated for part {part.id}. Status: {part.status}")

        # NEW Check for usage data within raw_responses
        if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
            await log_crew_run(
                session=session,
                project_id=project.id,
                initiating_task_name="Phase 2: Chapter Detailing for Part {part.part_number}",
                usage_metrics=run_result # Pass the entire RunResult object
            )
        else:
            print(f"⚠️ No usage metrics available for Chapter Detailing run for part {part_id}.")

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
        return False # Indicate failure


async def run_chapter_generation_crew(session: AsyncSession, chapter_id: uuid.UUID) -> bool:
    print(f"🚀 Starting content generation for chapter: {chapter_id}")
    chapter = None # Initialize chapter for error handling
    project_id = None # Initialize project_id for logging in case chapter not found
    try:
        chapter = await get_chapter_by_id(session, chapter_id=chapter_id)
        if not chapter or not chapter.part or not chapter.part.project:
            print(f"❌ Chapter content generation failed: Chapter {chapter_id} not found or is missing relationships.")
            return False

        project_id = chapter.part.project.id # Get project_id for logging
        
        # Retrieve the specific agent instance based on suggested_agent
        agent_instance = AGENT_INSTANCES.get(chapter.suggested_agent)
        if not agent_instance:
            print(f"❌ Chapter content generation failed: Agent instance not found for '{chapter.suggested_agent}'.")
            chapter.status = "AGENT_NOT_FOUND" # Update status to reflect issue
            await session.commit()
            return False

        if not chapter.title or not chapter.brief:
            print(f"❌ Chapter content generation failed: Chapter {chapter_id} is missing title or brief.")
            chapter.status = "BRIEF_MISSING"
            await session.commit()
            return False

        # Prepare a single string input for the agent based on the chapter brief
        # Reconstruct the brief into a readable string for the LLM
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

        # Execute the agent, expecting StringOutput as output
        run_result: RunResult = await Runner.run(agent_instance, agent_input)
        
        # Extract the string content
        content_output: StringOutput = run_result.final_output_as(StringOutput)
        content = content_output.text if content_output else None
        
        if content:
            await update_chapter_content(session, chapter_id=chapter.id, content=content)
            print(f"✅ Content generated successfully for chapter: {chapter_id}")
            
            # Log token usage
            # if run_result.usage:
            #     task_name = f"Chapter: Ch {chapter.chapter_number} - {chapter.title[:30]}..."
            #     await log_crew_run(
            #         session=session,
            #         project_id=project_id,
            #         initiating_task_name=task_name,
            #         usage_metrics=run_result.usage
            #     )
            # else:
            #     print(f"⚠️ No usage metrics available for Chapter Content Generation run for chapter {chapter_id}.")
            # return True
                        # NEW Check for usage data within raw_responses
            if hasattr(run_result, 'raw_responses') and run_result.raw_responses and hasattr(run_result.raw_responses[0], 'usage'):
                task_name = f"Chapter: Ch {chapter.chapter_number} - {chapter.title[:30]}..."
                await log_crew_run(
                    session=session,
                    project_id=project_id,
                    initiating_task_name=task_name,
                    usage_metrics=run_result # Pass the entire RunResult object
                )
            else:
                print(f"⚠️ No usage metrics available for Chapter Content Generation run for chapter {chapter_id}.")

            return True



        else:
            print(f"❌ Content generation failed for chapter: {chapter_id}. Agent returned no content.")
            chapter.status = "CONTENT_GEN_FAILED" # Update status
            await session.commit()
            return False

    except Exception as e:
        chapter_status_message = ""
        if chapter:
            chapter.status = "CONTENT_GEN_ERROR" # General error state
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
    current_chapter = None # Initialize for error handling
    project_id = None # Initialize for logging
    try:
        current_chapter = await get_chapter_by_id(session, chapter_id=chapter_id)
        if not current_chapter or not current_chapter.part:
            print(f"❌ Transition analysis failed: Could not load chapter {chapter_id} or its part.")
            return False

        project_id = current_chapter.part.project_id # Get project_id for logging

        # Get all chapters in the part
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
            current_chapter.status = "TRANSITION_DONE" # Indicate analysis completed/not needed
            await session.commit()
            return True

        preceding_chapter = chapters_in_part[current_index - 1]

        # CRITICAL FIX: Changed from silent return to raising an error
        if not current_chapter.content:
            error_msg = f"❌ Transition analysis failed: Current chapter {current_chapter.id} content is missing."
            print(error_msg)
            current_chapter.status = "CONTENT_MISSING_FOR_TRANSITION"
            await session.commit()
            raise ValueError(error_msg)
        
        if not preceding_chapter.content:
            error_msg = f"❌ Transition analysis failed: Preceding chapter {preceding_chapter.id} content is missing."
            print(error_msg)
            current_chapter.status = "CONTENT_MISSING_FOR_TRANSITION" # Apply to current chapter as it depends on preceding
            await session.commit()
            raise ValueError(error_msg)

        # Get the specific continuity editor agent instance
        agent_instance = continuity_editor_agent

        # Prepare a single string input, focusing on crucial parts of content
        agent_input = (
            f"Analyze the transition between two chapters and provide actionable feedback to improve narrative flow.\n\n"
            f"Previous Chapter Ending (last 500 chars):\n{preceding_chapter.content[-500:]}\n\n"
            f"Current Chapter Beginning (first 500 chars):\n{current_chapter.content[:500]}"
        )
        
        print(f"✂️ Continuity Editor AI analyzing transition for chapter {current_chapter.chapter_number}...")

        # Execute the agent, expecting StringOutput as output
        run_result: RunResult = await Runner.run(agent_instance, agent_input)
        
        # Extract the string content
        feedback_output: StringOutput = run_result.final_output_as(StringOutput)
        feedback = feedback_output.text if feedback_output else None

        if feedback:
            current_chapter.transition_feedback = feedback
            current_chapter.status = "TRANSITION_ANALYZED" # New status
            await session.commit()
            print(f"✅ Transition analysis complete for chapter: {chapter_id}. Feedback saved.")
            
            # Log token usage
            if run_result.usage:
                task_name = f"Transition: Ch {current_chapter.chapter_number}"
                await log_crew_run(
                    session=session,
                    project_id=project_id,
                    initiating_task_name=task_name,
                    usage_metrics=run_result.usage
                )
            else:
                print(f"⚠️ No usage metrics available for Transition Analysis run for chapter {chapter_id}.")
            return True
        else:
            print(f"❌ Transition analysis failed for chapter: {chapter_id}. Agent returned no feedback.")
            current_chapter.status = "TRANSITION_ANALYSIS_FAILED"
            await session.commit()
            return False

    except Exception as e:
        chapter_status_message = ""
        if current_chapter:
            current_chapter.status = "TRANSITION_ANALYSIS_ERROR" # General error state
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
    project = None # Initialize for error handling
    try:
        project = await get_project_with_details(session, project_id=project_id)
        if not project:
            print(f"❌ Finalization failed: Project {project_id} not found.")
            return False

        # Build full book content
        full_book_content = ""
        has_content = False # Flag to check if any chapter content was found
        for part in sorted(project.parts, key=lambda p: p.part_number):
            full_book_content += f"\n\n--- PART {part.part_number}: {part.title} ---\n"
            full_book_content += f"Summary: {part.summary}\n"
            for chapter in sorted(part.chapters, key=lambda c: c.chapter_number):
                if chapter.content:
                    full_book_content += f"\n### CHAPTER {chapter.chapter_number}: {chapter.title} ###\n"
                    full_book_content += chapter.content
                    has_content = True

        if not has_content: # Check the flag
            print(f"❌ Finalization failed: No content found for project {project_id} to generate {task_type}.")
            project.status = "NO_CONTENT_FOR_FINALIZATION"
            await session.commit()
            return False

        # Get the theorist agent instance
        agent_instance = theorist_agent # Direct instance

        # Prepare input for theorist agent
        agent_input = (
            f"You are writing the {task_type} for a book.\n"
            f"The full content of the book is provided below. Synthesize it into a compelling {task_type}.\n\n"
            f"Book Content:\n{full_book_content}"
        )
        
        print(f"🎓 Theorist AI generating {task_type} for project {project_id}...")

        # Execute the agent, expecting StringOutput as output
        run_result: RunResult = await Runner.run(agent_instance, agent_input)
        
        # Extract the string content
        result_text_output: StringOutput = run_result.final_output_as(StringOutput)
        result_text = result_text_output.text if result_text_output else None

        if result_text:
            # Determine part_number and title for the final chapter (Introduction/Conclusion)
            if task_type.lower() == 'introduction':
                part_number = 0 # Conventionally, intro is part 0 or handled as a special chapter
                chapter_number = 1
                title = "Introduction"
            elif task_type.lower() == 'conclusion':
                # Find the maximum part number and add 1 for the conclusion's part
                part_number = max((p.part_number for p in project.parts), default=0) + 1
                chapter_number = 1
                title = "Conclusion"
            else:
                print(f"❌ Finalization failed: Invalid task_type '{task_type}'. Must be 'introduction' or 'conclusion'.")
                return False

            # Find or create a dedicated part for the finalization chapter
            final_part = next((p for p in project.parts if p.part_number == part_number), None)
            if not final_part:
                final_part = Part(
                    project_id=project.id,
                    part_number=part_number,
                    title=f"The Book's {title}", # Make it clear this is an auto-generated part
                    summary=f"This part contains the book's {task_type}."
                )
                session.add(final_part)
                await session.flush() # Flush to get final_part.id

            # Create final chapter
            new_chapter = Chapter(
                part_id=final_part.id,
                chapter_number=chapter_number,
                title=title,
                content=result_text,
                status="COMPLETE",
                suggested_agent="Theorist AI" # The agent that generated it
            )
            session.add(new_chapter)
            project.status = "COMPLETE" # Mark project as fully complete
            await session.commit()
            print(f"✅ {task_type} created successfully for project {project_id}. Project status: {project.status}.")

            # Log token usage
            if run_result.usage:
                await log_crew_run(
                    session=session,
                    project_id=project.id,
                    initiating_task_name=f"Phase 5: {task_type} Generation",
                    usage_metrics=run_result.usage
                )
            else:
                print(f"⚠️ No usage metrics available for {task_type} Generation run for project {project_id}.")
            return True
        else:
            print(f"❌ {task_type} generation failed for project: {project_id}. Agent returned no content.")
            project.status = f"{task_type.upper()}_GEN_FAILED"
            await session.commit()
            return False

    except Exception as e:
        project_status_message = ""
        if project:
            project.status = f"{task_type.upper()}_GEN_ERROR" # General error state
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