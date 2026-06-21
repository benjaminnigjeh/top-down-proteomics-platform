"""
TopLib spectral library search adapter.

TopLib enables spectral library-based search for top-down proteomics.
It is part of the TopPIC Suite and must be installed alongside it.
Install: https://github.com/toppic-suite/toppic-suite/releases
"""
import subprocess
import shutil
import csv
from pathlib import Path
from typing import Any, Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult


class TopLibAdapter(SearchEngineAdapter):
    name = "toplib"
    version = "unknown"
    input_formats = [".mzml", ".mzxml", ".splib"]
    output_formats = [".tsv"]

    def validate_installation(self) -> bool:
        bin_path = shutil.which("toplib") or shutil.which("TopLib")
        if bin_path:
            try:
                r = subprocess.run([bin_path, "--version"], capture_output=True, text=True, timeout=5)
                import re
                m = re.search(r"TopLib\s+([\d.]+)", r.stdout + r.stderr)
                if m:
                    self.version = m.group(1)
            except Exception:
                pass
            return True
        return False

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        # TopLib uses a spectral library (.splib); FASTA is secondary
        splib = list(fasta_path.parent.glob("*.splib"))
        if splib:
            return splib[0]
        return fasta_path

    def run_search(
        self,
        input_files: list[Path],
        database_path: Path,
        params: dict[str, Any],
        output_dir: Path,
        log_callback=None,
    ) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() in (".mzml", ".mzxml")]
        if not mzml_files:
            raise ValueError("No mzML files for TopLib")

        for mzml in mzml_files:
            cmd = [
                "toplib",
                str(database_path),
                str(mzml),
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                if log_callback:
                    log_callback(line.rstrip())
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"TopLib failed (exit {proc.returncode})")

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        results = []
        for tsv in output_dir.glob("*toplib*.tsv"):
            results.extend(self._parse_tsv(tsv))
        return results

    def _parse_tsv(self, tsv_path: Path) -> list[ProteoformResult]:
        results = []
        with open(tsv_path, newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                r = ProteoformResult(engine_name=self.name, engine_version=self.version)
                r.scan_number = _safe_int(row.get("Scan"))
                r.accession = row.get("Accession", "")
                r.proteoform_string = row.get("Proteoform", "")
                r.score = _safe_float(row.get("Score"))
                r.qvalue = _safe_float(row.get("FDR"))
                r.raw_engine_output_path = str(tsv_path)
                results.append(r)
        return results


def _safe_float(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_int(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
