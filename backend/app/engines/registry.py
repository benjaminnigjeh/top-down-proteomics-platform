"""Central registry for all search engine and preprocessing adapters."""
from app.engines.base import SearchEngineAdapter
from app.engines.mspathfinder import MSPathFinderTAdapter
from app.engines.flashdeconv import FLASHDeconvAdapter, FLASHDeconvTopPICAdapter
from app.engines.openms_tools import PeakPickerAdapter, DechargerAdapter, FeatureFinderCentroidedAdapter, ProMexAdapter
from app.engines.toppic_docker import (
    TopFDDockerAdapter, TopPICDockerAdapter, TopMGDockerAdapter, TopDiffDockerAdapter,
)
from app.engines.extras import (
    PTopAdapter, ProteinProspectorAdapter,
    MetaMorpheusAdapter, ProteoformSuiteAdapter,
    THRASHAdapter, UniDecAdapter, XtractAdapter,
)
from app.engines.demo import DemoAdapter
from app.engines.nrtdp import ModformProAdapter, TDCDFDRAdapter, TdReportConverterAdapter

_ADAPTERS: dict[str, SearchEngineAdapter] = {
    # ── Search engines ────────────────────────────────────────────────
    # Note: toppic / topmg / topdiff already run TopFD internally.
    # Select a search engine OR topfd-standalone — not both.
    "toppic":               TopPICDockerAdapter(),
    "topmg":                TopMGDockerAdapter(),
    "topdiff":              TopDiffDockerAdapter(),
    "mspathfindert":        MSPathFinderTAdapter(),
    "ptop":                 PTopAdapter(),
    "protein_prospector":   ProteinProspectorAdapter(),
    "metamorpheus":         MetaMorpheusAdapter(),
    # ── Deconvolution / preprocessing ────────────────────────────────
    # topfd standalone: use when you only need deconvolved msalign files
    "topfd":                TopFDDockerAdapter(),
    "flashdeconv":          FLASHDeconvAdapter(),
    "peakpicker":           PeakPickerAdapter(),
    "decharger":            DechargerAdapter(),
    "featurefinder":        FeatureFinderCentroidedAdapter(),
    "promex":               ProMexAdapter(),
    "thrash":               THRASHAdapter(),
    "unidec":               UniDecAdapter(),
    "xtract":               XtractAdapter(),
    # ── Pipelines (deconvolution + search combined) ───────────────────
    "proteoform_suite":     ProteoformSuiteAdapter(),
    "flashdeconv_toppic":   FLASHDeconvTopPICAdapter(),
    "tdreport_converter":   TdReportConverterAdapter(),
    # ── Post-processing ──────────────────────────────────────────────
    "modformpro":           ModformProAdapter(),
    "tdcd_fdr":             TDCDFDRAdapter(),
    # ── Demo ─────────────────────────────────────────────────────────
    "demo":                 DemoAdapter(),
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
