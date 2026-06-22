from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any


@dataclass
class ProteoformResult:
    engine_name: str
    engine_version: Optional[str] = None
    job_id: Optional[str] = None

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

    ptms: list[dict[str, Any]] = field(default_factory=list)
    localization_confidence: Optional[float] = None

    raw_engine_output_path: Optional[str] = None
    is_demo: bool = False


class SearchEngineAdapter(ABC):
    name: str = ""
    version: str = "unknown"
    input_formats: list[str] = []
    output_formats: list[str] = []
    # category: "search" | "deconvolution" | "pipeline" | "demo" | "ai"
    category: str = "search"
    description: str = ""

    @abstractmethod
    def validate_installation(self) -> bool:
        """Return True if this engine is installed and ready to run."""

    @abstractmethod
    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        """Prepare the protein database for searching. Returns path to prepared DB."""

    @abstractmethod
    def run_search(
        self,
        input_files: list[Path],
        database_path: Path,
        params: dict[str, Any],
        output_dir: Path,
        log_callback=None,
    ) -> None:
        """Execute the search engine. Logs captured via log_callback(line: str)."""

    @abstractmethod
    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        """Parse raw engine output into standardized ProteoformResult objects."""

    def estimate_fdr(self, results: list[ProteoformResult]) -> list[ProteoformResult]:
        """Optional: re-estimate or validate FDR on parsed results."""
        return results

    def export_standardized(self, results: list[ProteoformResult], output_dir: Path) -> Path:
        """Write a standardized TSV of results. Returns path."""
        import csv
        out = output_dir / f"{self.name}_standardized.tsv"
        if not results:
            out.write_text("")
            return out
        keys = list(results[0].__dataclass_fields__.keys())
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys, delimiter="\t")
            w.writeheader()
            for r in results:
                w.writerow({k: getattr(r, k) for k in keys})
        return out

    def get_info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
            "input_formats": self.input_formats,
            "output_formats": self.output_formats,
            "available": self.validate_installation(),
        }
