"""
Adapters for NRTDP (National Resource for Translational and Developmental Proteomics)
and topdownproteomics GitHub organization tools.

Tools:
  modformPro         - Python CLI; protein modification site/region estimation
  TDCD_FDR_Calculator - .NET CLI; context-dependent FDR post-processing
  tdReport-to-mzIdentML - .NET CLI; TDPortal .tdReport → mzIdentML format conversion
"""
import os
import csv
import subprocess
import shutil
from pathlib import Path
from typing import Optional

from app.engines.base import SearchEngineAdapter, ProteoformResult

# ── Binary / tool locations ───────────────────────────────────────────────────

MODFORMPRO_DIR = Path(r"C:\tools\modformPro\src")
MODFORMPRO_MAIN = MODFORMPRO_DIR / "main.py"

TDCD_DLL = Path(
    r"C:\tools\TDCD_FDR_Calculator\src\TDCD_FDR_Calculator"
    r"\bin\Release\netcoreapp2.0\TDCD_FDR_Calculator.dll"
)
TDCD_DLL_FALLBACK = Path(
    r"C:\tools\TDCD_FDR_Calculator\src\TDCD_FDR_Calculator"
    r"\bin\Debug\netcoreapp2.0\TDCD_FDR_Calculator.dll"
)

TDREPORT_DLL = Path(
    r"C:\tools\tdReport-to-mzIdentML\src\NRTDP.ReportConverter.ConsoleApp"
    r"\bin\Release\net5.0\NRTDP.tdReportConverter.ConsoleApp.dll"
)
TDREPORT_DLL_FALLBACK = Path(
    r"C:\tools\tdReport-to-mzIdentML\src\NRTDP.ReportConverter.ConsoleApp"
    r"\bin\Debug\net5.0\NRTDP.tdReportConverter.ConsoleApp.dll"
)


def _find_dll(*paths: Path) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None


# ── modformPro ────────────────────────────────────────────────────────────────

