"""TruncNet adapter — placeholder for ProteoBio AI N/C-terminal truncation detection."""
from pathlib import Path
from typing import Any, Optional
from app.engines.base import SearchEngineAdapter, ProteoformResult


class TruncNetAdapter(SearchEngineAdapter):
    name = "truncnet"
    version = "placeholder"
    category = "ai"
    description = "TruncNet (ProteoBio AI) -- Neural network for N/C-terminal truncation detection [coming soon]"
    input_formats = [".mzml"]
    output_formats = [".json"]

    def validate_installation(self) -> bool:
        return False

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        raise NotImplementedError("TruncNet not yet installed.")

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        raise NotImplementedError("TruncNet not yet available.")

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        raise NotImplementedError

