from crewai import Task, Agent
from typing import Dict, Any
from src.project.schemas import ProjectRead, ChapterRead
from src.crew.agents import AGENT_ROSTER
from .schemas import BookOutline

# The format_blueprint_as_text helper function is no longer needed and can be removed.

def create_outline_task(agent: Agent) -> Task:
    """
    Creates the primary task for the Architect AI to interpret a raw text idea
    and generate a complete, structured book outline.
    """
    available_agents_str = "\n".join([f"- {name}: {desc}" for name, desc in AGENT_ROSTER.items()])

    description = (
        "You are a master Information Architect. Your task is to take a user's raw, "
        "free-form idea for a book and transform it into a comprehensive, structured outline. "
        "Analyze the user's intent, identify the core themes, and organize the content into logical Parts and Chapters. "
        "For each Chapter, you must create a detailed `brief` that will guide a specialist writer.\n\n"
        "### User's Raw Book Idea:\n"
        "--- START OF IDEA ---\n"
        "{blueprint_text}"
        "\n--- END OF IDEA ---\n\n"
        "**CRITICAL FINAL INSTRUCTION:** Now, based on the user's idea, generate the complete, structured `BookOutline` in the required JSON format. "
        "Your role is to be a brilliant architect; if the user's idea is sparse, elaborate on it to create a full structure. "
        "If it is detailed, ensure your structure faithfully represents their vision."
    )

    expected_output = (
        "A single, valid JSON object that conforms to the `BookOutline` schema. "
        "This object must contain a list of 'parts', and each part must contain a list of 'chapters'. "
        "Each chapter must have a detailed 'brief' object. "
        "For the 'suggested_agent' field, you MUST choose a valid agent from the provided list.\n\n"
        "### Available Agents:\n"
        f"{available_agents_str}"
    )

    return Task(
        description=description,
        expected_output=expected_output,
        agent=agent,
        output_pydantic=BookOutline
    )

# --- Chapter Writing Task (Unchanged) ---
def create_chapter_writing_task(agent: Agent, chapter_data: ChapterRead) -> Task:
    # This function remains the same as before.
    part_info = chapter_data.part
    brief = chapter_data.brief
    formatted_brief = (
        f"- **Chapter Thesis:** {brief['thesis_statement']}\n"
        f"- **Narrative Arc:** {brief['narrative_arc']}\n"
        f"- **Key Questions to Answer:**\n" + "".join([f"  - {q}\n" for q in brief['key_questions_to_answer']]) +
        f"- **Must-Include Concepts/Names:**\n" + "".join([f"  - {i}\n" for i in brief['required_inclusions']])
    )
    description = (
        "You are a specialist writer...\n\n"
        f"## Your Assignment Context:\n- **You are writing for Part {part_info.part_number}: '{part_info.title}'**\n"
        f"- **Part Summary:** {part_info.summary}\n\n"
        "## Your Specific Chapter Task:\n"
        f"- **Write Chapter {chapter_data.chapter_number}: '{chapter_data.title}'**\n"
        f"- **Chapter Brief:**\n{formatted_brief}\n\n"
        "Produce only the raw text of the chapter itself..."
    )
    expected_output = "The full, complete text of the book chapter..."
    return Task(description=description, expected_output=expected_output, agent=agent)
