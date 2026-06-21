"""Tests for job creation, submission, status, and retrieval."""
import pytest
import io


class TestUploadEndpoints:
    def test_upload_fasta_success(self, client, sample_fasta_bytes):
        resp = client.post(
            "/api/v1/uploads",
            files={"file": ("test.fasta", io.BytesIO(sample_fasta_bytes), "text/plain")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_type"] == "fasta"
        assert data["size_bytes"] == len(sample_fasta_bytes)

    def test_upload_mzml_success(self, client, sample_mzml_bytes):
        resp = client.post(
            "/api/v1/uploads",
            files={"file": ("test.mzML", io.BytesIO(sample_mzml_bytes), "text/xml")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["file_type"] == "mzml"

    def test_upload_disallows_executable(self, client):
        resp = client.post(
            "/api/v1/uploads",
            files={"file": ("malware.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_upload_rejects_empty_file(self, client):
        resp = client.post(
            "/api/v1/uploads",
            files={"file": ("empty.fasta", io.BytesIO(b""), "text/plain")},
        )
        assert resp.status_code == 400

    def test_get_upload_not_found(self, client):
        resp = client.get("/api/v1/uploads/nonexistent-id")
        assert resp.status_code == 404


def _upload_files(client, fasta_bytes, mzml_bytes):
    r1 = client.post("/api/v1/uploads", files={"file": ("test.fasta", io.BytesIO(fasta_bytes), "text/plain")})
    r2 = client.post("/api/v1/uploads", files={"file": ("test.mzML", io.BytesIO(mzml_bytes), "text/xml")})
    assert r1.status_code == 201
    assert r2.status_code == 201
    return r1.json()["id"], r2.json()["id"]


class TestJobCreation:
    def test_create_job_with_demo_engine(self, client, sample_fasta_bytes, sample_mzml_bytes):
        fasta_id, mzml_id = _upload_files(client, sample_fasta_bytes, sample_mzml_bytes)
        resp = client.post("/api/v1/jobs", json={
            "name": "Test Job",
            "mzml_file_id": mzml_id,
            "fasta_file_id": fasta_id,
            "engines": ["demo"],
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["engines_requested"] == ["demo"]
        assert len(data["engine_runs"]) == 1

    def test_create_job_with_unknown_engine_fails(self, client, sample_fasta_bytes, sample_mzml_bytes):
        fasta_id, mzml_id = _upload_files(client, sample_fasta_bytes, sample_mzml_bytes)
        resp = client.post("/api/v1/jobs", json={
            "name": "Bad Job",
            "mzml_file_id": mzml_id,
            "fasta_file_id": fasta_id,
            "engines": ["nonexistent"],
        })
        assert resp.status_code == 400

    def test_list_jobs_returns_list(self, client):
        resp = client.get("/api/v1/jobs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_job_not_found(self, client):
        resp = client.get("/api/v1/jobs/nonexistent")
        assert resp.status_code == 404

    def test_job_status_before_run(self, client, sample_fasta_bytes, sample_mzml_bytes):
        fasta_id, mzml_id = _upload_files(client, sample_fasta_bytes, sample_mzml_bytes)
        create_resp = client.post("/api/v1/jobs", json={
            "name": "Status Test",
            "mzml_file_id": mzml_id,
            "fasta_file_id": fasta_id,
            "engines": ["demo"],
        })
        job_id = create_resp.json()["id"]
        status_resp = client.get(f"/api/v1/jobs/{job_id}/status")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["job_id"] == job_id
        assert "engine_statuses" in data
        assert "demo" in data["engine_statuses"]

    def test_delete_job(self, client, sample_fasta_bytes, sample_mzml_bytes):
        fasta_id, mzml_id = _upload_files(client, sample_fasta_bytes, sample_mzml_bytes)
        create_resp = client.post("/api/v1/jobs", json={
            "name": "Delete Me",
            "mzml_file_id": mzml_id,
            "fasta_file_id": fasta_id,
            "engines": ["demo"],
        })
        job_id = create_resp.json()["id"]
        del_resp = client.delete(f"/api/v1/jobs/{job_id}")
        assert del_resp.status_code == 204
        get_resp = client.get(f"/api/v1/jobs/{job_id}")
        assert get_resp.status_code == 404
