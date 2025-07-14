from pydantic import BaseModel, Field
from typing import List

class TaskStatus(BaseModel):
    """A simple schema for returning the status of a queued job."""
    job_id: str
    status: str

# --- Brief and Chapter Schemas (No changes here) ---
class ChapterBrief(BaseModel):
    """A structured writing brief for a specialist agent."""
    thesis_statement: str = Field(..., description="The central thesis or main argument the chapter must defend.")
    narrative_arc: str = Field(..., description="A description of the chapter's narrative structure.")
    required_inclusions: List[str] = Field(..., description="A list of non-negotiable concepts that MUST be included.")
    key_questions_to_answer: List[str] = Field(..., description="The specific questions the chapter must answer.")

class ChapterOutline(BaseModel):
    """Defines the structure for a single chapter."""
    chapter_number: int
    title: str
    brief: ChapterBrief
    suggested_agent: str

# --- NEW: Schemas for the "Divide and Conquer" Workflow ---

class PartOnlyOutline(BaseModel):
    """Defines a part of the book, but WITHOUT chapters. Used for the first step."""
    part_number: int
    title: str
    summary: str

class PartListOutline(BaseModel):
    """A Pydantic model for a list of parts, without chapter details."""
    parts: List[PartOnlyOutline]

class ChapterListOutline(BaseModel):
    """A Pydantic model for a list of chapters for a single part."""
    chapters: List[ChapterOutline]


# --- Original Schemas for Final Assembly ---

class PartOutline(BaseModel):
    """Defines a part of the book, which contains multiple chapters."""
    part_number: int
    title: str
    summary: str
    chapters: List[ChapterOutline]

class BookOutline(BaseModel):
    """The complete, final, and structured outline for the entire book."""
    parts: List[PartOutline]
