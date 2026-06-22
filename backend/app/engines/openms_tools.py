"""
OpenMS preprocessing tool adapters.

These tools are part of OpenMS 3.x and perform preprocessing steps
(peak picking, charge deconvolution, feature detection) rather than
database searching. They are used upstream of a search engine.

All tools are expected at C:/Program Files/OpenMS-3.5.0/bin/
"""
import subprocess
import shutil
import csv
from pathlib import Path
from typing import Any, Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult

OPENMS_BIN = r"C:\Program Files\OpenMS-3.5.0\bin"


def _openms_bin(tool: str) -> str:
    import os
    local = os.path.join(OPENMS_BIN, tool + ".exe")
    if os.path.exists(local):
        return local
    return shutil.which(tool) or tool


def _run(cmd: list, log_callback=None) -> int:
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if log_callback:
            log_callback(line.rstrip())
    proc.wait()
    return proc.returncode


class PeakPickerAdapter(SearchEngineAdapter):
    """OpenMS PeakPickerHiRes — converts profile spectra to centroid peaks."""
    name = "peakpicker"
    version = "unknown"
    category = "deconvolution"
    description = "PeakPickerHiRes (OpenMS) — Converts profile-mode spectra to centroid peaks. Required preprocessing step before most search engines."
    input_formats = [".mzml"]
    output_formats = [".mzml"]

    def validate_installation(self) -> bool:
        import os
        path = _openms_bin("PeakPickerHiRes")
        exists = os.path.exists(path) if os.sep in path else bool(shutil.which(path))
        if exists:
            r = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
            import re
            m = re.search(r"([\d.]+)", r.stdout + r.stderr)
            if m:
                self.version = m.group(1)
        return exists

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() == ".mzml"]
        if not mzml_files:
            raise ValueError("No mzML files for PeakPickerHiRes")
        bin_ = _openms_bin("PeakPickerHiRes")
        for mzml in mzml_files:
            out = output_dir / (mzml.stem + "_centroided.mzML")
            rc = _run([bin_, "-in", str(mzml), "-out", str(out)], log_callback)
            if rc != 0:
                raise RuntimeError(f"PeakPickerHiRes failed (exit {rc})")

    def parse_results(self, output_dir):
        # Peak picking produces a new mzML — report the output files as metadata
        results = []
        for mzml in output_dir.glob("*_centroided.mzML"):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.source_file = str(mzml)
            r.raw_engine_output_path = str(mzml)
            results.append(r)
        return results


class DechargerAdapter(SearchEngineAdapter):
    """OpenMS Decharger — deconvolves MS1 spectra by grouping charge variants."""
    name = "decharger"
    version = "unknown"
    category = "deconvolution"
    description = "Decharger (OpenMS) — Groups multiply-charged MS1 isotope envelopes into neutral masses. Lighter-weight alternative to FLASHDeconv for some datasets."
    input_formats = [".mzml"]
    output_formats = [".mzml", ".featureXML"]

    def validate_installation(self) -> bool:
        import os
        path = _openms_bin("Decharger")
        exists = os.path.exists(path) if os.sep in path else bool(shutil.which(path))
        if exists:
            r = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
            import re
            m = re.search(r"([\d.]+)", r.stdout + r.stderr)
            if m:
                self.version = m.group(1)
        return exists

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() == ".mzml"]
        if not mzml_files:
            raise ValueError("No mzML files for Decharger")
        bin_ = _openms_bin("Decharger")
        for mzml in mzml_files:
            out_pos = output_dir / (mzml.stem + "_decharged_pos.featureXML")
            out_neg = output_dir / (mzml.stem + "_decharged_neg.featureXML")
            out_mzml = output_dir / (mzml.stem + "_decharged.mzML")
            rc = _run([
                bin_,
                "-in", str(mzml),
                "-out_pos", str(out_pos),
                "-out_neg", str(out_neg),
                "-out_cm", str(out_mzml),
            ], log_callback)
            if rc != 0:
                raise RuntimeError(f"Decharger failed (exit {rc})")

    def parse_results(self, output_dir):
        results = []
        for fx in output_dir.glob("*_decharged_pos.featureXML"):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.source_file = str(fx)
            r.raw_engine_output_path = str(fx)
            results.append(r)
        return results


