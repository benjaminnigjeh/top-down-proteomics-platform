"""
FLASHDeconv adapter.

FLASHDeconv is an ultrafast top-down deconvolution tool from OpenMS.
Install: https://github.com/OpenMS/OpenMS  (version >= 3.0 includes FLASHDeconv)
Or: conda install -c openms openms

FLASHDeconv produces .tsv deconvolved spectra that can then be fed to TopPIC.
If unavailable, the adapter will report as not installed.
"""
import subprocess
import shutil
import csv
from pathlib import Path
from typing import Any, Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult


class FLASHDeconvAdapter(SearchEngineAdapter):
    """
    FLASHDeconv deconvolution engine.
    Produces deconvolved spectra; pairs with TopPIC for search.
    """
    name = "flashdeconv"
    version = "unknown"
    input_formats = [".mzml"]
    output_formats = [".tsv", ".mzml"]

    def validate_installation(self) -> bool:
        bin_path = shutil.which("FLASHDeconv") or shutil.which("FLASHDeconvWizard")
        if bin_path:
            try:
                r = subprocess.run([bin_path, "--version"], capture_output=True, text=True, timeout=5)
                import re
                m = re.search(r"([\d.]+)", r.stdout)
                if m:
                    self.version = m.group(1)
            except Exception:
                pass
            return True
        return False

    def _bin(self) -> str:
        from app.config import settings
        return settings.FLASHDECONV_BIN or "FLASHDeconv"

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
        mzml_files = [f for f in input_files if f.suffix.lower() == ".mzml"]
        if not mzml_files:
            raise ValueError("No mzML files for FLASHDeconv")

        for mzml in mzml_files:
            out_tsv = output_dir / (mzml.stem + "_flashdeconv.tsv")
            cmd = [
                self._bin(),
                "-in", str(mzml),
                "-out", str(out_tsv),
                "-out_mzml", str(output_dir / (mzml.stem + "_deconvolved.mzML")),
                "-SD:min_charge", "2",
                "-SD:max_charge", "100",
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                if log_callback:
                    log_callback(line.rstrip())
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"FLASHDeconv failed (exit {proc.returncode})")

    def parse_results(self, output_dir: Path) -> list[ProteoformResult]:
        """Parse FLASHDeconv deconvolved feature table."""
        results = []
        for tsv in output_dir.glob("*_flashdeconv.tsv"):
            results.extend(self._parse_tsv(tsv))
        return results

    def _parse_tsv(self, tsv_path: Path) -> list[ProteoformResult]:
        results = []
        with open(tsv_path, newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                r = ProteoformResult(engine_name=self.name, engine_version=self.version)
                r.scan_number = _safe_int(row.get("ScanNum"))
                r.charge = _safe_int(row.get("MinCharge"))
                r.observed_mass = _safe_float(row.get("NeutralMass"))
                r.score = _safe_float(row.get("IntensityWeight"))
                r.raw_engine_output_path = str(tsv_path)
                results.append(r)
        return results


class FLASHDeconvTopPICAdapter(SearchEngineAdapter):
    """
    Combined FLASHDeconv + TopPIC pipeline.
    FLASHDeconv deconvolves; TopPIC searches against a FASTA database.
    """
    name = "flashdeconv_toppic"
    version = "unknown"
    input_formats = [".mzml"]
    output_formats = [".tsv"]

    def __init__(self):
        from app.engines.flashdeconv import FLASHDeconvAdapter
        from app.engines.toppic import TopPICAdapter
        self._flash = FLASHDeconvAdapter()
        self._toppic = TopPICAdapter()

    def validate_installation(self) -> bool:
        return self._flash.validate_installation() and self._toppic.validate_installation()

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return self._toppic.prepare_database(fasta_path, ptm_config, output_dir)

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        flash_dir = output_dir / "flashdeconv"
        self._flash.run_search(input_files, database_path, params, flash_dir, log_callback)
        deconv_mzmls = list(flash_dir.glob("*_deconvolved.mzML"))
        self._toppic.run_search(deconv_mzmls, database_path, params, output_dir / "toppic", log_callback)

    def parse_results(self, output_dir):
        results = self._toppic.parse_results(output_dir / "toppic")
        for r in results:
            r.engine_name = self.name
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
