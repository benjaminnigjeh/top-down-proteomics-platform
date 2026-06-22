"""
REST API for file conversion and deconvolution jobs.
"""
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.database import SessionLocal
from app.models.conversion import Conversion
from app.models.upload import Upload
from app.schemas.conversion import ConversionCreate, ConversionRead
from app.workers.conversion_tasks import run_conversion
from app.conversion.converter import msconvert_available, thermoparser_available, msconvert_version
from app.conversion.deconvolvers import thrash_available, unidec_available, xtract_available

router = APIRouter(prefix="/conversions", tags=["conversions"])


@router.get("/tools")
def list_tools():
    """Return availability and metadata for each conversion tool."""
    return [
        {
            "id": "msconvert",
            "name": "msconvert (ProteoWizard)",
            "category": "format_conversion",
            "description": "Convert vendor instrument files to open formats (mzML, mzXML, MGF, etc.). "
                           "Supports all major vendors including Thermo, Bruker, Waters, and Agilent.",
            "available": msconvert_available(),
            "version": msconvert_version() if msconvert_available() else None,
            "input_formats": [".raw", ".d", ".wiff", ".mzML", ".mzXML", ".mgf", ".ms2"],
            "output_formats": ["mzML", "mzXML", "mgf", "ms2", "mz5"],
        },
        {
            "id": "thermoparser",
            "name": "ThermoRawFileParser",
            "category": "format_conversion",
            "description": "Fast, cross-platform conversion of Thermo .raw files using .NET 8. "
                           "Alternative to msconvert for Thermo instruments.",
            "available": thermoparser_available(),
            "version": "2.0.0-dev",
            "input_formats": [".raw"],
            "output_formats": ["mzML", "mzXML", "mgf", "parquet"],
        },
        {
            "id": "thrash",
            "name": "THRASH (DeconTools)",
            "category": "deconvolution",
            "description": "The THRASH algorithm (Horn et al.) for high-resolution mass spectrum deconvolution. "
                           "Determines charge states and computes neutral masses via isotopic pattern matching. "
                           "Ideal for FT-MS and Orbitrap data.",
            "available": thrash_available(),
            "version": "1.1.8658",
            "input_formats": [".raw", ".mzML", ".mzXML"],
            "output_formats": ["_isos.csv", "_scans.csv"],
        },
        {
            "id": "unidec",
            "name": "UniDec",
            "category": "deconvolution",
            "description": "Bayesian deconvolution tool particularly suited for native mass spectrometry "
                           "and intact protein analysis. Handles heterogeneous charge state distributions.",
            "available": unidec_available(),
            "version": "unknown",
            "input_formats": [".txt", ".mzML"],
            "output_formats": ["_unidecfiles/"],
        },
        {
            "id": "xtract",
            "name": "Xtract (Thermo)",
            "category": "deconvolution",
            "description": "Thermo's proprietary deconvolution algorithm bundled with Xcalibur and FreeStyle. "
                           "Highly optimized for Orbitrap data.",
            "available": xtract_available(),
            "version": "unknown",
            "input_formats": [".raw"],
            "output_formats": [".mzML"],
        },
    ]


@router.post("", response_model=ConversionRead, status_code=status.HTTP_201_CREATED)
def create_conversion(payload: ConversionCreate, db: Session = Depends(get_db)):
    """Submit a new conversion / deconvolution job."""
    upload: Upload = db.get(Upload, payload.input_file_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Input file not found")

    valid_tools = {"msconvert", "thermoparser", "thrash", "unidec", "xtract"}
    if payload.tool not in valid_tools:
        raise HTTPException(status_code=400, detail=f"Unknown tool: {payload.tool}. Valid: {valid_tools}")

    conv = Conversion(
        name=payload.name,
        input_file_id=payload.input_file_id,
        input_filename=upload.original_filename,
        tool=payload.tool,
        options=payload.options.model_dump(),
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    task = run_conversion.delay(conv.id)
    conv.celery_task_id = task.id
    conv.status = "queued"
    db.commit()
    db.refresh(conv)
    return conv


@router.get("", response_model=list[ConversionRead])
def list_conversions(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    rows = db.execute(
        select(Conversion).order_by(Conversion.created_at.desc()).offset(skip).limit(limit)
    ).scalars().all()
    return rows


@router.get("/{conversion_id}", response_model=ConversionRead)
def get_conversion(conversion_id: str, db: Session = Depends(get_db)):
    conv = db.get(Conversion, conversion_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversion not found")
    return conv


@router.delete("/{conversion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversion(conversion_id: str, db: Session = Depends(get_db)):
    conv = db.get(Conversion, conversion_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversion not found")
    if conv.output_path and os.path.isfile(conv.output_path):
        try:
            os.unlink(conv.output_path)
        except Exception:
            pass
    db.delete(conv)
    db.commit()


@router.get("/{conversion_id}/download")
def download_conversion(conversion_id: str, db: Session = Depends(get_db)):
    conv = db.get(Conversion, conversion_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversion not found")
    if conv.status != "completed":
        raise HTTPException(status_code=400, detail=f"Conversion not completed (status: {conv.status})")
    if not conv.output_path or not os.path.isfile(conv.output_path):
        raise HTTPException(status_code=404, detail="Output file not found on disk")
    return FileResponse(
        path=conv.output_path,
        filename=conv.output_filename,
        media_type="application/octet-stream",
    )
