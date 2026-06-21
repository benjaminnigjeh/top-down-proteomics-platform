"""
Celery tasks for job execution.

Each job spawns one sub-task per engine, run sequentially within a single Celery task.
Parallel multi-engine jobs can be achieved by dispatching separate tasks.
"""
import logging
from datetime import datetime, UTC
from pathlib import Path

from celery import shared_task
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models.job import Job, JobEngine
from app.models.result import ProteoformResult as DBResult
from app.engines.registry import get_adapter
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_job")
def run_job(self, job_id: str) -> dict:
    db = SessionLocal()
    try:
        return _execute_job(self, db, job_id)
    finally:
        db.close()


def _execute_job(task, db: Session, job_id: str) -> dict:
    job: Job = db.get(Job, job_id)
    if not job:
        raise ValueError(f"Job {job_id} not found")

    job.status = "running"
    job.started_at = datetime.now(UTC)
    db.commit()

    upload_dir = settings.UPLOAD_DIR
    job_dir = settings.JOB_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    # Resolve uploaded file paths
    mzml_path = _resolve_upload(db, job.mzml_file_id, upload_dir)
    fasta_path = _resolve_upload(db, job.fasta_file_id, upload_dir)
    ptm_path = _resolve_upload(db, job.ptm_file_id, upload_dir) if job.ptm_file_id else None

    params = job.parameters or {}
    total_engines = len(job.engines_requested)
    completed = 0
    any_failed = False

    for engine_name in job.engines_requested:
        job_engine: JobEngine = next(
            (e for e in job.engine_runs if e.engine_name == engine_name), None
        )
        if not job_engine:
            job_engine = JobEngine(job_id=job_id, engine_name=engine_name)
            db.add(job_engine)
            db.commit()

        engine_dir = job_dir / engine_name
        engine_dir.mkdir(parents=True, exist_ok=True)
        log_lines = []

        try:
            adapter = get_adapter(engine_name)
            if not adapter.validate_installation():
                raise RuntimeError(
                    f"Engine '{engine_name}' is not installed. "
                    f"See README for installation instructions."
                )

            job_engine.status = "running"
            job_engine.started_at = datetime.now(UTC)
            db.commit()

            def log_cb(line: str):
                log_lines.append(line)
                job_engine.log = "\n".join(log_lines)
                db.commit()

            db_path = adapter.prepare_database(fasta_path, ptm_path, engine_dir / "db")
            adapter.run_search([mzml_path], db_path, params, engine_dir / "output", log_cb)

            results = adapter.parse_results(engine_dir / "output")
            results = adapter.estimate_fdr(results)

            # Persist results to database
            for r in results:
                r.job_id = job_id
                db_result = DBResult(
                    job_id=job_id,
                    job_engine_id=job_engine.id,
                    engine_name=r.engine_name,
                    engine_version=r.engine_version,
                    spectrum_id=r.spectrum_id,
                    scan_number=r.scan_number,
                    source_file=r.source_file,
                    precursor_mz=r.precursor_mz,
                    charge=r.charge,
                    observed_mass=r.observed_mass,
                    theoretical_mass=r.theoretical_mass,
                    delta_mass=r.delta_mass,
                    accession=r.accession,
                    protein_name=r.protein_name,
                    sequence=r.sequence,
                    proteoform_string=r.proteoform_string,
                    proteoform_mass=r.proteoform_mass,
                    score=r.score,
                    evalue=r.evalue,
                    qvalue=r.qvalue,
                    fdr=r.fdr,
                    matched_fragments=r.matched_fragments,
                    sequence_coverage=r.sequence_coverage,
                    ptms=r.ptms,
                    localization_confidence=r.localization_confidence,
                    raw_engine_output_path=r.raw_engine_output_path,
                    is_demo=r.is_demo,
                )
                db.add(db_result)

            job_engine.result_count = len(results)
            job_engine.status = "completed"
            job_engine.completed_at = datetime.now(UTC)
            db.commit()

        except Exception as exc:
            logger.exception(f"Engine {engine_name} failed for job {job_id}")
            log_lines.append(f"ERROR: {exc}")
            job_engine.log = "\n".join(log_lines)
            job_engine.status = "failed"
            job_engine.completed_at = datetime.now(UTC)
            db.commit()
            any_failed = True

        completed += 1
        task.update_state(state="PROGRESS", meta={"percent": int(completed / total_engines * 100)})

    job.status = "failed" if any_failed and completed == total_engines else "completed"
    job.completed_at = datetime.now(UTC)
    db.commit()

    return {"job_id": job_id, "status": job.status}


def _resolve_upload(db: Session, file_id: str, upload_dir: Path) -> Path:
    from app.models.upload import Upload
    upload = db.get(Upload, file_id)
    if not upload:
        raise FileNotFoundError(f"Upload {file_id} not found in database")
    path = upload_dir / upload.stored_filename
    if not path.exists():
        raise FileNotFoundError(f"Uploaded file not found on disk: {path}")
    return path
