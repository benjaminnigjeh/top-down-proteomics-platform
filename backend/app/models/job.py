import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    # pending | queued | running | completed | failed | cancelled

    mzml_file_id: Mapped[str] = mapped_column(String(36))
    fasta_file_id: Mapped[str] = mapped_column(String(36))
    ptm_file_id: Mapped[str] = mapped_column(String(36), nullable=True)

    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    engines_requested: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    celery_task_id: Mapped[str] = mapped_column(String(128), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

    engine_runs: Mapped[list["JobEngine"]] = relationship("JobEngine", back_populates="job", cascade="all, delete")


class JobEngine(Base):
    __tablename__ = "job_engines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"))
    engine_name: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    log: Mapped[str] = mapped_column(Text, default="")
    output_dir: Mapped[str] = mapped_column(String(512), nullable=True)
    result_count: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    job: Mapped["Job"] = relationship("Job", back_populates="engine_runs")
