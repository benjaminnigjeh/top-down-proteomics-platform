"""
Deconvolution engine adapters.

THRASH  - via DeconTools (PNNL; DeconConsole.exe)
UniDec  - via UniDec standalone application
Xtract  - via Thermo Xtract (requires Xcalibur / FreeStyle)
"""
import os
import subprocess
import json
import shutil
import tempfile
import configparser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Callable

# Binary locations
DECONTOOLS_BIN = r"C:\tools\DeconTools\DeconConsole.exe"
UNIDEC_BIN_PATHS = [
    r"C:\tools\UniDec\UniDec.exe",
    r"C:\Program Files\UniDec\UniDec.exe",
]
XTRACT_BIN_PATHS = [
    r"C:\tools\Xtract\Xtract.exe",
    r"C:\Program Files\Thermo\Xcalibur\Xtract.exe",
]


# ---------------------------------------------------------------------------
# THRASH via DeconTools (DeconConsole.exe)
# ---------------------------------------------------------------------------

@dataclass
class THRASHOptions:
    """Options for the THRASH deconvolution algorithm via DeconTools."""

    # Mass range
    min_mass: float = 400.0
    max_mass: float = 200000.0

    # m/z range (0 = no limit)
    min_mz: float = 0.0
    max_mz: float = 0.0

    # Charge state range
    min_charge: int = 1
    max_charge: int = 60

    # THRASH parameters
    max_fit: float = 0.25          # maximum isotopic fit score (lower = tighter)
    use_charge_carrier: bool = True
    charge_carrier: str = "H"      # H, Na, K, NH4 etc.
    use_mercury: bool = True       # use Mercury algorithm for isotope fitting
    use_average_mass: bool = False  # report average vs monoisotopic mass

    # Signal/noise
    sn_threshold: float = 3.0
    background_ratio: float = 5.0

    # MS level filter
    ms_levels: str = "1-"         # process all MS levels by default

    # Peak detection
    peak_detection_type: str = "Centroid"  # Centroid | Apex | ZN
    peak_bkg_ratio: float = 5.0
    min_peak_intensity: float = 0.0

    # Scan selection
    scan_min: int = 0
    scan_max: int = 0  # 0 = all scans

    # Output
    save_lc_ms_features: bool = True
    result_type: str = "PeakBased"  # PeakBased | ScanBased


def run_thrash(
    input_file: Path,
    output_dir: Path,
    opts: THRASHOptions,
    log_callback: Optional[Callable] = None,
) -> Path:
    """Run THRASH deconvolution via DeconConsole.exe."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write DeconTools parameter file (INI format)
    params_file = output_dir / f"{input_file.stem}_decon_params.xml"
    _write_decontools_params(params_file, opts)

    output_file = output_dir / (input_file.stem + "_isos.csv")

    cmd = [
        DECONTOOLS_BIN,
        str(input_file),
        str(output_dir),
        str(params_file),
    ]

    if log_callback:
        log_callback(f"[THRASH/DeconTools] Command: {' '.join(cmd)}")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if log_callback:
            log_callback(line.rstrip())
    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"DeconConsole/THRASH failed (exit {proc.returncode})")

    if not output_file.exists():
        # Search for any generated file
        candidates = list(output_dir.glob(f"{input_file.stem}*_isos*"))
        if candidates:
            output_file = candidates[0]

    return output_file


def _write_decontools_params(params_file: Path, opts: THRASHOptions):
    """Write a DeconTools XML parameter file."""
    params_file.write_text(
        f"""<?xml version="1.0" encoding="utf-8"?>
