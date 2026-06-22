"""
ProteoID adapter — placeholder for ProteoBio AI proteoform identification engine.

To activate: implement validate_installation, run_search, and parse_results
with the real ProteoID inference pipeline.
"""
from pathlib import Path
from typing import Any, Optional
from app.engines.base import SearchEngineAdapter, ProteoformResult


class ProteoIDAdapter(SearchEngineAdapter):
    name = "proteoid"
    version = "placeholder"
    category = "ai"
    description = "ProteoID (ProteoBio AI) -- AI-based proteoform identification using deep learning [coming soon]"
    input_formats = [".mzml"]
    output_formats = [".json", ".tsv"]

    def validate_installation(self) -> bool:
        return False  # Set to True when model weights and runtime are available

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        raise NotImplementedError("ProteoID is not yet installed. See README for integration instructions.")

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        raise NotImplementedError("ProteoID is not yet available. Check https://proteobio.ai for release schedule.")

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        raise NotImplementedError("ProteoID parser not implemented.")

