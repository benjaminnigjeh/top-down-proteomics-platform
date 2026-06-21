"""
Tests for engine adapters.

These tests verify the adapter interface contract without requiring
real engines to be installed. Integration tests require actual binaries.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.engines.base import SearchEngineAdapter, ProteoformResult
from app.engines.demo import DemoAdapter
from app.engines.toppic import TopPICAdapter, _parse_ptm_string, _float, _int
from app.engines.registry import get_adapter, list_engines


class TestProteoformResult:
    def test_defaults_are_none(self):
        r = ProteoformResult(engine_name="test")
        assert r.accession is None
        assert r.score is None
        assert r.ptms == []
        assert r.is_demo is False


class TestBaseAdapterContract:
    def test_all_adapters_have_name(self):
        for info in list_engines():
            assert info["name"], "Engine must have a name"

    def test_all_adapters_have_input_formats(self):
        for info in list_engines():
            assert isinstance(info["input_formats"], list)

    def test_get_adapter_raises_on_unknown(self):
        with pytest.raises(ValueError, match="Unknown engine"):
            get_adapter("nonexistent_engine_xyz")

    def test_get_adapter_returns_known_engine(self):
        adapter = get_adapter("demo")
        assert adapter.name == "demo"

    def test_export_standardized_creates_tsv(self, tmp_path):
        from app.engines.demo import DemoAdapter
        adapter = DemoAdapter()
        results = adapter.parse_results(tmp_path)
        out = adapter.export_standardized(results, tmp_path)
        assert out.exists()
        content = out.read_text()
        assert "engine_name" in content


class TestDemoAdapter:
    def test_demo_adapter_available_when_enabled(self):
        with patch("app.config.settings.DEMO_MODE_ENABLED", True):
            adapter = DemoAdapter()
            assert adapter.validate_installation() is True

    def test_demo_adapter_unavailable_when_disabled(self):
        with patch("app.config.settings.DEMO_MODE_ENABLED", False):
            adapter = DemoAdapter()
            assert adapter.validate_installation() is False

    def test_demo_run_search_logs_warning(self, tmp_path):
        adapter = DemoAdapter()
        logs = []
        adapter.run_search(
            input_files=[tmp_path / "fake.mzML"],
            database_path=tmp_path / "fake.fasta",
            params={},
            output_dir=tmp_path / "out",
            log_callback=logs.append,
        )
        assert any("DEMO" in line for line in logs)

    def test_demo_parse_results_returns_fifty_results(self, tmp_path):
        adapter = DemoAdapter()
        results = adapter.parse_results(tmp_path)
        assert len(results) == 50

    def test_demo_results_all_flagged_as_demo(self, tmp_path):
        adapter = DemoAdapter()
        results = adapter.parse_results(tmp_path)
        assert all(r.is_demo is True for r in results)

    def test_demo_results_have_required_fields(self, tmp_path):
        adapter = DemoAdapter()
        results = adapter.parse_results(tmp_path)
        for r in results:
            assert r.engine_name == "demo"
            assert r.scan_number is not None
            assert r.observed_mass is not None
            assert r.accession is not None

    def test_demo_results_have_valid_qvalues(self, tmp_path):
        adapter = DemoAdapter()
        results = adapter.parse_results(tmp_path)
        for r in results:
            if r.qvalue is not None:
                assert 0 <= r.qvalue <= 1


class TestTopPICParsing:
    def test_parse_ptm_string_empty(self):
        assert _parse_ptm_string("") == []

    def test_parse_ptm_string_single(self):
        result = _parse_ptm_string("phospho[S3]")
        assert len(result) == 1
        assert result[0]["modification"] == "phospho"
        assert result[0]["residue"] == "S"
        assert result[0]["position"] == 3

    def test_parse_ptm_string_multiple(self):
        result = _parse_ptm_string("phospho[S3];acetyl[K5]")
        assert len(result) == 2
        assert result[1]["modification"] == "acetyl"

    def test_parse_ptm_string_invalid_ignored(self):
        result = _parse_ptm_string("invalid_mod")
        assert result == []

    def test_float_helper_handles_none(self):
        assert _float(None) is None

    def test_float_helper_handles_string(self):
        assert _float("3.14") == pytest.approx(3.14)

    def test_int_helper_handles_range(self):
        assert _int("5-10") == 5


class TestProteoBioPlaceholders:
    def test_placeholder_adapters_not_installed(self):
        for name in ["proteoid", "truncnet", "ptmnet", "massflownet", "proteoengine"]:
            adapter = get_adapter(name)
            assert adapter.validate_installation() is False

    def test_placeholder_run_search_raises(self, tmp_path):
        from app.engines.proteo_ai.proteoid import ProteoIDAdapter
        adapter = ProteoIDAdapter()
        with pytest.raises(NotImplementedError):
            adapter.run_search([], tmp_path / "db.fasta", {}, tmp_path / "out")
