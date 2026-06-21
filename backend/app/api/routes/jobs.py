from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.api.deps import get_db
from app.models.job import Job, JobEngine
from app.models.result import ProteoformResult
from app.schemas.job import JobCreate, JobRead, JobStatus
from app.engines.registry import get_adapter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    # Validate engines exist
    for engine_name in payload.engines:
        try:
            get_adapter(engine_name)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    job = Job(
        name=payload.name,
        mzml_file_id=payload.mzml_file_id,
        fasta_file_id=payload.fasta_file_id,
        ptm_file_id=payload.ptm_file_id,
        engines_requested=payload.engines,
        parameters=payload.parameters.model_dump(),
    )
    db.add(job)
    db.flush()

    for engine_name in payload.engines:
        je = JobEngine(job_id=job.id, engine_name=engine_name)
        db.add(je)

    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/submit", response_model=JobRead)
def submit_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ("pending", "failed"):
        raise HTTPException(status_code=409, detail=f"Job is already {job.status}")

    from app.workers.tasks import run_job
    task = run_job.delay(job_id)
    job.status = "queued"
    job.celery_task_id = task.id
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[JobRead])
def list_jobs(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    stmt = select(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/{job_id}/status", response_model=JobStatus)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    total_results = db.execute(
        select(ProteoformResult).where(ProteoformResult.job_id == job_id)
    ).scalars().all()

    engine_statuses = {je.engine_name: je.status for je in job.engine_runs}
    completed = sum(1 for s in engine_statuses.values() if s in ("completed", "failed"))
    progress = (completed / max(len(engine_statuses), 1)) * 100

    return JobStatus(
        job_id=job_id,
        status=job.status,
        progress_percent=progress,
        engine_statuses=engine_statuses,
        total_results=len(total_results),
    )


@router.get("/{job_id}/logs/{engine_name}")
def get_engine_log(job_id: str, engine_name: str, db: Session = Depends(get_db)):
    job_engine = db.execute(
        select(JobEngine).where(
            JobEngine.job_id == job_id,
            JobEngine.engine_name == engine_name,
        )
    ).scalar_one_or_none()
    if not job_engine:
        raise HTTPException(status_code=404, detail="Engine run not found")
    return {"log": job_engine.log, "status": job_engine.status}


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.celery_task_id and job.status == "running":
        from app.workers.celery_app import celery_app
        celery_app.control.revoke(job.celery_task_id, terminate=True)
    db.delete(job)
    db.commit()
