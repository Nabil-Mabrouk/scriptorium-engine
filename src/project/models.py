# src/project/models.py
import uuid
from sqlalchemy import Column, String, TEXT, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import UUID
from src.core.database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # --- MODIFICATION ---
    # The blueprint is now a simple text field, not a structured JSON object.
    blueprint = Column(TEXT, nullable=False)
    
    summary_outline = Column(TEXT, nullable=True)
    total_cost = Column(Numeric(10, 8), nullable=False, default=0.0)
    parts = relationship("Part", back_populates="project", cascade="all, delete-orphan")


class Part(Base):
    __tablename__ = "parts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    part_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(TEXT, nullable=True)
    # Relationship from Part to Project and Chapter
    project = relationship("Project", back_populates="parts")
    chapters = relationship("Chapter", back_populates="part", cascade="all, delete-orphan")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # A chapter now belongs to a Part, not a Project directly
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    brief = Column(JSON, nullable=True)
    content = Column(TEXT, nullable=True)
    status = Column(String, default="Pending")
    # Add a field for the agent suggestion from the blueprint
    suggested_agent = Column(String, nullable=True)
    # Relationship from Chapter back to Part
    part = relationship("Part", back_populates="chapters")