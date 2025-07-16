from pydantic import BaseModel, Field
from typing import List
from pydantic import BaseModel, Field, field_validator
from typing import List, Union
import json
from pydantic import BaseModel, Field, validator, ValidationError
from typing import List, Union

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
    part_number: int = Field(..., description="Numerical order of the part")
    title: str = Field(..., description="Title of the part")
    summary: str = Field(..., description="Brief summary of the part's content")

    @validator('part_number')
    def part_number_positive(cls, v):
        if v < 1:
            raise ValueError('Part number must be positive integer')
        return v

class PartListOutline(BaseModel):
    parts: List[PartOnlyOutline] = Field(..., description="List of book parts")
    
    @validator('parts', pre=True)
    def ensure_list(cls, v):
        """Handle different output formats for Pydantic V1"""
        if isinstance(v, dict):
            # Convert dict to list of parts
            if 'parts' in v:
                return v['parts']
            # Handle parts as dictionary values
            return list(v.values())
        elif isinstance(v, str):
            # Try to parse JSON string
            try:
                data = json.loads(v)
                if 'parts' in data:
                    return data['parts']
                return data
            except json.JSONDecodeError:
                pass
        return v
    
    @validator('parts')
    def check_min_parts(cls, v):
        """Ensure at least 3 parts are generated"""
        if len(v) < 3:
            raise ValueError('At least 3 parts are required')
        return v

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

# NEW: Schema for the finalization request body
class FinalizationRequest(BaseModel):
    task_type: str = Field(..., description="The type of finalization task to run, e.g., 'introduction' or 'conclusion'.")