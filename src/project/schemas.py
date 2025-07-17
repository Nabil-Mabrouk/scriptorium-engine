# src/project/schemas.py
import uuid
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
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
    id: uuid.UUID
    raw_blueprint: str
    status: str
    structured_outline: Dict[str, Any] | None = None
    total_cost: Decimal
    
    # FIX: Replace Config class with model_config
    model_config = ConfigDict(from_attributes=True)

class PartRead(BaseModel):
    id: uuid.UUID
    part_number: int
    title: str
    summary: str | None = None

    # FIX: Replace Config class with model_config
    model_config = ConfigDict(from_attributes=True)

class ChapterRead(BaseModel):
    id: uuid.UUID
    chapter_number: int
    title: str
    brief: ChapterBrief | None = None
    status: str
    suggested_agent: str | None = None
    # The part relationship might cause issues if not configured correctly, let's keep it simple for now
    # part: PartRead 

    # FIX: Replace Config class with model_config
    model_config = ConfigDict(from_attributes=True)

class PartReadWithChapters(PartRead):
    chapters: list[ChapterRead] = []
    
    # FIX: This also needs the config since it inherits from PartRead but is a new model
    model_config = ConfigDict(from_attributes=True)


class ProjectDetailRead(ProjectRead):
    parts: list[PartReadWithChapters] = []

    # FIX: This also needs the config
    model_config = ConfigDict(from_attributes=True)
    """Read schema for a full Project, including all its Parts and Chapters."""
    parts: list[PartReadWithChapters] = []