"""
TopPIC Suite adapters running via Docker (toppicsuite/toppic image).

Runs TopFD (deconvolution) + TopPIC / TopMG (search) inside the official
Docker image, mounting the job work directory as a volume.

Key behaviour: TopFD writes output files into the SAME directory as its
input file (no separate output-dir argument). We hard-link (same drive)
or copy the mzML into the output_dir, run TopFD there, then clean up.

Image: docker pull toppicsuite/toppic
"""
import os
import subprocess
import re
import csv
import shutil
from pathlib import Path
from typing import Any, Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult

DOCKER_IMAGE = "toppicsuite/toppic"


def _docker_path(host_path: Path) -> str:
    """Return a Docker-mountable string for a Windows absolute path.

    Calls .resolve() so that drive-relative paths like Path('/data/uploads')
    (which Python produces from settings.UPLOAD_DIR = '/data/uploads') become
    fully qualified Windows paths like 'F:/data/uploads' that Docker Desktop
    can map correctly.
    """
    return str(host_path.resolve()).replace("\\", "/")



def _run_docker(args: list[str], volumes: dict[str, str], log_callback=None) -> int:
    """Run a command inside the TopPIC Docker container."""
    cmd = ["docker", "run", "--rm"]
    for host, container in volumes.items():
        cmd += ["-v", f"{host}:{container}"]
    cmd += [DOCKER_IMAGE] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if log_callback:
            log_callback(line.rstrip())
    proc.wait()
    return proc.returncode


def _docker_available() -> bool:
    try:
        r = subprocess.run(["docker", "image", "inspect", DOCKER_IMAGE],
                           capture_output=True, timeout=8)
        return r.returncode == 0
    except Exception:
        return False


def _get_version() -> str:
    try:
        r = subprocess.run(
            ["docker", "run", "--rm", DOCKER_IMAGE, "toppic"],
            capture_output=True, text=True, timeout=15
        )
        m = re.search(r"version[:\s]+([\d.]+)", (r.stdout + r.stderr), re.I)
        return m.group(1) if m else "docker"
    except Exception:
        return "docker"


