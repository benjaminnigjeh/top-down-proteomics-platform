"""ProteoEngine adapter — placeholder for ProteoBio's integrated AI search engine."""
from pathlib import Path
from typing import Any, Optional
from app.engines.base import SearchEngineAdapter, ProteoformResult


class ProteoEngineAdapter(SearchEngineAdapter):
    name = "proteoengine"
    version = "placeholder"
    category = "ai"
    description = "ProteoEngine (ProteoBio AI) -- Integrated AI search engine for top-down proteomics [coming soon]"
    input_formats = [".mzml"]
    output_formats = [".json", ".tsv"]

    def validate_installation(self) -> bool:
        return False

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        raise NotImplementedError("ProteoEngine not yet installed.")

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        raise NotImplementedError("ProteoEngine not yet available.")

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        raise NotImplementedError

