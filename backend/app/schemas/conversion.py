from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class ConversionOptionsSchema(BaseModel):
    # Format
    output_format: str = "mzML"           # mzML | mzXML | mgf | ms2 | mz5

    # Precision
    mz_precision: int = 64               # 32 | 64
    intensity_precision: int = 32        # 32 | 64

    # Compression
    zlib: bool = False
    numpress_linear: bool = False
    numpress_slof: bool = False
    numpress_pic: bool = False
    gzip_output: bool = False

    # Options
    write_index: bool = True
    sim_as_spectra: bool = False
    srm_as_spectra: bool = False
    combine_ion_mobility: bool = False
    ignore_unknown_instrument: bool = False
    strip_location: bool = False
    strip_version: bool = False
    single_threaded: bool = False
    verbose: bool = True

    # Filters
    peak_picking: str = "none"           # none | vendor | cwt
    peak_picking_ms_levels: str = "1-"
    peak_picking_snr: Optional[float] = None
    peak_picking_spacing: Optional[float] = None

    ms_levels: Optional[str] = None
    scan_number_range: Optional[str] = None
    scan_time_range: Optional[str] = None
    mz_window: Optional[str] = None

    threshold_type: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_orientation: str = "most-intense"
    threshold_ms_levels: Optional[str] = None

    zero_samples: Optional[str] = None

    charge_state_predictor: bool = False
    charge_predictor_override: bool = False
    charge_predictor_min: int = 2
    charge_predictor_max: int = 3

    etd_filter: bool = False
    etd_remove_precursor: bool = True
    etd_remove_charge_reduced: bool = True
    etd_remove_neutral_loss: bool = True
    etd_blanket_removal: bool = True

    precursor_recalculation: bool = False
    precursor_refine: bool = False

    metadata_fixer: bool = False
    sort_by_scan_time: bool = False

    ms2_denoise: bool = False
    ms2_denoise_peaks: int = 6
    ms2_denoise_window: float = 30.0
    ms2_deisotope: bool = False

    activation_type: Optional[str] = None
    polarity: Optional[str] = None
    analyzer: Optional[str] = None

    min_peaks: Optional[int] = None
    scan_summing: bool = False

    # ThermoRawFileParser-specific (used when tool == "thermoparser")
    thermo_output_format: str = "mzML"

    # THRASH-specific
    thrash_min_mass: float = 400.0
    thrash_max_mass: float = 200000.0
    thrash_min_charge: int = 1
    thrash_max_charge: int = 60
    thrash_max_fit: float = 0.25
    thrash_sn_threshold: float = 3.0
    thrash_use_mercury: bool = True

    # UniDec-specific
    unidec_min_mass: float = 1000.0
    unidec_max_mass: float = 200000.0
    unidec_min_mz: float = 200.0
    unidec_max_mz: float = 8000.0
    unidec_min_charge: int = 1
    unidec_max_charge: int = 50
    unidec_mass_bin: float = 10.0
    unidec_mz_bin: float = 0.5

    # Xtract-specific
    xtract_min_mass: float = 400.0
    xtract_max_mass: float = 100000.0
    xtract_resolution: float = 60000.0
    xtract_sn: float = 3.0
    xtract_fit: float = 44.0
    xtract_remainder: float = 25.0


class ConversionCreate(BaseModel):
    name: str
    input_file_id: str
    tool: str = "msconvert"
    options: ConversionOptionsSchema = ConversionOptionsSchema()


class ConversionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    status: str
    input_file_id: str
    input_filename: str
    tool: str
    options: dict[str, Any]
    output_filename: Optional[str] = None
    output_size_bytes: Optional[int] = None
    log: str
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
