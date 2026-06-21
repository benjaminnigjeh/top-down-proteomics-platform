"""Tests for result export utilities."""
import json
import pytest
from pathlib import Path

from app.engines.demo import DemoAdapter
from app.utils.export_utils import (
    export_csv, export_json, export_mzidentml, export_proforma,
    export_ptm_library_xml, export_annotated_fasta, export_consensus,
)


@pytest.fixture
def demo_results(tmp_path):
    adapter = DemoAdapter()
    return adapter.parse_results(tmp_path)


class TestExportCSV:
    def test_creates_file(self, demo_results, tmp_path):
        path = export_csv(demo_results, tmp_path / "out.csv")
        assert path.exists()

    def test_has_header_row(self, demo_results, tmp_path):
        path = export_csv(demo_results, tmp_path / "out.csv")
        lines = path.read_text().splitlines()
        assert "engine_name" in lines[0]

    def test_row_count_matches(self, demo_results, tmp_path):
        path = export_csv(demo_results, tmp_path / "out.csv")
        lines = path.read_text().splitlines()
        assert len(lines) == len(demo_results) + 1  # +1 for header

    def test_empty_results(self, tmp_path):
        path = export_csv([], tmp_path / "empty.csv")
        assert path.exists()

    def test_tsv_delimiter(self, demo_results, tmp_path):
        path = export_csv(demo_results, tmp_path / "out.tsv", delimiter="\t")
        first_line = path.read_text().splitlines()[0]
        assert "\t" in first_line


class TestExportJSON:
    def test_creates_valid_json(self, demo_results, tmp_path):
        path = export_json(demo_results, tmp_path / "out.json")
        data = json.loads(path.read_text())
        assert isinstance(data, list)
        assert len(data) == len(demo_results)

    def test_all_results_have_engine_name(self, demo_results, tmp_path):
        path = export_json(demo_results, tmp_path / "out.json")
        data = json.loads(path.read_text())
        assert all(d["engine_name"] == "demo" for d in data)


class TestExportMzIdentML:
    def test_creates_valid_xml(self, demo_results, tmp_path):
        path = export_mzidentml(demo_results, tmp_path / "out.mzid", "test-job-123")
        content = path.read_text()
        assert "MzIdentML" in content
        assert "SpectrumIdentificationResult" in content

    def test_contains_job_id(self, demo_results, tmp_path):
        path = export_mzidentml(demo_results, tmp_path / "out.mzid", "myjobid")
        assert "myjobid" in path.read_text()


class TestExportProForma:
    def test_creates_file_with_proteoforms(self, demo_results, tmp_path):
        path = export_proforma(demo_results, tmp_path / "out.txt")
        lines = [l for l in path.read_text().splitlines() if l]
        assert len(lines) == len(demo_results)


class TestExportPTMLibrary:
    def test_creates_xml_with_ptm_entries(self, demo_results, tmp_path):
        results_with_ptms = [r for r in demo_results if r.ptms]
        path = export_ptm_library_xml(results_with_ptms, tmp_path / "ptm.xml")
        content = path.read_text()
        assert "<PTMLibrary>" in content
        if results_with_ptms:
            assert "<PTM" in content


class TestExportAnnotatedFasta:
    def test_creates_fasta_file(self, demo_results, tmp_path):
        path = export_annotated_fasta(demo_results, tmp_path / "out.fasta")
        content = path.read_text()
        assert ">" in content

    def test_accessions_deduped(self, demo_results, tmp_path):
        path = export_annotated_fasta(demo_results, tmp_path / "out.fasta")
        headers = [l for l in path.read_text().splitlines() if l.startswith(">")]
        accessions = [h.split()[0][1:] for h in headers]
        assert len(accessions) == len(set(accessions))


class TestExportConsensus:
    def test_consensus_multi_engine(self, tmp_path):
        # Create synthetic multi-engine results
        from app.engines.base import ProteoformResult
        results = [
            ProteoformResult(engine_name="toppic", scan_number=1, qvalue=0.001, score=100),
            ProteoformResult(engine_name="demo", scan_number=1, qvalue=0.002, score=90),
            ProteoformResult(engine_name="toppic", scan_number=2, qvalue=0.003, score=80),
        ]
        path = export_consensus(results, tmp_path / "consensus.tsv")
        lines = [l for l in path.read_text().splitlines() if l]
        assert len(lines) >= 2  # header + at least one consensus row

    def test_consensus_single_engine_no_rows(self, tmp_path):
        from app.engines.base import ProteoformResult
        results = [ProteoformResult(engine_name="toppic", scan_number=1)]
        path = export_consensus(results, tmp_path / "consensus.tsv")
        lines = [l for l in path.read_text().splitlines() if l]
        assert len(lines) == 1  # only header