class FeatureFinderCentroidedAdapter(SearchEngineAdapter):
    """OpenMS FeatureFinderCentroided — detects LC-MS features from centroided data."""
    name = "featurefinder"
    version = "unknown"
    category = "deconvolution"
    description = "FeatureFinderCentroided (OpenMS) — Detects LC-MS features (peptide/protein signals) from centroided spectra. Useful for label-free quantification preprocessing."
    input_formats = [".mzml"]
    output_formats = [".featureXML", ".tsv"]

    def validate_installation(self) -> bool:
        import os
        path = _openms_bin("FeatureFinderCentroided")
        exists = os.path.exists(path) if os.sep in path else bool(shutil.which(path))
        if exists:
            r = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
            import re
            m = re.search(r"([\d.]+)", r.stdout + r.stderr)
            if m:
                self.version = m.group(1)
        return exists

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() == ".mzml"]
        if not mzml_files:
            raise ValueError("No mzML files for FeatureFinderCentroided")
        bin_ = _openms_bin("FeatureFinderCentroided")
        for mzml in mzml_files:
            out = output_dir / (mzml.stem + "_features.featureXML")
            rc = _run([bin_, "-in", str(mzml), "-out", str(out)], log_callback)
            if rc != 0:
                raise RuntimeError(f"FeatureFinderCentroided failed (exit {rc})")

    def parse_results(self, output_dir):
        results = []
        for fx in output_dir.glob("*_features.featureXML"):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.source_file = str(fx)
            r.raw_engine_output_path = str(fx)
            results.append(r)
        return results


class ProMexAdapter(SearchEngineAdapter):
    """ProMex (Informed Proteomics) — LC-MS/MS feature detection for top-down data."""
    name = "promex"
    version = "unknown"
    category = "deconvolution"
    description = "ProMex (Informed Proteomics / PNNL) — Deconvolves top-down LC-MS data into a list of protein features. Pairs naturally with MSPathFinderT."
    input_formats = [".mzml", ".pbf", ".raw"]
    output_formats = [".ms1ft", ".tsv"]

    def validate_installation(self) -> bool:
        import os
        path = PROMEX_BIN if os.path.exists(PROMEX_BIN) else shutil.which("ProMex")
        if path:
            r = subprocess.run([path], capture_output=True, text=True, timeout=5)
            import re
            m = re.search(r"([\d.]+)", r.stdout + r.stderr)
            if m:
                self.version = m.group(1)
            return True
        return False

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        import os
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() in (".mzml", ".pbf", ".raw")]
        if not mzml_files:
            raise ValueError("No mzML/.pbf files for ProMex")
        path = PROMEX_BIN if os.path.exists(PROMEX_BIN) else shutil.which("ProMex") or "ProMex"
        for mzml in mzml_files:
            rc = _run([
                path,
                "-i", str(mzml),
                "-o", str(output_dir),
                "-minCharge", str(params.get("min_charge", 2)),
                "-maxCharge", str(params.get("max_charge", 60)),
                "-minMass",   str(params.get("min_mass", 2000)),
                "-maxMass",   str(params.get("max_mass", 50000)),
            ], log_callback)
            if rc != 0:
                raise RuntimeError(f"ProMex failed (exit {rc})")

    def parse_results(self, output_dir):
        results = []
        for tsv in output_dir.glob("*.ms1ft"):
            results.extend(self._parse_ms1ft(tsv))
        return results

    def _parse_ms1ft(self, path: Path):
        results = []
        try:
            with open(path, newline="") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    r = ProteoformResult(engine_name=self.name, engine_version=self.version)
                    r.observed_mass = _safe_float(row.get("MonoMass") or row.get("Mass"))
                    r.charge = _safe_int(row.get("Charge") or row.get("MinCharge"))
                    r.score = _safe_float(row.get("Probability") or row.get("Score"))
                    r.raw_engine_output_path = str(path)
                    results.append(r)
        except Exception:
            pass
        return results


PROMEX_BIN = r"C:\tools\InformedProteomics\ProMex.exe"


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