class ModformProAdapter(SearchEngineAdapter):
    """
    modformPro (NRTDP) — Estimates high-dimensional modform regions for proteins
    with multiple modification types and sites from mass-spectrometry data.

    Uses linear programming to determine which combinations of modifications
    are consistent with observed mass measurements.

    Source: https://github.com/NRTDP/modformPro
    Installed at: C:\\tools\\modformPro\\
    """
    name = "modformpro"
    version = "unknown"
    category = "search"
    description = (
        "modformPro (NRTDP) — Estimates protein modification regions from MS data. "
        "Uses linear programming to identify feasible sets of proteoforms consistent "
        "with observed intact mass measurements. Accepts a specifications file (.txt) "
        "describing protein mass, modification masses, and observed abundances."
    )
    input_formats = [".txt"]
    output_formats = [".txt", ".csv"]

    def validate_installation(self) -> bool:
        if not MODFORMPRO_MAIN.exists():
            return False
        try:
            r = subprocess.run(
                ["python", str(MODFORMPRO_MAIN), "--help"],
                capture_output=True, text=True, timeout=8, cwd=str(MODFORMPRO_DIR),
            )
            self.version = "git"
            return True
        except Exception:
            return False

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        """
        input_files should contain a modformPro specifications .txt file.
        The spec file format is documented at https://nrtdp.github.io/modformPro/
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        spec_files = [f for f in input_files if f.suffix.lower() == ".txt"]
        if not spec_files:
            raise ValueError(
                "modformPro requires a specifications .txt file as input. "
                "See https://nrtdp.github.io/modformPro/ for the format."
            )

        for spec_file in spec_files:
            cmd = ["python", str(MODFORMPRO_MAIN), "-f", str(spec_file)]
            if log_callback:
                log_callback(f"[modformPro] Running: {' '.join(cmd)}")
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, cwd=str(MODFORMPRO_DIR),
            )
            for line in proc.stdout:
                if log_callback:
                    log_callback(line.rstrip())
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"modformPro failed (exit {proc.returncode})")

    def parse_results(self, output_dir) -> list:
        results = []
        for f in list(output_dir.glob("*.txt")) + list(output_dir.glob("*.csv")):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.raw_engine_output_path = str(f)
            results.append(r)
        return results


def modformpro_available() -> bool:
    return MODFORMPRO_MAIN.exists()


# ── TDCD_FDR_Calculator ───────────────────────────────────────────────────────

class TDCDFDRAdapter(SearchEngineAdapter):
    """
    TDCD_FDR_Calculator (NRTDP) — Context-dependent FDR post-processing for
    top-down proteomics search results.

    Accepts forward-search and decoy-search CSV files (score column), outputs
    enhanced q-values using context-dependent calibration. Can be applied to
    results from any search engine (TopPIC, MSPathFinderT, etc.).

    Source: https://github.com/NRTDP/TDCD_FDR_Calculator
    Input CSV format: col1=label, col2=score (higher is better, ascending sort)
    Output: same as forward file + 'non-parametric q-value' and 'Enhanced q-value'

    Build: cd C:\\tools\\TDCD_FDR_Calculator\\src\\TDCD_FDR_Calculator && dotnet build -c Release
    """
    name = "tdcd_fdr"
    version = "unknown"
    category = "search"
    description = (
        "TDCD_FDR_Calculator (NRTDP) — Context-dependent FDR post-processing that "
        "enhances q-values from any top-down search engine. Input: forward + decoy CSVs "
        "with a score column. Output: original results with added enhanced q-value column. "
        "Build with: cd C:\\tools\\TDCD_FDR_Calculator\\src\\TDCD_FDR_Calculator && dotnet build -c Release"
    )
    input_formats = [".csv"]
    output_formats = [".csv"]

    def validate_installation(self) -> bool:
        dll = _find_dll(TDCD_DLL, TDCD_DLL_FALLBACK)
        if dll:
            self.version = "git"
        return dll is not None

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        """
        Expects exactly 2 CSV files: forward (targets) and decoy.
        Alternatively, params may specify 'forward_csv' and 'decoy_csv' paths.
        """
        dll = _find_dll(TDCD_DLL, TDCD_DLL_FALLBACK)
        if not dll:
            raise RuntimeError(
                "TDCD_FDR_Calculator not built. Run: "
                "cd C:\\tools\\TDCD_FDR_Calculator\\src\\TDCD_FDR_Calculator && dotnet build -c Release"
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        csvs = [f for f in input_files if f.suffix.lower() == ".csv"]
        if len(csvs) < 2:
            raise ValueError(
                "TDCD_FDR_Calculator requires 2 CSV files: forward (targets) and decoy. "
                "First file = forward, second = decoy."
            )

        forward_csv = csvs[0]
        decoy_csv = csvs[1]
        output_csv = output_dir / f"{forward_csv.stem}_enhanced_fdr.csv"

        cmd = ["dotnet", str(dll), str(forward_csv), str(decoy_csv), str(output_csv)]
        if log_callback:
            log_callback(f"[TDCD_FDR] Running: {' '.join(cmd)}")

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        for line in proc.stdout:
            if log_callback:
                log_callback(line.rstrip())
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError(f"TDCD_FDR_Calculator failed (exit {proc.returncode})")

    def parse_results(self, output_dir) -> list:
        results = []
        for f in output_dir.glob("*_enhanced_fdr.csv"):
            try:
                with open(f, newline="", encoding="utf-8", errors="replace") as fh:
                    reader = csv.DictReader(fh)
                    for row in reader:
                        r = ProteoformResult(
                            engine_name=self.name, engine_version=self.version,
                        )
                        r.raw_engine_output_path = str(f)
                        # Enhanced q-value column
                        enhanced_q = row.get("Enhanced q-value") or row.get("enhanced q-value")
                        if enhanced_q:
                            try:
                                r.qvalue = float(enhanced_q)
                            except ValueError:
                                pass
                        label = row.get(list(row.keys())[0], "")
                        r.spectrum_id = label
                        results.append(r)
            except Exception:
                pass
        return results


def tdcd_fdr_available() -> bool:
    return _find_dll(TDCD_DLL, TDCD_DLL_FALLBACK) is not None


# ── tdReport-to-mzIdentML ────────────────────────────────────────────────────

class TdReportConverterAdapter(SearchEngineAdapter):
    """
    tdReport-to-mzIdentML (NRTDP) — Converts TDPortal .tdReport files (SQLite)
    to standard mzIdentML format for downstream use with third-party tools.

    Source: https://github.com/NRTDP/tdReport-to-mzIdentML
    Build: cd C:\\tools\\tdReport-to-mzIdentML\\src\\NRTDP.ReportConverter.ConsoleApp && dotnet build -c Release
    """
    name = "tdreport_converter"
    version = "1.0.1"
    category = "pipeline"
    description = (
        "tdReport → mzIdentML converter (NRTDP) — Converts TDPortal .tdReport "
        "SQLite files into standard mzIdentML format. Enables use of TDPortal "
        "search results with any tool that accepts mzIdentML. "
        "Build with: cd C:\\tools\\tdReport-to-mzIdentML\\src\\NRTDP.ReportConverter.ConsoleApp && dotnet build -c Release"
    )
    input_formats = [".tdReport"]
    output_formats = [".mzid"]

    def validate_installation(self) -> bool:
        dll = _find_dll(TDREPORT_DLL, TDREPORT_DLL_FALLBACK)
        return dll is not None

    def prepare_database(self, fasta_path, ptm_config, output_dir):
        return fasta_path

    def run_search(self, input_files, database_path, params, output_dir, log_callback=None):
        dll = _find_dll(TDREPORT_DLL, TDREPORT_DLL_FALLBACK)
        if not dll:
            raise RuntimeError(
                "tdReport converter not built. Run: "
                "cd C:\\tools\\tdReport-to-mzIdentML\\src\\NRTDP.ReportConverter.ConsoleApp && dotnet build -c Release"
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        tdreports = [f for f in input_files if f.suffix.lower() == ".tdreport"]
        if not tdreports:
            raise ValueError("No .tdReport files found in input")

        for td in tdreports:
            out_mzid = output_dir / (td.stem + ".mzid")
            cmd = ["dotnet", str(dll), str(td), str(out_mzid)]
            if log_callback:
                log_callback(f"[tdReport→mzIdentML] {' '.join(cmd)}")
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            for line in proc.stdout:
                if log_callback:
                    log_callback(line.rstrip())
            proc.wait()
            if proc.returncode != 0:
                raise RuntimeError(f"tdReport converter failed (exit {proc.returncode})")

    def parse_results(self, output_dir) -> list:
        results = []
        for f in output_dir.glob("*.mzid"):
            r = ProteoformResult(engine_name=self.name, engine_version=self.version)
            r.raw_engine_output_path = str(f)
            results.append(r)
        return results


def tdreport_converter_available() -> bool:
    return _find_dll(TDREPORT_DLL, TDREPORT_DLL_FALLBACK) is not None
