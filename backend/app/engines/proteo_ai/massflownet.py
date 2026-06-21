"""MassFlowNet adapter — placeholder for ProteoBio AI mass shift flow network."""
from pathlib import Path
from typing import Any, Optional
from app.engines.base import SearchEngineAdapter, ProteoformResult


class MassFlowNetAdapter(SearchEngineAdapter):
    name = "massflownet"
    version = "placeholder"
    input_formats = [".mzml"]
    output_formats = [".json"]

    def validate_installation(self) -> bool:
        return False

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        raise NotImplementedError("MassFlowNet not yet installed.")

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        raise NotImplementedError("MassFlowNet not yet available.")

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        raise NotImplementedError
