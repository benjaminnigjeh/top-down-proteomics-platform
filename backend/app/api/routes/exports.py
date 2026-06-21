import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.models.result import ProteoformResult
from app.models.job import Job, JobEngine
from app.utils.export_utils import (
    export_csv, export_json, export_mzidentml, export_proforma,
    export_ptm_library_xml, export_annotated_fasta, export_raw_zip, export_consensus,
)

router = APIRouter(prefix="/exports", tags=["exports"])

FORMATS = ["csv", "tsv", "json", "mzidentml", "proforma", "ptm_xml", "fasta", "raw_zip", "consensus"]


def _get_results(job_id: str, db: Session) -> list:
    return db.execute(
        select(ProteoformResult).where(ProteoformResult.job_id == job_id)
    ).scalars().all()


@router.get("/job/{job_id}/{format}")
def export_job_results(job_id: str, format: str, db: Session = Depends(get_db)):
    if format not in FORMATS:
        raise HTTPException(status_code=400, detail=f"Unknown format. Choose from: {FORMATS}")

    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    results = _get_results(job_id, db)

    # Create a temp directory for the export file
    tmp_dir = Path(tempfile.mkdtemp())

    if format == "csv":
        path = export_csv(results, tmp_dir / "results.csv")
        media_type = "text/csv"
        filename = f"tdportal_{job_id[:8]}_results.csv"

    elif format == "tsv":
        path = export_csv(results, tmp_dir / "results.tsv", delimiter="\t")
        media_type = "text/tab-separated-values"
        filename = f"tdportal_{job_id[:8]}_results.tsv"

    elif format == "json":
        path = export_json(results, tmp_dir / "results.json")
        media_type = "application/json"
        filename = f"tdportal_{job_id[:8]}_results.json"

    elif format == "mzidentml":
        path = export_mzidentml(results, tmp_dir / "results.mzid", job_id)
        media_type = "application/xml"
        filename = f"tdportal_{job_id[:8]}_results.mzid"

    elif format == "proforma":
        path = export_proforma(results, tmp_dir / "proteoforms.txt")
        media_type = "text/plain"
        filename = f"tdportal_{job_id[:8]}_proteoforms.txt"

    elif format == "ptm_xml":
        path = export_ptm_library_xml(results, tmp_dir / "ptm_library.xml")
        media_type = "application/xml"
        filename = f"tdportal_{job_id[:8]}_ptm_library.xml"

    elif format == "fasta":
        path = export_annotated_fasta(results, tmp_dir / "proteoforms.fasta")
        media_type = "application/octet-stream"
        filename = f"tdportal_{job_id[:8]}_proteoforms.fasta"

    elif format == "raw_zip":
        from app.config import settings
        raw_dirs = [settings.JOB_DIR / job_id / je.engine_name / "output"
                    for je in job.engine_runs]
        path = export_raw_zip(raw_dirs, tmp_dir / "raw_output.zip")
        media_type = "application/zip"
        filename = f"tdportal_{job_id[:8]}_raw_output.zip"

    elif format == "consensus":
        path = export_consensus(results, tmp_dir / "consensus.tsv")
        media_type = "text/tab-separated-values"
        filename = f"tdportal_{job_id[:8]}_consensus.tsv"

    else:
        raise HTTPException(status_code=400, detail="Unknown format")

    return FileResponse(path=str(path), media_type=media_type, filename=filename)
