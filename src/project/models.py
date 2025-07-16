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
    raw_blueprint = Column(TEXT, nullable=False)
    structured_outline = Column(JSON, nullable=True)
    status = Column(String, default="RAW_IDEA", nullable=False)
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

    # NEW: To track the status of chapter generation for this part.
    status = Column(String, default="DEFINED", nullable=False)

    project = relationship("Project", back_populates="parts")
    chapters = relationship("Chapter", back_populates="part", cascade="all, delete-orphan", order_by="Chapter.chapter_number")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    part_id = Column(UUID(as_uuid=True), ForeignKey("parts.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    brief = Column(JSON, nullable=True)
    content = Column(TEXT, nullable=True)
    status = Column(String, default="BRIEF_PENDING_VALIDATION")
    suggested_agent = Column(String, nullable=True)
    transition_feedback = Column(TEXT, nullable=True)
    part = relationship("Part", back_populates="chapters")