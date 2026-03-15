from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.database import Base
import uuid

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=True)
    status = Column(String, default="PENDING")
    priority = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    result = Column(JSONB, nullable=True)

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True)
    status = Column(String, default="ACTIVE")
    current_task_id = Column(String, nullable=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    tasks_completed = Column(Integer, default=0)

