"""
File conversion module — converts vendor instrument files to open formats.

Primary converter: msconvert (ProteoWizard) bundled with OpenMS 3.5.0
Supplemental:      ThermoRawFileParser (for Thermo .raw via .NET 8)
                   OpenMS FileConverter (for format bridging)
"""
import os
import re
import subprocess
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

MSCONVERT_BIN = r"C:\Program Files\OpenMS-3.5.0\share\OpenMS\THIRDPARTY\pwiz-bin\msconvert.exe"
THERMOPARSER_DLL = r"C:\tools\ThermoRawFileParser\ThermoRawFileParser.dll"
OPENMS_FC_BIN = r"C:\Program Files\OpenMS-3.5.0\bin\FileConverter.exe"


# ---------------------------------------------------------------------------
# Option dataclass
# ---------------------------------------------------------------------------

@dataclass
class ConversionOptions:
    """All msconvert options mapped to Python fields."""

    # --- Output format ---
    output_format: str = "mzML"           # mzML | mzXML | mgf | ms2 | mz5

    # --- Binary encoding ---
    mz_precision: int = 64               # 32 | 64
    intensity_precision: int = 32        # 32 | 64

    # --- Compression ---
    zlib: bool = False
    numpress_linear: bool = False        # m/z + RT compression
    numpress_slof: bool = False          # intensity compression
    numpress_pic: bool = False           # positive-integer intensity
    gzip_output: bool = False

    # --- Index / metadata ---
    write_index: bool = True
    sim_as_spectra: bool = False         # SIM as spectra not chromatograms
    srm_as_spectra: bool = False
    combine_ion_mobility: bool = False
    ignore_unknown_instrument: bool = False
    strip_location: bool = False
    strip_version: bool = False
    single_threaded: bool = False

    # --- Filters (applied in order) ---

    # Peak picking — MUST be first filter when using vendor
    peak_picking: str = "none"           # none | vendor | cwt
    peak_picking_ms_levels: str = "1-"  # int_set, e.g. "1-" or "1-2"
    peak_picking_snr: Optional[float] = None
    peak_picking_spacing: Optional[float] = None

    # MS-level selection
    ms_levels: Optional[str] = None     # int_set e.g. "1-2" or "2"

    # Scan range filters
    scan_number_range: Optional[str] = None  # e.g. "1-5000"
    scan_time_range: Optional[str] = None    # seconds, e.g. "[0,3600]"

    # m/z window
    mz_window: Optional[str] = None     # e.g. "[100,2000]"

    # Intensity threshold
    threshold_type: Optional[str] = None       # absolute|bpi-relative|tic-relative|count
    threshold_value: Optional[float] = None
    threshold_orientation: str = "most-intense"
    threshold_ms_levels: Optional[str] = None

    # Zero samples
    zero_samples: Optional[str] = None  # removeExtra | addMissing | addMissing=5

    # Charge state predictor
    charge_state_predictor: bool = False
    charge_predictor_override: bool = False
    charge_predictor_min: int = 2
    charge_predictor_max: int = 3

    # ETD filter
    etd_filter: bool = False
    etd_remove_precursor: bool = True
    etd_remove_charge_reduced: bool = True
    etd_remove_neutral_loss: bool = True
    etd_blanket_removal: bool = True

    # Precursor
    precursor_recalculation: bool = False
    precursor_refine: bool = False

    # Metadata
    metadata_fixer: bool = False
    sort_by_scan_time: bool = False

    # MS2 cleanup
    ms2_denoise: bool = False
    ms2_denoise_peaks: int = 6
    ms2_denoise_window: float = 30.0
    ms2_deisotope: bool = False

    # Activation / polarity / analyzer
    activation_type: Optional[str] = None  # ETD|CID|HCD|ECD|...
    polarity: Optional[str] = None         # positive|negative
    analyzer: Optional[str] = None         # quad|orbi|FT|IT|TOF

    # Default array length (remove empty spectra)
    min_peaks: Optional[int] = None

    # Scan summing (Waters PASEF)
    scan_summing: bool = False

    # Verbose
    verbose: bool = True


