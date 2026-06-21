"""
ProteoBio AI Engine Adapters — placeholder stubs.

These adapters define the interface for future AI-powered search engines:
- ProteoID
- TruncNet
- PTMNet
- MassFlowNet
- ProteoEngine

Each inherits from SearchEngineAdapter and follows the same contract.
Replace the NotImplementedError bodies with actual model calls when available.
"""
from app.engines.proteo_ai.proteoid import ProteoIDAdapter
from app.engines.proteo_ai.truncnet import TruncNetAdapter
from app.engines.proteo_ai.ptmnet import PTMNetAdapter
from app.engines.proteo_ai.massflownet import MassFlowNetAdapter
from app.engines.proteo_ai.proteoengine import ProteoEngineAdapter

__all__ = [
    "ProteoIDAdapter",
    "TruncNetAdapter",
    "PTMNetAdapter",
    "MassFlowNetAdapter",
    "ProteoEngineAdapter",
]
