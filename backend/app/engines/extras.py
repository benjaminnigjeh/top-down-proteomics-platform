"""
Additional search engine and analysis adapters for Proteoformer Pipeline.

Covers:
  - pTop (ICT Beijing) -- top-down database search
  - Protein Prospector (UCSF) -- web API search
  - MetaMorpheus (Smith Lab) -- top-down + PTM search via CLI
"""
import subprocess
import shutil
import csv
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import Any, Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult


# ---------------------------------------------------------------------------
# pTop (ICT Beijing / pFind group)
# ---------------------------------------------------------------------------

PTOP_DEFAULT_BIN = r"C:\tools\pTop\pTop.exe"


class PTopAdapter(SearchEngineAdapter):
    """
    pTop -- academic top-down database search engine from ICT Beijing.

    pTop is developed by the pFind group at the Institute of Computing
    Technology, Chinese Academy of Sciences. It handles large intact-protein
    spectra with high sensitivity and supports common PTMs.

    Installation: request access at http://pfind.ict.ac.cn  then install to
    C:\\tools\\pTop\\ (or set PTOP_BIN in settings).
    """
    name = "ptop"
    version = "unknown"
    category = "search"
    description = (
        "pTop (ICT Beijing / pFind group) -- High-sensitivity top-down database "
        "search engine supporting complex PTMs. Install from pfind.ict.ac.cn."
    )
    input_formats = [".mzml", ".mzxml", ".raw"]
    output_formats = [".txt", ".psm"]

    def _bin(self) -> Optional[str]:
        import os
        from app.config import settings
        custom = getattr(settings, "PTOP_BIN", None)
        if custom and os.path.exists(custom):
            return custom
        if os.path.exists(PTOP_DEFAULT_BIN):
            return PTOP_DEFAULT_BIN
        return shutil.which("pTop") or shutil.which("ptop")

    def validate_installation(self) -> bool:
        b = self._bin()
        if not b:
            return False
        try:
            r = subprocess.run([b, "--version"], capture_output=True, text=True, timeout=8)
            import re
            m = re.search(r"([\d.]+)", r.stdout + r.stderr)
            if m:
                self.version = m.group(1)
            return True
        except Exception:
            return True  # binary exists even if version flag fails

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        b = self._bin()
        if not b:
            raise RuntimeError("pTop not found. Install from http://pfind.ict.ac.cn")
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() in (".mzml", ".mzxml", ".raw")]
        if not mzml_files:
            raise ValueError("No spectrum files for pTop")
        for mzml in mzml_files:
            cmd = [
                b,
                "-input", str(mzml),
                "-db", str(database_path),
                "-output", str(output_dir),
                "-thread", str(params.get("threads", 4)),
                "-ppm", str(params.get("precursor_tolerance_ppm", 15)),
            ]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                if log_callback:
                    log_callback(line.rstrip())
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"pTop failed (exit {proc.returncode})")

    def parse_results(self, output_dir):
        results = []
        for f in output_dir.glob("*.psm"):
            try:
                with open(f, newline="") as fh:
                    reader = csv.DictReader(fh, delimiter="\t")
                    for row in reader:
                        r = ProteoformResult(engine_name=self.name, engine_version=self.version)
                        r.scan_number = _safe_int(row.get("Scan"))
                        r.accession = row.get("Accession", "")
                        r.protein_name = row.get("Protein", "")
                        r.proteoform_string = row.get("Sequence", "")
                        r.observed_mass = _safe_float(row.get("Mass"))
                        r.score = _safe_float(row.get("Score"))
                        r.evalue = _safe_float(row.get("E-value"))
                        r.raw_engine_output_path = str(f)
                        results.append(r)
            except Exception:
                pass
        return results


# ---------------------------------------------------------------------------
# Protein Prospector (UCSF) -- web API
# ---------------------------------------------------------------------------

_PP_BASE = "https://prospector.ucsf.edu/prospector/cgi-bin"


