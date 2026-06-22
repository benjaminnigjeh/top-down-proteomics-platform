"""
MSPathFinderT adapter (Informed Proteomics).

MSPathFinderT is part of the Informed Proteomics suite from PNNL.
Install: https://github.com/PNNL-Comp-Mass-Spec/Informed-Proteomics
Requires .NET runtime (cross-platform via dotnet tool or wine on Linux).

If MSPathFinderT is not installed, the adapter will raise a clear error.
Installation instructions: see scripts/install_mspathfinder.sh
"""
import subprocess
import shutil
import csv
from pathlib import Path
from typing import Any, Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult


MSPATHFINDER_BIN = r"C:\tools\InformedProteomics\MSPathFinderT.exe"
PROMEX_BIN = r"C:\tools\InformedProteomics\ProMex.exe"
PBFGEN_BIN = r"C:\tools\InformedProteomics\PbfGen.exe"


class MSPathFinderTAdapter(SearchEngineAdapter):
    name = "mspathfindert"
    version = "unknown"
    category = "search"
    description = "MSPathFinderT (Informed Proteomics / PNNL) — Database search for intact proteins; generates PBF index for fast re-searching"
    input_formats = [".mzml", ".pbf", ".raw"]
    output_formats = [".tsv", ".mzid"]

    def validate_installation(self) -> bool:
        import os
        bin_path = (shutil.which("MSPathFinderT") or shutil.which("mspathfindert")
                    or (MSPATHFINDER_BIN if os.path.exists(MSPATHFINDER_BIN) else None))
        if bin_path:
            try:
                r = subprocess.run([bin_path, "-version"], capture_output=True, text=True, timeout=5)
                import re
                m = re.search(r"MSPathFinder\s+([\d.]+)", r.stdout + r.stderr)
                if m:
                    self.version = m.group(1)
            except Exception:
                pass
            return True
        return False

    def _bin(self) -> str:
        import os
        from app.config import settings
        return (settings.MSPATHFINDER_BIN
                or shutil.which("MSPathFinderT")
                or (MSPATHFINDER_BIN if os.path.exists(MSPATHFINDER_BIN) else "MSPathFinderT"))

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
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
        mzml_files = [f for f in input_files if f.suffix.lower() in (".mzml", ".pbf")]
        if not mzml_files:
            raise ValueError("No mzML/.pbf files for MSPathFinderT")

        for mzml in mzml_files:
            cmd = [
                self._bin(),
                "-s", str(mzml),
                "-d", str(database_path),
                "-o", str(output_dir),
                "-t", str(params.get("precursor_tolerance_ppm", 10)),
                "-f", str(params.get("fragment_tolerance_ppm", 15)),
                "-ntt", "0",  # top-down: no enzymatic specificity
                "-tda", "1",  # target-decoy
                "-minLength", "21",
                "-maxLength", "300",
                "-minCharge", "2",
                "-maxCharge", "60",
            ]
            # Add modifications if specified
            if params.get("fixed_modifications"):
                cmd += ["-mod", ",".join(params["fixed_modifications"])]

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                if log_callback:
                    log_callback(line.rstrip())
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"MSPathFinderT failed (exit {proc.returncode})")

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        results = []
        for tsv in output_dir.glob("*_IcTda.tsv"):
            results.extend(self._parse_tsv(tsv))
        return results

    def _parse_tsv(self, tsv_path: Path) -> list[ProteoformResult]:
        results = []
        with open(tsv_path, newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                r = ProteoformResult(engine_name=self.name, engine_version=self.version)
                r.scan_number = _safe_int(row.get("Scan"))
                r.charge = _safe_int(row.get("Charge"))
                r.precursor_mz = _safe_float(row.get("PrecursorMz"))
                r.observed_mass = _safe_float(row.get("Mass"))
                r.accession = row.get("ProteinId", "")
                r.protein_name = row.get("ProteinName", "")
                r.sequence = row.get("Sequence", "")
                r.proteoform_string = row.get("Modifications", "")
                r.score = _safe_float(row.get("#MatchedFragments"))
                r.matched_fragments = _safe_int(row.get("#MatchedFragments"))
                r.evalue = _safe_float(row.get("EValue"))
                r.qvalue = _safe_float(row.get("QValue"))
                r.fdr = r.qvalue
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