<parameters>
  <MiscMSParameters>
    <MinMZ>{opts.min_mz}</MinMZ>
    <MaxMZ>{opts.max_mz if opts.max_mz > 0 else 100000}</MaxMZ>
    <MinScan>{opts.scan_min}</MinScan>
    <MaxScan>{opts.scan_max if opts.scan_max > 0 else 100000}</MaxScan>
    <SumSpectra>false</SumSpectra>
    <SumSpectraAcrossScanRange>false</SumSpectraAcrossScanRange>
    <NumScansToSumOver>1</NumScansToSumOver>
    <NumScansToAdvance>1</NumScansToAdvance>
    <ProcessMSMS>false</ProcessMSMS>
    <MSMSProcessingMode>Full</MSMSProcessingMode>
    <MS1>true</MS1>
    <MS2>false</MS2>
    <MS3>false</MS3>
  </MiscMSParameters>
  <PeakParameters>
    <PeakBackgroundRatio>{opts.peak_bkg_ratio}</PeakBackgroundRatio>
    <SignalToNoiseThreshold>{opts.sn_threshold}</SignalToNoiseThreshold>
  </PeakParameters>
  <HornTransformParameters>
    <MaxCharge>{opts.max_charge}</MaxCharge>
    <MaxMass>{opts.max_mass}</MaxMass>
    <MinMass>{opts.min_mass}</MinMass>
    <MaxFit>{opts.max_fit}</MaxFit>
    <UseMercury>{"true" if opts.use_mercury else "false"}</UseMercury>
    <UseRapidDeconvolution>false</UseRapidDeconvolution>
    <CheckAllPatternsAgainstCharge1>true</CheckAllPatternsAgainstCharge1>
    <LeftFitStringencyFactor>1</LeftFitStringencyFactor>
    <RightFitStringencyFactor>1</RightFitStringencyFactor>
    <UseIsotopicDistributionCalculator>false</UseIsotopicDistributionCalculator>
    <DeleteIntensityThreshold>10</DeleteIntensityThreshold>
    <MinIntensityForScore>0</MinIntensityForScore>
    <NumPeaksForShoulder>1</NumPeaksForShoulder>
    <DebugHornTransform>false</DebugHornTransform>
    <MaxMercury>300</MaxMercury>
    <CCMass>1.00727638</CCMass>
    <ChargeCarrierMass>1.00727638</ChargeCarrierMass>
    <IsotopeFitType>Mercrucy</IsotopeFitType>
  </HornTransformParameters>
  <Filters>
    <IntensityThreshold>{opts.min_peak_intensity}</IntensityThreshold>
  </Filters>
  <WriterParameters>
    <OutputFilePath></OutputFilePath>
    <WriteDeconvolutedPeaks>true</WriteDeconvolutedPeaks>
    <WriteRawData>false</WriteRawData>
    <WriteScanData>true</WriteScanData>
    <OutputType>CSV</OutputType>
    <SaveLCMSFeatures>{"true" if opts.save_lc_ms_features else "false"}</SaveLCMSFeatures>
  </WriterParameters>
