# src/project/schemas.py
import uuid
from decimal import Decimal
from pydantic import BaseModel
from typing import List
from src.crew.schemas import ChapterBrief

# --- Blueprint Sub-Models are no longer needed for input ---

# --- Main Application Schemas ---

class ProjectCreate(BaseModel):
    """The schema for creating a project from a simple text blueprint."""
    blueprint: str # The input is now a simple string

# --- Read Schemas (for API responses) ---
# These remain the same as they reflect the structured data AFTER the Architect has run.

class ProjectRead(BaseModel):
    """Base read schema for a project."""
    id: uuid.UUID
    blueprint: str # This will now show the original text blueprint
    total_cost: Decimal

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