from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class SearchParameters(BaseModel):
    precursor_tolerance_ppm: float = 10.0
    fragment_tolerance_ppm: float = 15.0
    fixed_modifications: list[str] = []
    variable_modifications: list[str] = []
    max_unexpected_mass_shift: float = 500.0
    fdr_threshold: float = 0.01
    protease: str = "no_cleavage"
    min_score: float = 0.0
    max_ptm_count: int = 5
    deconvolution_engine: str = "topfd"
    search_engine: str = "toppic"


class JobCreate(BaseModel):
    name: str
    mzml_file_id: str
    fasta_file_id: str
    ptm_file_id: Optional[str] = None
    engines: list[str]
    parameters: SearchParameters = SearchParameters()


class JobEngineRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    engine_name: str
    status: str
    log: str
    result_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    status: str
    mzml_file_id: str
    fasta_file_id: str
    ptm_file_id: Optional[str] = None
    parameters: dict[str, Any]
    engines_requested: list[str]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    engine_runs: list[JobEngineRead] = []


class JobStatus(BaseModel):
    job_id: str
    status: str
    progress_percent: float
    engine_statuses: dict[str, str]
    total_results: int
