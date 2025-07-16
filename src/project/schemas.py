# src/project/schemas.py
import uuid
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from src.crew.schemas import ChapterBrief
from pydantic import field_validator

# --- Main Application Schemas ---

class ProjectCreate(BaseModel):
    """The schema for creating a project from a raw text blueprint."""
    # UPDATED: Renamed to match the new database model.
    raw_blueprint: str

# --- Read Schemas (for API responses) ---

class ProjectRead(BaseModel):
    """Base read schema for a project."""
    id: uuid.UUID
    
    # UPDATED: Renamed to match the model.
    raw_blueprint: str
    
    # NEW: To show the project's current phase.
    status: str
    
    # NEW: To show the evolving structured data.
    structured_outline: Dict[str, Any] | None = None
    
    total_cost: Decimal

    @field_validator('structured_outline')
    def validate_outline(cls, value):
        if value is not None and not isinstance(value, dict):
            raise ValueError("structured_outline must be a dictionary")
        return value

    class Config:
        from_attributes = True

class PartRead(BaseModel):
    """Read schema for a single Part."""
    id: uuid.UUID
    part_number: int
    title: str
    summary: str | None = None

    class Config:
        from_attributes = True

class ChapterRead(BaseModel):
    """Read schema for a single Chapter, using the 'brief' field."""
    id: uuid.UUID
    chapter_number: int
    title: str
    brief: ChapterBrief | None = None
    status: str
    suggested_agent: str | None = None
    part: PartRead

    class Config:
        from_attributes = True

class PartReadWithChapters(PartRead):
    """Read schema for a Part that includes its nested Chapters."""
    chapters: list[ChapterRead] = []

class ProjectDetailRead(ProjectRead):
    """Read schema for a full Project, including all its Parts and Chapters."""
    parts: list[PartReadWithChapters] = []