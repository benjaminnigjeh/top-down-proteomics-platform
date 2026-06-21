import uuid
from sqlalchemy import String, Float, Integer, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProteoformResult(Base):
    __tablename__ = "proteoform_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"))
    job_engine_id: Mapped[str] = mapped_column(String(36), ForeignKey("job_engines.id", ondelete="CASCADE"))

    engine_name: Mapped[str] = mapped_column(String(64))
    engine_version: Mapped[str] = mapped_column(String(32), nullable=True)

    spectrum_id: Mapped[str] = mapped_column(String(128), nullable=True)
    scan_number: Mapped[int] = mapped_column(Integer, nullable=True)
    source_file: Mapped[str] = mapped_column(String(256), nullable=True)

    precursor_mz: Mapped[float] = mapped_column(Float, nullable=True)
    charge: Mapped[int] = mapped_column(Integer, nullable=True)
    observed_mass: Mapped[float] = mapped_column(Float, nullable=True)
    theoretical_mass: Mapped[float] = mapped_column(Float, nullable=True)
    delta_mass: Mapped[float] = mapped_column(Float, nullable=True)

    accession: Mapped[str] = mapped_column(String(128), nullable=True)
    protein_name: Mapped[str] = mapped_column(Text, nullable=True)
    sequence: Mapped[str] = mapped_column(Text, nullable=True)
    proteoform_string: Mapped[str] = mapped_column(Text, nullable=True)
    proteoform_mass: Mapped[float] = mapped_column(Float, nullable=True)

    score: Mapped[float] = mapped_column(Float, nullable=True)
    evalue: Mapped[float] = mapped_column(Float, nullable=True)
    qvalue: Mapped[float] = mapped_column(Float, nullable=True)
    fdr: Mapped[float] = mapped_column(Float, nullable=True)

    matched_fragments: Mapped[int] = mapped_column(Integer, nullable=True)
    sequence_coverage: Mapped[float] = mapped_column(Float, nullable=True)

    ptms: Mapped[list] = mapped_column(JSON, default=list)
    localization_confidence: Mapped[float] = mapped_column(Float, nullable=True)

    raw_engine_output_path: Mapped[str] = mapped_column(String(512), nullable=True)
    is_demo: Mapped[bool] = mapped_column(default=False)