def build_msconvert_cmd(
    input_file: Path,
    output_dir: Path,
    opts: ConversionOptions,
    output_filename: Optional[str] = None,
) -> list[str]:
    """Build the msconvert command line from ConversionOptions."""
    cmd = [MSCONVERT_BIN, str(input_file)]

    # Output
    cmd += ["-o", str(output_dir)]
    if output_filename:
        cmd += ["--outfile", output_filename]

    # Format
    fmt_map = {
        "mzML": "--mzML", "mzXML": "--mzXML", "mgf": "--mgf",
        "ms2": "--ms2", "mz5": "--mz5", "cms2": "--cms2",
    }
    cmd.append(fmt_map.get(opts.output_format, "--mzML"))

    # Precision
    if opts.mz_precision == 32:
        cmd.append("--mz32")
    if opts.intensity_precision == 64:
        cmd.append("--inten64")

    # Compression
    if opts.zlib:
        cmd.append("--zlib")
    if opts.numpress_linear:
        cmd.append("--numpressLinear")
    if opts.numpress_slof:
        cmd.append("--numpressSlof")
    if opts.numpress_pic:
        cmd.append("--numpressPic")
    if opts.gzip_output:
        cmd.append("--gzip")

    # Index / metadata
    if not opts.write_index:
        cmd.append("--noindex")
    if opts.sim_as_spectra:
        cmd.append("--simAsSpectra")
    if opts.srm_as_spectra:
        cmd.append("--srmAsSpectra")
    if opts.combine_ion_mobility:
        cmd.append("--combineIonMobilitySpectra")
    if opts.ignore_unknown_instrument:
        cmd.append("--ignoreUnknownInstrumentError")
    if opts.strip_location:
        cmd.append("--stripLocationFromSourceFiles")
    if opts.strip_version:
        cmd.append("--stripVersionFromSoftware")
    if opts.single_threaded:
        cmd.append("--singleThreaded")
    if opts.verbose:
        cmd.append("-v")

    # --- Filters (order matters!) ---
    # 1. Peak picking FIRST if vendor
    if opts.peak_picking != "none":
        parts = [opts.peak_picking]
        if opts.peak_picking_snr is not None:
            parts.append(f"snr={opts.peak_picking_snr}")
        if opts.peak_picking_spacing is not None:
            parts.append(f"peakSpace={opts.peak_picking_spacing}")
        if opts.peak_picking_ms_levels:
            parts.append(f"msLevel={opts.peak_picking_ms_levels}")
        cmd += ["--filter", f"peakPicking {' '.join(parts)}"]

    # 2. MS-level
    if opts.ms_levels:
        cmd += ["--filter", f"msLevel {opts.ms_levels}"]

    # 3. Scan number range
    if opts.scan_number_range:
        cmd += ["--filter", f"scanNumber {opts.scan_number_range}"]

    # 4. Scan time range
    if opts.scan_time_range:
        cmd += ["--filter", f"scanTime {opts.scan_time_range}"]

    # 5. m/z window
    if opts.mz_window:
        cmd += ["--filter", f"mzWindow {opts.mz_window}"]

    # 6. Intensity threshold
    if opts.threshold_type and opts.threshold_value is not None:
        thr = f"threshold {opts.threshold_type} {opts.threshold_value} {opts.threshold_orientation}"
        if opts.threshold_ms_levels:
            thr += f" {opts.threshold_ms_levels}"
        cmd += ["--filter", thr]

    # 7. Zero samples
    if opts.zero_samples:
        cmd += ["--filter", f"zeroSamples {opts.zero_samples}"]

    # 8. ETD filter
    if opts.etd_filter:
        cmd += ["--filter",
                f"ETDFilter {str(opts.etd_remove_precursor).lower()} "
                f"{str(opts.etd_remove_charge_reduced).lower()} "
                f"{str(opts.etd_remove_neutral_loss).lower()} "
                f"{str(opts.etd_blanket_removal).lower()}"]

    # 9. Charge state predictor
    if opts.charge_state_predictor:
        cmd += ["--filter",
                f"chargeStatePredictor overrideExistingCharge={str(opts.charge_predictor_override).lower()} "
                f"minMultipleCharge={opts.charge_predictor_min} "
                f"maxMultipleCharge={opts.charge_predictor_max}"]

    # 10. Precursor operations
    if opts.precursor_recalculation:
        cmd += ["--filter", "precursorRecalculation"]
    if opts.precursor_refine:
        cmd += ["--filter", "precursorRefine"]

    # 11. Metadata / sorting
    if opts.metadata_fixer:
        cmd += ["--filter", "metadataFixer"]
    if opts.sort_by_scan_time:
        cmd += ["--filter", "sortByScanTime"]

    # 12. MS2 processing
    if opts.ms2_denoise:
        cmd += ["--filter",
                f"MS2Denoise {opts.ms2_denoise_peaks} {opts.ms2_denoise_window}"]
    if opts.ms2_deisotope:
        cmd += ["--filter", "MS2Deisotope"]

    # 13. Activation / polarity / analyzer
    if opts.activation_type:
        cmd += ["--filter", f"activation {opts.activation_type}"]
    if opts.polarity:
        cmd += ["--filter", f"polarity {opts.polarity}"]
    if opts.analyzer:
        cmd += ["--filter", f"analyzer {opts.analyzer}"]

    # 14. Remove empty spectra
    if opts.min_peaks is not None:
        cmd += ["--filter", f"defaultArrayLength {opts.min_peaks}-"]

    # 15. Scan summing
    if opts.scan_summing:
        cmd += ["--filter", "scanSumming"]

    return cmd


