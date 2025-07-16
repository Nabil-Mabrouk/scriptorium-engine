# src/crew/tasks.py

from typing import Dict

from src.project.schemas import ChapterRead
from .schemas import PartListOutline, ChapterListOutline
from .agents import AGENT_ROSTER
# src/crew/tasks.py

def prepare_part_generation_inputs(raw_blueprint: str) -> dict:
    """Prepares inputs for the architect chain to generate book parts."""
    return {
        "raw_blueprint": raw_blueprint
    }

def prepare_chapter_detailing_inputs(part_title: str, part_summary: str) -> dict:
    """Prepares inputs for the architect chain to generate chapter details."""
    return {
        "part_title": part_title,
        "part_summary": part_summary
    }

def prepare_chapter_writing_inputs(chapter_data: dict) -> dict:
    """Prepares inputs for specialist chains to write chapter content."""
    brief = chapter_data.get("brief", {})
    return {
        "title": chapter_data.get("title", ""),
        "brief": (
            f"- Chapter Thesis: {brief.get('thesis_statement', '')}\n"
            f"- Narrative Arc: {brief.get('narrative_arc', '')}\n"
            f"- Key Questions: {', '.join(brief.get('key_questions_to_answer', []))}\n"
            f"- Required Inclusions: {', '.join(brief.get('required_inclusions', []))}"
        )
    }

def prepare_transition_analysis_inputs(preceding_end: str, current_start: str) -> dict:
    """Prepares inputs for continuity editor chain to analyze transitions."""
    return {
        "preceding_chapter_end": preceding_end[-500:],  # Last 500 chars
        "current_chapter_start": current_start[:500]    # First 500 chars
    }

def prepare_finalization_inputs(task_type: str, full_book_content: str) -> dict:
    """Prepares inputs for theorist chain to write introduction/conclusion."""
    return {
        "task_type": task_type,
        "full_book_content": full_book_content
    }