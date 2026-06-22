"""
Celery tasks for file conversion and deconvolution.
"""
import logging
from datetime import datetime, UTC
from pathlib import Path

from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models.conversion import Conversion
from app.models.upload import Upload
from app.config import settings
from app.conversion.converter import (
    ConversionOptions, run_msconvert, run_thermoparser,
    msconvert_available, thermoparser_available,
)
from app.conversion.deconvolvers import (
    THRASHOptions, run_thrash, thrash_available,
    UniDecOptions, run_unidec, unidec_available,
    XtractOptions, run_xtract, xtract_available,
)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_conversion")
def run_conversion(self, conversion_id: str) -> dict:
    db = SessionLocal()
    try:
        return _execute_conversion(self, db, conversion_id)
    finally:
        db.close()


def _execute_conversion(task, db, conversion_id: str) -> dict:
    conv: Conversion = db.get(Conversion, conversion_id)
    if not conv:
        raise ValueError(f"Conversion {conversion_id} not found")

    conv.status = "running"
    conv.started_at = datetime.now(UTC)
    conv.log = ""
    db.commit()

    def append_log(line: str):
        conv.log = (conv.log or "") + line + "\n"
        db.commit()

    try:
        # Resolve input file
        upload: Upload = db.get(Upload, conv.input_file_id)
        if not upload:
            raise ValueError(f"Input file {conv.input_file_id} not found")
        input_file = (settings.UPLOAD_DIR / upload.stored_filename).resolve()
        if not input_file.exists():
            raise FileNotFoundError(f"Input file missing: {input_file}")

        output_dir = (settings.JOB_DIR / "conversions" / conversion_id).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        opts = conv.options or {}
        tool = conv.tool

        if tool == "msconvert":
            if not msconvert_available():
                raise RuntimeError("msconvert not found at expected path")
            co = ConversionOptions(**{k: v for k, v in opts.items()
                                     if hasattr(ConversionOptions, k)})
            output_file = run_msconvert(input_file, output_dir, co, append_log)

        elif tool == "thermoparser":
            if not thermoparser_available():
                raise RuntimeError("ThermoRawFileParser DLL not found at expected path")
            fmt = opts.get("thermo_output_format", "mzML")
            output_file = run_thermoparser(input_file, output_dir, fmt, append_log)

        elif tool == "thrash":
            if not thrash_available():
                raise RuntimeError("DeconConsole.exe not found; install DeconTools to C:\\tools\\DeconTools\\")
            to = THRASHOptions(
                min_mass=opts.get("thrash_min_mass", 400.0),
                max_mass=opts.get("thrash_max_mass", 200000.0),
                min_charge=opts.get("thrash_min_charge", 1),
                max_charge=opts.get("thrash_max_charge", 60),
                max_fit=opts.get("thrash_max_fit", 0.25),
                sn_threshold=opts.get("thrash_sn_threshold", 3.0),
                use_mercury=opts.get("thrash_use_mercury", True),
            )
            output_file = run_thrash(input_file, output_dir, to, append_log)

        elif tool == "unidec":
            if not unidec_available():
                raise RuntimeError(
                    "UniDec not found. Download from https://github.com/michaelmarty/UniDec/releases "
                    "and install to C:\\tools\\UniDec\\"
                )
            uo = UniDecOptions(
                min_mass=opts.get("unidec_min_mass", 1000.0),
                max_mass=opts.get("unidec_max_mass", 200000.0),
                min_mz=opts.get("unidec_min_mz", 200.0),
                max_mz=opts.get("unidec_max_mz", 8000.0),
                min_charge=opts.get("unidec_min_charge", 1),
                max_charge=opts.get("unidec_max_charge", 50),
                mass_bin_size=opts.get("unidec_mass_bin", 10.0),
                mz_bin_size=opts.get("unidec_mz_bin", 0.5),
            )
            output_file = run_unidec(input_file, output_dir, uo, append_log)

        elif tool == "xtract":
            if not xtract_available():
                raise RuntimeError(
                    "Xtract not found. Requires Thermo Xcalibur or FreeStyle installation."
                )
            xo = XtractOptions(
                min_mass=opts.get("xtract_min_mass", 400.0),
                max_mass=opts.get("xtract_max_mass", 100000.0),
                resolution=opts.get("xtract_resolution", 60000.0),
                sn_threshold=opts.get("xtract_sn", 3.0),
                fit_factor=opts.get("xtract_fit", 44.0),
                remainder=opts.get("xtract_remainder", 25.0),
            )
            output_file = run_xtract(input_file, output_dir, xo, append_log)

        else:
            raise ValueError(f"Unknown conversion tool: {tool}")

        # Record output
        output_file = Path(output_file)
        if output_file.is_file():
            conv.output_filename = output_file.name
            conv.output_path = str(output_file)
            conv.output_size_bytes = output_file.stat().st_size
        else:
            # Directory output (UniDec)
            conv.output_filename = output_file.name
            conv.output_path = str(output_file)

        conv.status = "completed"
        conv.completed_at = datetime.now(UTC)
        db.commit()

        return {"conversion_id": conversion_id, "status": "completed", "output": conv.output_filename}

    except Exception as exc:
        logger.exception("Conversion %s failed", conversion_id)
        conv.status = "failed"
        conv.error_message = str(exc)
        conv.completed_at = datetime.now(UTC)
        db.commit()
        raise