def run_msconvert(
    input_file: Path,
    output_dir: Path,
    opts: ConversionOptions,
    log_callback=None,
) -> Path:
    """Run msconvert and return the output file path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = build_msconvert_cmd(input_file, output_dir, opts)
    if log_callback:
        log_callback(f"[msconvert] Command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if log_callback:
            log_callback(line.rstrip())
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"msconvert failed (exit {proc.returncode})")

    # Find output file
    stem = input_file.stem
    ext_map = {"mzML": ".mzML", "mzXML": ".mzXML", "mgf": ".mgf",
               "ms2": ".ms2", "mz5": ".mz5", "cms2": ".cms2"}
    ext = ext_map.get(opts.output_format, ".mzML")
    out = output_dir / (stem + ext)
    if opts.gzip_output:
        out = Path(str(out) + ".gz")
    if not out.exists():
        # Fallback: find any new file
        candidates = sorted(output_dir.glob(f"{stem}*"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            out = candidates[0]
    return out


def msconvert_available() -> bool:
    return os.path.exists(MSCONVERT_BIN)


def msconvert_version() -> str:
    try:
        r = subprocess.run([MSCONVERT_BIN], capture_output=True, text=True, timeout=5)
        m = re.search(r"ProteoWizard release:\s*([\d.]+)", r.stdout + r.stderr)
        return f"ProteoWizard {m.group(1)}" if m else "bundled"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# ThermoRawFileParser
# ---------------------------------------------------------------------------

def run_thermoparser(
    input_file: Path,
    output_dir: Path,
    output_format: str = "mzML",
    log_callback=None,
) -> Path:
    """
    Convert Thermo .raw files using ThermoRawFileParser.
    Format codes: 0=MGF, 1=mzML, 2=mzXML, 3=parquet
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    fmt_code = {"mgf": "0", "mzML": "1", "mzXML": "2", "parquet": "3"}.get(output_format, "1")
    cmd = [
        "dotnet", THERMOPARSER_DLL,
        "-i", str(input_file),
        "-o", str(output_dir),
        "-f", fmt_code,
        "-l", "1",  # log level info
    ]
    if log_callback:
        log_callback(f"[ThermoRawFileParser] Command: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if log_callback:
            log_callback(line.rstrip())
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ThermoRawFileParser failed (exit {proc.returncode})")
    ext = {"mgf": ".mgf", "mzML": ".mzML", "mzXML": ".mzXML", "parquet": ".parquet"}.get(output_format, ".mzML")
    out = output_dir / (input_file.stem + ext)
    return out


def thermoparser_available() -> bool:
    return os.path.exists(THERMOPARSER_DLL)


# ---------------------------------------------------------------------------
# OpenMS FileConverter
# ---------------------------------------------------------------------------

def run_openms_convert(
    input_file: Path,
    output_file: Path,
    log_callback=None,
) -> Path:
    """Use OpenMS FileConverter for simple format bridging."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    cmd = [OPENMS_FC_BIN, "-in", str(input_file), "-out", str(output_file)]
    if log_callback:
        log_callback(f"[OpenMS FileConverter] {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if log_callback:
            log_callback(line.rstrip())
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"OpenMS FileConverter failed (exit {proc.returncode})")
    return output_file


def openms_converter_available() -> bool:
    return os.path.exists(OPENMS_FC_BIN)
