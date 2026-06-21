from typing import Optional, Any
from pydantic import BaseModel


class PTMAnnotation(BaseModel):
    position: int
    residue: str
    modification: str
    mass_shift: float
    source: str = "engine"


class ProteoformResultRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    job_id: str
    job_engine_id: str
    engine_name: str
    engine_version: Optional[str] = None

    spectrum_id: Optional[str] = None
    scan_number: Optional[int] = None
    source_file: Optional[str] = None

    precursor_mz: Optional[float] = None
    charge: Optional[int] = None
    observed_mass: Optional[float] = None
    theoretical_mass: Optional[float] = None
    delta_mass: Optional[float] = None

    accession: Optional[str] = None
    protein_name: Optional[str] = None
    sequence: Optional[str] = None
    proteoform_string: Optional[str] = None
    proteoform_mass: Optional[float] = None

    score: Optional[float] = None
    evalue: Optional[float] = None
    qvalue: Optional[float] = None
    fdr: Optional[float] = None

    matched_fragments: Optional[int] = None
    sequence_coverage: Optional[float] = None

    ptms: list[dict[str, Any]] = []
    localization_confidence: Optional[float] = None
    is_demo: bool = False


class ResultFilter(BaseModel):
    engine_names: Optional[list[str]] = None
    max_qvalue: Optional[float] = None
    min_score: Optional[float] = None
    accession: Optional[str] = None
    min_sequence_coverage: Optional[float] = None
    has_ptms: Optional[bool] = None
    page: int = 1
    page_size: int = 50
