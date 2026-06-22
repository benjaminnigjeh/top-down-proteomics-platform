"""Central registry for all search engine and preprocessing adapters."""
from app.engines.base import SearchEngineAdapter
from app.engines.toppic import TopPICAdapter, TopMGAdapter
from app.engines.mspathfinder import MSPathFinderTAdapter
from app.engines.toplib import TopLibAdapter
from app.engines.flashdeconv import FLASHDeconvAdapter, FLASHDeconvTopPICAdapter
from app.engines.openms_tools import PeakPickerAdapter, DechargerAdapter, FeatureFinderCentroidedAdapter, ProMexAdapter
from app.engines.demo import DemoAdapter
from app.engines.proteo_ai import (
    ProteoIDAdapter, TruncNetAdapter, PTMNetAdapter,
    MassFlowNetAdapter, ProteoEngineAdapter,
)

_ADAPTERS: dict[str, SearchEngineAdapter] = {
    # ── Search engines ────────────────────────────────────────────────
    "toppic":           TopPICAdapter(),
    "topmg":            TopMGAdapter(),
    "mspathfindert":    MSPathFinderTAdapter(),
    "toplib":           TopLibAdapter(),
    # ── Deconvolution / preprocessing ────────────────────────────────
    "flashdeconv":      FLASHDeconvAdapter(),
    "peakpicker":       PeakPickerAdapter(),
    "decharger":        DechargerAdapter(),
    "featurefinder":    FeatureFinderCentroidedAdapter(),
    "promex":           ProMexAdapter(),
    # ── Pipelines (deconvolution + search combined) ───────────────────
    "flashdeconv_toppic": FLASHDeconvTopPICAdapter(),
    # ── Demo ─────────────────────────────────────────────────────────
    "demo":             DemoAdapter(),
    # ── AI placeholders ──────────────────────────────────────────────
    "proteoid":         ProteoIDAdapter(),
    "truncnet":         TruncNetAdapter(),
    "ptmnet":           PTMNetAdapter(),
    "massflownet":      MassFlowNetAdapter(),
    "proteoengine":     ProteoEngineAdapter(),
}


def get_adapter(name: str) -> SearchEngineAdapter:
    adapter = _ADAPTERS.get(name.lower())
    if not adapter:
        raise ValueError(f"Unknown engine: '{name}'. Available: {list(_ADAPTERS)}")
    return adapter


def list_engines() -> list[dict]:
    return [adapter.get_info() for adapter in _ADAPTERS.values()]


def list_available_engines() -> list[dict]:
    return [info for info in list_engines() if info["available"]]
