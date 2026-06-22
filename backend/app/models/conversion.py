import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Conversion(Base):
    __tablename__ = "conversions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    # pending | running | completed | failed

    # Input
    input_file_id: Mapped[str] = mapped_column(String(36))
    input_filename: Mapped[str] = mapped_column(String(512))
    tool: Mapped[str] = mapped_column(String(64), default="msconvert")
    # msconvert | thermoparser | openms | thrash | unidec | xtract

    # Options stored as JSON
    options: Mapped[dict] = mapped_column(JSON, default=dict)

    # Output
    output_filename: Mapped[str] = mapped_column(String(512), nullable=True)
    output_path: Mapped[str] = mapped_column(String(1024), nullable=True)
    output_size_bytes: Mapped[int] = mapped_column(Integer, nullable=True)

    # Execution
    celery_task_id: Mapped[str] = mapped_column(String(128), nullable=True)
    log: Mapped[str] = mapped_column(Text, default="")
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