def _run_topfd(mzml: Path, output_dir: Path, params: dict, log_callback=None) -> int:
    """
    Run TopFD inside Docker.

    TopFD writes all output files (msalign, feature) NEXT TO its input file.
    We mount the mzML's parent directory, run TopFD there, then move the
    generated files into output_dir.  Works on exFAT and NTFS alike.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    mzml_dir = mzml.parent
    stem = mzml.stem

    threads = str(params.get("threads", 4))
    rc = _run_docker(
        ["topfd",
         "--thread-number", threads,
         "--skip-html-folder",
         f"/input/{mzml.name}"],
        {_docker_path(mzml_dir): "/input"},
        log_callback,
    )

    # Move TopFD output files out of the uploads dir into the job output dir
    for f in list(mzml_dir.glob(f"{stem}*.msalign")) + \
              list(mzml_dir.glob(f"{stem}*.feature")) + \
              list(mzml_dir.glob(f"{stem}*.csv")):
        try:
            f.rename(output_dir / f.name)
        except Exception:
            pass

    return rc


class TopFDDockerAdapter(SearchEngineAdapter):
    """TopFD via Docker — deconvolves mzML spectra to msalign feature files."""
    name = "topfd"
    version = "unknown"
    category = "deconvolution"
    description = (
        "TopFD standalone (TopPIC Suite, Docker) — Deconvolution only: converts "
        "raw mzML into msalign / feature files without protein database search. "
        "NOTE: TopPIC and TopMG already run TopFD internally — select topfd alone "
        "when you only need deconvolved spectra."
    )
    input_formats = [".mzml", ".mzxml"]
    output_formats = [".msalign", ".feature"]

    def validate_installation(self) -> bool:
        ok = _docker_available()
        if ok:
            self.version = _get_version()
        return ok

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() in (".mzml", ".mzxml")]
        if not mzml_files:
            raise ValueError("No mzML files for TopFD")

        for mzml in mzml_files:
            rc = _run_topfd(mzml, output_dir, params, log_callback)
            if rc != 0:
                raise RuntimeError(f"TopFD failed (exit {rc})")

    def parse_results(self, output_dir):
        results = []
        for f in list(output_dir.glob("*_ms2.msalign")) + list(output_dir.glob("*.feature")):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.source_file = str(f)
            r.raw_engine_output_path = str(f)
            results.append(r)
        return results


class TopPICDockerAdapter(SearchEngineAdapter):
    """TopFD + TopPIC via Docker — full top-down proteoform identification."""
    name = "toppic"
    version = "unknown"
    category = "search"
    description = (
        "TopPIC (TopPIC Suite, Docker) — Runs TopFD deconvolution then "
        "TopPIC database search for proteoform identifications with FDR control. "
        "Runs via official toppicsuite/toppic Docker image."
    )
    input_formats = [".mzml", ".mzxml"]
    output_formats = [".tsv", ".html"]

    def validate_installation(self) -> bool:
        ok = _docker_available()
        if ok:
            self.version = _get_version()
        return ok

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() in (".mzml", ".mzxml")]
        if not mzml_files:
            raise ValueError("No mzML files for TopPIC")

        ppm = str(params.get("precursor_tolerance_ppm", 15))
        max_shift = str(params.get("max_unexpected_mass_shift", 500))
        cutoff = str(params.get("fdr_threshold", 0.01))

        for mzml in mzml_files:
            # Step 1: TopFD deconvolution (writes to output_dir alongside the linked mzML)
            if log_callback:
                log_callback("[TopPIC] Step 1/2: TopFD deconvolution...")
            rc = _run_topfd(mzml, output_dir, params, log_callback)
            if rc != 0:
                raise RuntimeError(f"TopFD failed (exit {rc})")

            # Step 2: TopPIC database search
            ms2_align = output_dir / (mzml.stem + "_ms2.msalign")
            if not ms2_align.exists():
                raise RuntimeError("TopFD produced no ms2.msalign file")

            # Copy fasta into work dir so it's accessible under /work
            work_fasta = output_dir / database_path.name
            if not work_fasta.exists():
                shutil.copy2(database_path, work_fasta)

            if log_callback:
                log_callback("[TopPIC] Step 2/2: TopPIC database search...")
            rc = _run_docker(
                ["toppic",
                 "--thread-number", "4",
                 "--mass-error-tolerance", ppm,
                 "--max-shift", max_shift,
                 "--spectrum-cutoff-type", "FDR",
                 "--spectrum-cutoff-value", cutoff,
                 "--proteoform-cutoff-type", "FDR",
                 "--proteoform-cutoff-value", cutoff,
                 "--decoy",
                 "--skip-html-folder",
                 f"/work/{database_path.name}",
                 f"/work/{ms2_align.name}"],
                {_docker_path(output_dir): "/work"},
                log_callback,
            )
            try:
                work_fasta.unlink()
            except Exception:
                pass
            if rc != 0:
                raise RuntimeError(f"TopPIC search failed (exit {rc})")

    def parse_results(self, output_dir):
        results = []
        for tsv in output_dir.glob("*toppic_proteoform.tsv"):
            results.extend(_parse_toppic_tsv(tsv, self.name, self.version))
        return results


class TopMGDockerAdapter(SearchEngineAdapter):
    """TopFD + TopMG via Docker — proteogenomics / large mass-shift search."""
    name = "topmg"
    version = "unknown"
    category = "search"
    description = (
        "TopMG (TopPIC Suite, Docker) — Like TopPIC but tolerates large unexpected "
        "modifications and supports proteogenomics databases. "
        "Runs via official toppicsuite/toppic Docker image."
    )
    input_formats = [".mzml", ".mzxml"]
    output_formats = [".tsv", ".html"]

    def validate_installation(self) -> bool:
        ok = _docker_available()
        if ok:
            self.version = _get_version()
        return ok

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        output_dir.mkdir(parents=True, exist_ok=True)
        mzml_files = [f for f in input_files if f.suffix.lower() in (".mzml", ".mzxml")]
        if not mzml_files:
            raise ValueError("No mzML files for TopMG")

        for mzml in mzml_files:
            if log_callback:
                log_callback("[TopMG] Step 1/2: TopFD deconvolution...")
            rc = _run_topfd(mzml, output_dir, params, log_callback)
            if rc != 0:
                raise RuntimeError(f"TopFD failed (exit {rc})")

            ms2_align = output_dir / (mzml.stem + "_ms2.msalign")
            if not ms2_align.exists():
                raise RuntimeError("TopFD produced no ms2.msalign file")

            work_fasta = output_dir / database_path.name
            if not work_fasta.exists():
                _link_or_copy(database_path, work_fasta)

            if log_callback:
                log_callback("[TopMG] Step 2/2: TopMG database search...")
            rc = _run_docker(
                ["topmg",
                 "--thread-number", "4",
                 "--skip-html-folder",
                 f"/work/{database_path.name}",
                 f"/work/{ms2_align.name}"],
                {_docker_path(output_dir): "/work"},
                log_callback,
            )
            try:
                work_fasta.unlink()
            except Exception:
                pass
            if rc != 0:
                raise RuntimeError(f"TopMG search failed (exit {rc})")

    def parse_results(self, output_dir):
        results = []
        for tsv in output_dir.glob("*topmg_proteoform.tsv"):
            results.extend(_parse_toppic_tsv(tsv, self.name, self.version))
        return results


class TopDiffDockerAdapter(SearchEngineAdapter):
    """TopDiff via Docker — statistical differential proteoform analysis."""
    name = "topdiff"
    version = "unknown"
    category = "search"
    description = (
        "TopDiff (TopPIC Suite, Docker) — Compares proteoform abundance across "
        "conditions. Requires TopPIC results from multiple samples as input."
    )
    input_formats = [".tsv"]
    output_formats = [".tsv", ".html"]

    def validate_installation(self) -> bool:
        ok = _docker_available()
        if ok:
            self.version = _get_version()
        return ok

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        raise NotImplementedError(
            "TopDiff requires multiple TopPIC result files. "
            "Run TopPIC on at least two samples first, then use TopDiff."
        )

    def parse_results(self, output_dir):
        return []


def _parse_toppic_tsv(tsv_path: Path, engine_name: str, engine_version: str) -> list:
    results = []
    try:
        with open(tsv_path, newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                r = ProteoformResult(engine_name=engine_name, engine_version=engine_version)
                r.spectrum_id = row.get("Prsm ID") or row.get("Spectrum ID")
                r.scan_number = _safe_int(row.get("Scan(s)") or row.get("First scan"))
                r.charge = _safe_int(row.get("Charge"))
                r.precursor_mz = _safe_float(row.get("Precursor mass"))
                r.observed_mass = _safe_float(row.get("Adjusted precursor mass"))
                r.theoretical_mass = _safe_float(row.get("Proteoform mass"))
                r.accession = row.get("Protein accession", "")
                r.protein_name = row.get("Protein description", "")
                r.sequence = row.get("First residue", "")
                r.proteoform_string = row.get("Proteoform", "")
                r.evalue = _safe_float(row.get("E-value") or row.get("Spectrum-level E-value"))
                r.qvalue = _safe_float(row.get("FDR") or row.get("Spectrum-level FDR"))
                r.matched_fragments = _safe_int(row.get("Matched fragment number"))
                r.raw_engine_output_path = str(tsv_path)
                results.append(r)
    except Exception:
        pass
    return results


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
