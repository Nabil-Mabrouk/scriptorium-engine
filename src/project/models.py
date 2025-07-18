# src/project/models.py
import uuid
from sqlalchemy import Column, String, TEXT, Integer, Numeric, DateTime, ForeignKey, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from datetime import datetime
from src.core.database import Base

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_blueprint = Column(TEXT, nullable=False)
    # structured_outline = Column(JSON, nullable=True) # OLD: Remove or comment out this line
    
    # NEW: Dedicated JSON columns for drafts
    draft_parts_outline = Column(JSON, nullable=True) # Will store PartListOutline JSON
    draft_chapters_outline = Column(JSON, nullable=True) # Will store a map: {part_id: ChapterListOutline JSON}

    status = Column(String, default="RAW_IDEA", nullable=False)
    summary_outline = Column(TEXT, nullable=True) # Keep existing
    total_cost = Column(Numeric(10, 8), nullable=False, default=0.0)
    parts = relationship("Part", back_populates="project", cascade="all, delete-orphan")

class Part(Base):
    __tablename__ = "parts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    part_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(TEXT, nullable=True)

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
    status = Column(String, default="BRIEF_COMPLETE")
    suggested_agent = Column(String, nullable=True)
    transition_feedback = Column(TEXT, nullable=True)
    part = relationship("Part", back_populates="chapters")
    versions = relationship(
        "ChapterVersion",
        backref="chapter_object", # Renamed backref to avoid conflict with `chapter` column name (if one existed, though unlikely here)
        cascade="all, delete-orphan",
        order_by="ChapterVersion.created_at"
    )

class ChapterVersion(Base):
    __tablename__ = "chapter_versions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    content = Column(TEXT, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)