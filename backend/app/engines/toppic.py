"""
TopPIC Suite adapter.

Integrates TopFD (deconvolution) + TopPIC (proteoform identification).
Requires TopPIC Suite >= 1.6 installed and on PATH.
Install: https://github.com/toppic-suite/toppic-suite/releases
"""
import subprocess
import shutil
import re
import csv
from pathlib import Path
from typing import Any, Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult


class TopPICAdapter(SearchEngineAdapter):
    name = "toppic"
    version = "unknown"
    input_formats = [".mzml", ".mzxml"]
    output_formats = [".tsv", ".xml", ".html"]

    def validate_installation(self) -> bool:
        topfd = shutil.which(self._topfd_bin())
        toppic = shutil.which(self._toppic_bin())
        if topfd and toppic:
            try:
                r = subprocess.run([toppic, "--version"], capture_output=True, text=True, timeout=5)
                m = re.search(r"TopPIC\s+([\d.]+)", r.stdout + r.stderr)
                if m:
                    self.version = m.group(1)
            except Exception:
                pass
            return True
        return False

    def _topfd_bin(self) -> str:
        from app.config import settings
        return settings.TOPFD_BIN or "topfd"

    def _toppic_bin(self) -> str:
        from app.config import settings
        return settings.TOPPIC_BIN or "toppic"

    def prepare_database(self, fasta_path: Path, ptm_config: Optional[Path], output_dir: Path) -> Path:
        # TopPIC uses the FASTA directly; return its path
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
            raise ValueError("No mzML/mzXML files provided for TopPIC")

        for mzml in mzml_files:
            self._run_topfd(mzml, output_dir, params, log_callback)
            msalign = output_dir / (mzml.stem + "_ms2.msalign")
            if msalign.exists():
                self._run_toppic(msalign, database_path, output_dir, params, log_callback)

    def _run_topfd(self, mzml: Path, output_dir: Path, params: dict, log_callback) -> None:
        cmd = [
            self._topfd_bin(),
            "--output-dir", str(output_dir),
            str(mzml),
        ]
        self._run_subprocess(cmd, log_callback)

    def _run_toppic(self, msalign: Path, fasta: Path, output_dir: Path, params: dict, log_callback) -> None:
        cmd = [
            self._toppic_bin(),
            "--activation", "ETD",
            "--fixed-mod", ",".join(params.get("fixed_modifications", [])) or "C57",
            "--n-unknown-shift", str(params.get("max_ptm_count", 1)),
            "--error-tol", str(params.get("fragment_tolerance_ppm", 15)),
            "--thread-number", "4",
            str(fasta),
            str(msalign),
        ]
        self._run_subprocess(cmd, log_callback)

    def _run_subprocess(self, cmd: list, log_callback) -> None:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            if log_callback:
                log_callback(line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"Command failed with exit code {proc.returncode}: {' '.join(str(c) for c in cmd)}")

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        results = []
        # TopPIC outputs *_ms2_toppic_proteoform.tsv
        for tsv in output_dir.glob("*toppic_proteoform.tsv"):
            results.extend(self._parse_proteoform_tsv(tsv))
        # Also check prsm table
        for tsv in output_dir.glob("*toppic_prsm.tsv"):
            results.extend(self._parse_prsm_tsv(tsv))
        return results

    def _parse_proteoform_tsv(self, tsv_path: Path) -> list[ProteoformResult]:
        results = []
        with open(tsv_path, newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                r = ProteoformResult(engine_name=self.name, engine_version=self.version)
                r.accession = row.get("Protein accession", "")
                r.protein_name = row.get("Protein name", "")
                r.sequence = row.get("First residue", "")
                r.proteoform_string = row.get("Proteoform", "")
                r.proteoform_mass = _float(row.get("Proteoform mass"))
                r.score = _float(row.get("Feature score"))
                r.evalue = _float(row.get("E-value"))
                r.qvalue = _float(row.get("FDR"))
                r.fdr = r.qvalue
                r.matched_fragments = _int(row.get("Matched fragment number"))
                r.sequence_coverage = _float(row.get("Sequence coverage"))
                r.ptms = _parse_ptm_string(row.get("Variable PTMs", ""))
                r.raw_engine_output_path = str(tsv_path)
                results.append(r)
        return results

    def _parse_prsm_tsv(self, tsv_path: Path) -> list[ProteoformResult]:
        results = []
        with open(tsv_path, newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                r = ProteoformResult(engine_name=self.name, engine_version=self.version)
                r.spectrum_id = row.get("Spectrum ID", "")
                r.scan_number = _int(row.get("Scan(s)", ""))
                r.source_file = row.get("Data file name", "")
                r.precursor_mz = _float(row.get("Precursor mono mass"))
                r.charge = _int(row.get("Charge", ""))
                r.observed_mass = _float(row.get("Precursor mass"))
                r.theoretical_mass = _float(row.get("Proteoform mass"))
                r.delta_mass = _float(row.get("Unexpected modifications mass shift"))
                r.accession = row.get("Protein accession", "")
                r.protein_name = row.get("Protein name", "")
                r.sequence = row.get("First residue", "")
                r.proteoform_string = row.get("Proteoform", "")
                r.score = _float(row.get("PrSM score"))
                r.evalue = _float(row.get("E-value"))
                r.qvalue = _float(row.get("FDR"))
                r.fdr = r.qvalue
                r.matched_fragments = _int(row.get("Matched fragment number"))
                r.sequence_coverage = _float(row.get("Sequence coverage"))
                r.ptms = _parse_ptm_string(row.get("Variable PTMs", ""))
                r.raw_engine_output_path = str(tsv_path)
                results.append(r)
        return results


class TopMGAdapter(TopPICAdapter):
    """TopPIC Suite's TopMG for proteogenomics / unexpected modifications."""
    name = "topmg"

    def _toppic_bin(self) -> str:
        from app.config import settings
        return settings.TOPMG_BIN or "topmg"

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        results = []
        for tsv in output_dir.glob("*topmg_proteoform.tsv"):
            results.extend(self._parse_proteoform_tsv(tsv))
        for tsv in output_dir.glob("*topmg_prsm.tsv"):
            results.extend(self._parse_prsm_tsv(tsv))
        return results


def _float(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int(v) -> Optional[int]:
    try:
        return int(str(v).split("-")[0].strip())
    except (TypeError, ValueError):
        return None


def _parse_ptm_string(s: str) -> list[dict]:
    """Parse TopPIC PTM string like 'phospho[S3];acetyl[K5]'."""
    ptms = []
    if not s:
        return ptms
    for part in s.split(";"):
        part = part.strip()
        m = re.match(r"(.+)\[([A-Z])(\d+)\]", part)
        if m:
            ptms.append({"modification": m.group(1), "residue": m.group(2), "position": int(m.group(3))})
    return ptms
