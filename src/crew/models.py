import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, UUID
from src.core.database import Base


class CrewRunLog(Base):
    __tablename__ = "crew_run_logs" # New table name

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    # A descriptive name for the overall job that was run.
    initiating_task_name = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    total_cost = Column(Numeric(10, 8), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)