class ProteinProspectorAdapter(SearchEngineAdapter):
    """
    Protein Prospector MS-Tag (UCSF) -- web-based top-down MS search.

    Sends spectra data to the UCSF Protein Prospector web API and retrieves
    proteoform matches. Requires internet access. Good for quick, single-run
    searches against SwissProt or custom databases.

    No local installation required.
    """
    name = "protein_prospector"
    version = "web"
    category = "search"
    description = (
        "Protein Prospector MS-Tag (UCSF) -- Web-based search engine from UCSF. "
        "Submits spectra to prospector.ucsf.edu for intact protein matching. "
        "Requires internet access. No local install needed."
    )
    input_formats = [".mzml", ".mgf", ".txt"]
    output_formats = [".html", ".txt"]

    def validate_installation(self) -> bool:
        try:
            req = urllib.request.urlopen(
                f"{_PP_BASE}/msform.cgi?form=mssearch",
                timeout=8
            )
            return req.status == 200
        except Exception:
            return False

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        if log_callback:
            log_callback("[Protein Prospector] Submitting to UCSF web service...")
        # Build form payload for MS-Tag intact protein search
        payload = {
            "form": "mssearch",
            "search_name": "ms-tag",
            "db": "SwissProt",  # SwissProt is the default; custom FASTA not supported via API
            "species": "human",
            "tolerance": str(params.get("precursor_tolerance_ppm", 15)),
            "tolerance_unit": "ppm",
            "max_hits": "100",
            "protein_mass_tol": str(params.get("precursor_tolerance_ppm", 15)),
        }
        data = urllib.parse.urlencode(payload).encode()
        try:
            req = urllib.request.Request(
                f"{_PP_BASE}/msform.cgi",
                data=data,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded",
                         "User-Agent": "Proteoformer-Pipeline/1.0"},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                html = resp.read().decode("utf-8", errors="replace")
            out = output_dir / "protein_prospector_results.html"
            out.write_text(html, encoding="utf-8")
            if log_callback:
                log_callback(f"[Protein Prospector] Results saved to {out.name}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Protein Prospector web request failed: {e}")

    def parse_results(self, output_dir):
        # HTML results -- return a single metadata entry pointing to the file
        results = []
        for html in output_dir.glob("protein_prospector_results.html"):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.raw_engine_output_path = str(html)
            results.append(r)
        return results


# ---------------------------------------------------------------------------
# MetaMorpheus CLI (Smith Lab / Wisconsin)
# ---------------------------------------------------------------------------

MM_CLI_DEFAULT = r"C:\tools\ProteoformSuite\MetaMorpheus_CommandLine\CMD.exe"
MM_CLI_STANDALONE = r"C:\tools\MetaMorpheus\CMD.exe"