</parameters>
""",
        encoding="utf-8",
    )


def thrash_available() -> bool:
    return os.path.exists(DECONTOOLS_BIN)


def thrash_version() -> str:
    try:
        r = subprocess.run([DECONTOOLS_BIN], capture_output=True, text=True, timeout=5)
        for line in (r.stdout + r.stderr).splitlines():
            if "version" in line.lower():
                return line.strip()
        return "DeconTools"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# UniDec deconvolution
# ---------------------------------------------------------------------------

@dataclass
class UniDecOptions:
    """Options for UniDec deconvolution."""

    # Mass range
    min_mass: float = 1000.0
    max_mass: float = 200000.0

    # m/z range
    min_mz: float = 200.0
    max_mz: float = 8000.0

    # Charge range
    min_charge: int = 1
    max_charge: int = 50

    # Resolution / sampling
    mass_bin_size: float = 10.0    # Da per bin (lower = higher resolution)
    mz_bin_size: float = 0.5       # m/z bin size

    # Noise handling
    peak_detection_range: float = 50.0   # range in m/z for peak detection
    peak_detection_threshold: float = 0.01   # fraction of max intensity

    # Smoothing
    smooth_width: float = 1.0       # Gaussian smoothing width (m/z)

    # Charge smooth
    charge_smooth: float = 1.0

    # Score threshold
    score_threshold: float = 0.0

    # Output
    export_mass_list: bool = True
    export_mz_peaks: bool = True


def run_unidec(
    input_file: Path,
    output_dir: Path,
    opts: UniDecOptions,
    log_callback: Optional[Callable] = None,
) -> Path:
    """
    Run UniDec deconvolution in command-line mode.
    UniDec supports batch mode via a config file.
    """
    unidec_bin = _find_binary(UNIDEC_BIN_PATHS)
    if not unidec_bin:
        raise RuntimeError(
            "UniDec not found. Download from https://github.com/michaelmarty/UniDec/releases "
            "and install to C:\\tools\\UniDec\\"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    # Write UniDec config
    config_file = output_dir / "unidec_config.txt"
    _write_unidec_config(config_file, opts, input_file)

    cmd = [unidec_bin, "-f", str(config_file), str(input_file)]
    if log_callback:
        log_callback(f"[UniDec] Command: {' '.join(cmd)}")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            cwd=str(output_dir))
    for line in proc.stdout:
        if log_callback:
            log_callback(line.rstrip())
    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"UniDec failed (exit {proc.returncode})")

    # UniDec outputs to the same directory as input, named <stem>_unidecfiles/
    out = output_dir / (input_file.stem + "_unidecfiles")
    return out if out.exists() else output_dir


def _write_unidec_config(config_file: Path, opts: UniDecOptions, input_file: Path):
    config_file.write_text(
        f"minmz {opts.min_mz}\n"
        f"maxmz {opts.max_mz}\n"
        f"minz {opts.min_charge}\n"
        f"maxz {opts.max_charge}\n"
        f"mzbins {opts.mz_bin_size}\n"
        f"masslb {opts.min_mass}\n"
        f"massub {opts.max_mass}\n"
        f"massbins {opts.mass_bin_size}\n"
        f"smfwhm {opts.smooth_width}\n"
        f"zzsig {opts.charge_smooth}\n"
        f"peakwindow {opts.peak_detection_range}\n"
        f"peakthresh {opts.peak_detection_threshold}\n"
        f"rawflag 0\n"
        f"aggressiveflag 0\n"
    )


def unidec_available() -> bool:
    return _find_binary(UNIDEC_BIN_PATHS) is not None


def unidec_version() -> str:
    exe = _find_binary(UNIDEC_BIN_PATHS)
    if not exe:
        return "unknown"
    try:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5)
        return (r.stdout + r.stderr).strip().split("\n")[0] or "UniDec"
    except Exception:
        return "UniDec"


# ---------------------------------------------------------------------------
# Xtract (Thermo) deconvolution
# ---------------------------------------------------------------------------

@dataclass
class XtractOptions:
    """Options for Thermo Xtract deconvolution."""

    # Mass range
    min_mass: float = 400.0
    max_mass: float = 100000.0

    # Resolution
    resolution: float = 60000.0    # instrument resolution at 400 m/z

    # Signal-to-noise
    sn_threshold: float = 3.0

    # Fit factor
    fit_factor: float = 44.0       # minimum fit (percentage)

    # Remainder threshold
    remainder: float = 25.0        # percentage of isotope envelope

    # Output
    output_format: str = "mzML"    # mzML | txt


def run_xtract(
    input_file: Path,
    output_dir: Path,
    opts: XtractOptions,
    log_callback: Optional[Callable] = None,
) -> Path:
    """Run Thermo Xtract deconvolution."""
    xtract_bin = _find_binary(XTRACT_BIN_PATHS)
    if not xtract_bin:
        raise RuntimeError(
            "Thermo Xtract not found. Xtract is bundled with Thermo Xcalibur or FreeStyle. "
            "Install Xcalibur/FreeStyle and ensure Xtract.exe is in a known location."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / (input_file.stem + "_xtract.mzML")

    cmd = [
        xtract_bin,
        str(input_file),
        f"/output:{str(output_dir)}",
        f"/low:{opts.min_mass}",
        f"/high:{opts.max_mass}",
        f"/res:{opts.resolution}",
        f"/sn:{opts.sn_threshold}",
        f"/fit:{opts.fit_factor}",
        f"/rem:{opts.remainder}",
    ]

    if log_callback:
        log_callback(f"[Xtract] Command: {' '.join(cmd)}")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        if log_callback:
            log_callback(line.rstrip())
    proc.wait()

    if proc.returncode not in (0, 1):  # Xtract often returns 1 on success
        raise RuntimeError(f"Xtract failed (exit {proc.returncode})")

    candidates = sorted(output_dir.glob(f"{input_file.stem}*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else output_dir


def xtract_available() -> bool:
    return _find_binary(XTRACT_BIN_PATHS) is not None


def xtract_version() -> str:
    exe = _find_binary(XTRACT_BIN_PATHS)
    if not exe:
        return "unknown"
    try:
        r = subprocess.run([exe, "/version"], capture_output=True, text=True, timeout=5)
        return (r.stdout + r.stderr).strip().split("\n")[0] or "Xtract"
    except Exception:
        return "Xtract"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_binary(paths: list[str]) -> Optional[str]:
    for p in paths:
        if os.path.exists(p):
            return p
    return None
