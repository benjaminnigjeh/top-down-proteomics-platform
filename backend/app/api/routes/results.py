from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.api.deps import get_db
from app.models.result import ProteoformResult
from app.schemas.result import ProteoformResultRead, ResultFilter

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/job/{job_id}", response_model=list[ProteoformResultRead])
def get_results_for_job(
    job_id: str,
    engine_name: str | None = None,
    max_qvalue: float | None = None,
    min_score: float | None = None,
    accession: str | None = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
):
    filters = [ProteoformResult.job_id == job_id]
    if engine_name:
        filters.append(ProteoformResult.engine_name == engine_name)
    if max_qvalue is not None:
        filters.append(ProteoformResult.qvalue <= max_qvalue)
    if min_score is not None:
        filters.append(ProteoformResult.score >= min_score)
    if accession:
        filters.append(ProteoformResult.accession.ilike(f"%{accession}%"))

    stmt = (
        select(ProteoformResult)
        .where(and_(*filters))
        .order_by(ProteoformResult.qvalue)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return db.execute(stmt).scalars().all()


@router.get("/job/{job_id}/count")
def count_results(job_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import func
    n = db.execute(
        select(func.count()).where(ProteoformResult.job_id == job_id)
    ).scalar()
    return {"count": n}


@router.get("/job/{job_id}/by-engine")
def results_by_engine(job_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import func
    rows = db.execute(
        select(ProteoformResult.engine_name, func.count().label("n"))
        .where(ProteoformResult.job_id == job_id)
        .group_by(ProteoformResult.engine_name)
    ).all()
    return [{"engine": r.engine_name, "count": r.n} for r in rows]


@router.get("/job/{job_id}/venn")
def venn_overlap(job_id: str, db: Session = Depends(get_db)):
    """Return per-scan engine membership for Venn diagram."""
    rows = db.execute(
        select(ProteoformResult.scan_number, ProteoformResult.engine_name)
        .where(ProteoformResult.job_id == job_id)
        .where(ProteoformResult.scan_number.isnot(None))
    ).all()

    scan_engines: dict[int, set] = {}
    for scan, engine in rows:
        scan_engines.setdefault(scan, set()).add(engine)

    all_engines = sorted({e for engines in scan_engines.values() for e in engines})
    sets: dict[str, set] = {e: set() for e in all_engines}
    for scan, engines in scan_engines.items():
        for e in engines:
            sets[e].add(scan)

    result = {"engines": all_engines, "sets": {k: len(v) for k, v in sets.items()}, "overlaps": {}}
    for i, e1 in enumerate(all_engines):
        for e2 in all_engines[i+1:]:
            key = f"{e1}∩{e2}"
            result["overlaps"][key] = len(sets[e1] & sets[e2])
    return result


@router.get("/{result_id}", response_model=ProteoformResultRead)
def get_result(result_id: str, db: Session = Depends(get_db)):
    r = db.get(ProteoformResult, result_id)
    if not r:
        raise HTTPException(status_code=404, detail="Result not found")
    return r