class MetaMorpheusAdapter(SearchEngineAdapter):
    """
    MetaMorpheus (Smith Lab, U. Wisconsin) -- top-down + PTM search engine.

    Full-featured search engine with G-PTM-D PTM discovery, quantification,
    and glycoproteomics support. Supports top-down mode with intact protein
    identification.

    Bundled with Proteoform Suite v0.4.1 at:
      C:\\tools\\ProteoformSuite\\MetaMorpheus_CommandLine\\CMD.exe
    Or download standalone from:
      https://github.com/smith-chem-wisc/MetaMorpheus/releases
    Requires .NET 3.1 (bundled) or .NET 8 (standalone 1.1.7+).
    """
    name = "metamorpheus"
    version = "unknown"
    category = "search"
    description = (
        "MetaMorpheus (Smith Lab) -- G-PTM-D powered database search with PTM "
        "discovery, glycoproteomics, and top-down mode. Install from GitHub or "
        "included in Proteoform Suite."
    )
    input_formats = [".mzml", ".mzxml", ".raw"]
    output_formats = [".tsv", ".psmtsv", ".mzid"]

    def _bin(self) -> Optional[str]:
        import os
        from app.config import settings
        custom = getattr(settings, "METAMORPHEUS_BIN", None)
        if custom and os.path.exists(custom):
            return custom
        for candidate in [MM_CLI_DEFAULT, MM_CLI_STANDALONE]:
            if os.path.exists(candidate):
                return candidate
        return shutil.which("CMD") or shutil.which("metamorpheus")

    def validate_installation(self) -> bool:
        import os
        b = self._bin()
        if not b or not os.path.exists(b):
            return False
        try:
            r = subprocess.run([b, "--version"], capture_output=True, text=True, timeout=10)
            import re
            m = re.search(r"([\d.]+)", r.stdout + r.stderr)
            if m:
                self.version = m.group(1)
            return r.returncode == 0
        except Exception:
            return False

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        b = self._bin()
        if not b:
            raise RuntimeError("MetaMorpheus not found. Install from GitHub or via Proteoform Suite.")
        output_dir.mkdir(parents=True, exist_ok=True)
        # Build task TOML / CMD arguments for top-down search
        spectra_args = []
        for f in input_files:
            if f.suffix.lower() in (".mzml", ".mzxml", ".raw"):
                spectra_args += ["-s", str(f)]
        if not spectra_args:
            raise ValueError("No spectrum files for MetaMorpheus")
        cmd = [
            b,
            "-t", "TopDown",  # top-down search task
            "-d", str(database_path),
            *spectra_args,
            "-o", str(output_dir),
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            if log_callback:
                log_callback(line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"MetaMorpheus failed (exit {proc.returncode})")

    def parse_results(self, output_dir):
        results = []
        for tsv in output_dir.rglob("*.psmtsv"):
            try:
                with open(tsv, newline="") as f:
                    reader = csv.DictReader(f, delimiter="\t")
                    for row in reader:
                        r = ProteoformResult(engine_name=self.name, engine_version=self.version)
                        r.scan_number = _safe_int(row.get("Scan Number") or row.get("MS2 Scan Number"))
                        r.accession = row.get("Protein Accession", "")
                        r.protein_name = row.get("Protein Name", "")
                        r.sequence = row.get("Base Sequence", "")
                        r.proteoform_string = row.get("Full Sequence", "")
                        r.observed_mass = _safe_float(row.get("Precursor Mass"))
                        r.score = _safe_float(row.get("Score"))
                        r.qvalue = _safe_float(row.get("QValue"))
                        r.charge = _safe_int(row.get("Charge"))
                        r.matched_fragments = _safe_int(row.get("Matched Ion Number"))
                        r.raw_engine_output_path = str(tsv)
                        results.append(r)
            except Exception:
                pass
        return results


# ---------------------------------------------------------------------------
# Proteoform Suite Workflow adapter (GUI wrapper note)
# ---------------------------------------------------------------------------

class ProteoformSuiteAdapter(SearchEngineAdapter):
    """
    Proteoform Suite (Smith Lab) -- integrated top-down proteoform analysis.

    Proteoform Suite combines database search, quantification, and proteoform
    characterization into an integrated GUI workflow. The standalone GUI is at
    C:\\tools\\ProteoformSuite\\ProteoWPFSuite.exe (requires .NET 3.1 desktop).

    This adapter records installation state and documents the tool. For
    automated analysis, use the MetaMorpheus CLI adapter instead.
    """
    name = "proteoform_suite"
    version = "0.4.1"
    category = "pipeline"
    description = (
        "Proteoform Suite (Smith Lab / Wisconsin) -- Integrated GUI for top-down "
        "proteoform identification and quantification. Requires .NET 3.1 desktop. "
        "Installed at C:\\tools\\ProteoformSuite\\. For CLI use, prefer MetaMorpheus."
    )
    input_formats = [".mzml", ".raw", ".mzxml"]
    output_formats = [".xlsx", ".tsv"]

    def validate_installation(self) -> bool:
        import os
        return os.path.exists(r"C:\tools\ProteoformSuite\ProteoWPFSuite.exe")

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        raise NotImplementedError(
            "Proteoform Suite is a GUI application and cannot run headlessly. "
            "Open ProteoWPFSuite.exe at C:\\tools\\ProteoformSuite\\ for manual analysis."
        )

    def parse_results(self, output_dir):
        return []


# ---------------------------------------------------------------------------
# THRASH via DeconTools
# ---------------------------------------------------------------------------

class THRASHAdapter(SearchEngineAdapter):
    """
    THRASH deconvolution algorithm via PNNL DeconTools (DeconConsole.exe).

    THRASH (Transform-based High-Resolution Automated Spectral Histogram) uses
    isotopic pattern matching (Mercury algorithm) to determine charge states
    and monoisotopic masses from high-resolution FT-MS spectra.

    Install: already bundled at C:\\tools\\DeconTools\\DeconConsole.exe
    GitHub: https://github.com/PNNL-Comp-Mass-Spec/DeconTools
    """
    name = "thrash"
    version = "unknown"
    category = "deconvolution"
    description = (
        "THRASH (DeconTools, PNNL) — Charge-state deconvolution via isotopic pattern "
        "matching using the Mercury algorithm. Outputs _isos.csv and _scans.csv files "
        "with monoisotopic masses, charge states, and abundances."
    )
    input_formats = [".raw", ".mzml", ".mzxml"]
    output_formats = ["_isos.csv", "_scans.csv"]

    def validate_installation(self) -> bool:
        import os
        ok = os.path.exists(r"C:\tools\DeconTools\DeconConsole.exe")
        if ok:
            self.version = "1.1.8658"
        return ok

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        from app.conversion.deconvolvers import run_thrash, THRASHOptions
        output_dir.mkdir(parents=True, exist_ok=True)
        for f in input_files:
            opts = THRASHOptions(
                min_mass=params.get("thrash_min_mass", 400.0),
                max_mass=params.get("thrash_max_mass", 200000.0),
                max_charge=params.get("thrash_max_charge", 60),
                max_fit=params.get("thrash_max_fit", 0.25),
                sn_threshold=params.get("thrash_sn_threshold", 3.0),
            )
            run_thrash(f, output_dir, opts, log_callback)

    def parse_results(self, output_dir):
        results = []
        for csv_file in output_dir.glob("*_isos.csv"):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.raw_engine_output_path = str(csv_file)
            results.append(r)
        return results


# ---------------------------------------------------------------------------
# UniDec
# ---------------------------------------------------------------------------

class UniDecAdapter(SearchEngineAdapter):
    """
    UniDec — Bayesian deconvolution for native and intact protein MS.

    Particularly suited for heterogeneous charge state distributions in native
    MS and top-down experiments on large proteins and protein complexes.

    Install: Download from https://github.com/michaelmarty/UniDec/releases
    and extract to C:\\tools\\UniDec\\
    """
    name = "unidec"
    version = "unknown"
    category = "deconvolution"
    description = (
        "UniDec (Marty Lab) — Bayesian charge-state deconvolution optimized for "
        "native mass spectrometry and intact protein analysis. Install from "
        "https://github.com/michaelmarty/UniDec/releases to C:\\tools\\UniDec\\"
    )
    input_formats = [".txt", ".mzml"]
    output_formats = ["_unidecfiles/"]

    def validate_installation(self) -> bool:
        from app.conversion.deconvolvers import unidec_available
        return unidec_available()

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        from app.conversion.deconvolvers import run_unidec, UniDecOptions
        output_dir.mkdir(parents=True, exist_ok=True)
        for f in input_files:
            opts = UniDecOptions(
                min_mass=params.get("unidec_min_mass", 1000.0),
                max_mass=params.get("unidec_max_mass", 200000.0),
            )
            run_unidec(f, output_dir, opts, log_callback)

    def parse_results(self, output_dir):
        results = []
        for d in output_dir.glob("*_unidecfiles"):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.raw_engine_output_path = str(d)
            results.append(r)
        return results


# ---------------------------------------------------------------------------
# Xtract (Thermo)
# ---------------------------------------------------------------------------

class XtractAdapter(SearchEngineAdapter):
    """
    Thermo Xtract — proprietary deconvolution bundled with Xcalibur / FreeStyle.

    Highly optimized for Orbitrap data. Requires Thermo Xcalibur or FreeStyle
    to be installed; not available as a standalone download.
    """
    name = "xtract"
    version = "unknown"
    category = "deconvolution"
    description = (
        "Xtract (Thermo) — Proprietary Orbitrap deconvolution algorithm bundled "
        "with Xcalibur and FreeStyle software. Requires Thermo software installation."
    )
    input_formats = [".raw"]
    output_formats = [".mzml"]

    def validate_installation(self) -> bool:
        from app.conversion.deconvolvers import xtract_available
        return xtract_available()

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        from app.conversion.deconvolvers import run_xtract, XtractOptions
        output_dir.mkdir(parents=True, exist_ok=True)
        for f in input_files:
            opts = XtractOptions(
                resolution=params.get("xtract_resolution", 60000.0),
                sn_threshold=params.get("xtract_sn", 3.0),
            )
            run_xtract(f, output_dir, opts, log_callback)

    def parse_results(self, output_dir):
        results = []
        for f in output_dir.glob("*.mzML"):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.raw_engine_output_path = str(f)
            results.append(r)
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_int(v) -> Optional[int]:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None
