import time
from fastapi import APIRouter
from app.engines.registry import list_engines, list_available_engines

router = APIRouter(prefix="/engines", tags=["engines"])

_CACHE_TTL = 60  # seconds
_cache: dict = {"data": None, "ts": 0.0}


def _cached_list() -> list:
    now = time.monotonic()
    if _cache["data"] is None or (now - _cache["ts"]) > _CACHE_TTL:
        _cache["data"] = list_engines()
        _cache["ts"] = now
    return _cache["data"]


@router.get("")
def get_all_engines():
    return _cached_list()


@router.get("/available")
def get_available_engines():
    return [e for e in _cached_list() if e["available"]]


@router.post("/refresh")
def refresh_engines():
    """Force re-validation of all engines (clears the cache)."""
    _cache["data"] = None
    return _cached_list()
