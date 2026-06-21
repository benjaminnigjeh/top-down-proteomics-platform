"""Tests for result queries and filtering."""
import pytest
from sqlalchemy.orm import Session

from app.models.result import ProteoformResult
from app.models.job import Job, JobEngine


def _seed_results(db: Session, job_id: str, engine_id: str, n: int = 5):
    results = []
    engines = ["toppic", "demo"]
    for i in range(n):
        r = ProteoformResult(
            job_id=job_id,
            job_engine_id=engine_id,
            engine_name=engines[i % len(engines)],
            scan_number=i + 1,
            accession=f"P{i:05d}",
            qvalue=0.001 * (i + 1),
            score=100.0 - i * 10,
            observed_mass=10000.0 + i * 500,
            is_demo=(engines[i % len(engines)] == "demo"),
        )
        db.add(r)
        results.append(r)
    db.commit()
    return results


class TestResultsEndpoint:
    def test_empty_results(self, client):
        resp = client.get("/api/v1/results/job/nonexistent")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_results_by_engine(self, client, db_session):
        job = Job(name="t", mzml_file_id="a", fasta_file_id="b", engines_requested=["demo"])
        db_session.add(job)
        db_session.flush()
        je = JobEngine(job_id=job.id, engine_name="demo")
        db_session.add(je)
        db_session.flush()
        _seed_results(db_session, job.id, je.id, 10)

        resp = client.get(f"/api/v1/results/job/{job.id}/by-engine")
        assert resp.status_code == 200
        data = resp.json()
        engine_names = {d["engine"] for d in data}
        assert "demo" in engine_names or "toppic" in engine_names

    def test_results_filter_by_max_qvalue(self, client, db_session):
        job = Job(name="t", mzml_file_id="a", fasta_file_id="b", engines_requested=["demo"])
        db_session.add(job)
        db_session.flush()
        je = JobEngine(job_id=job.id, engine_name="demo")
        db_session.add(je)
        db_session.flush()
        _seed_results(db_session, job.id, je.id, 10)

        resp = client.get(f"/api/v1/results/job/{job.id}?max_qvalue=0.002")
        assert resp.status_code == 200
        data = resp.json()
        assert all(r["qvalue"] <= 0.002 for r in data if r["qvalue"] is not None)

    def test_result_count(self, client, db_session):
        job = Job(name="t2", mzml_file_id="a", fasta_file_id="b", engines_requested=["demo"])
        db_session.add(job)
        db_session.flush()
        je = JobEngine(job_id=job.id, engine_name="demo")
        db_session.add(je)
        db_session.flush()
        _seed_results(db_session, job.id, je.id, 7)

        resp = client.get(f"/api/v1/results/job/{job.id}/count")
        assert resp.status_code == 200
        assert resp.json()["count"] == 7

    def test_venn_overlap(self, client, db_session):
        job = Job(name="venn", mzml_file_id="a", fasta_file_id="b", engines_requested=["demo", "toppic"])
        db_session.add(job)
        db_session.flush()
        je = JobEngine(job_id=job.id, engine_name="demo")
        db_session.add(je)
        db_session.flush()
        _seed_results(db_session, job.id, je.id, 6)

        resp = client.get(f"/api/v1/results/job/{job.id}/venn")
        assert resp.status_code == 200
        data = resp.json()
        assert "engines" in data
        assert "sets" in data
