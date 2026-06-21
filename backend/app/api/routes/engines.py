from fastapi import APIRouter
from app.engines.registry import list_engines, list_available_engines

router = APIRouter(prefix="/engines", tags=["engines"])


@router.get("")
def get_all_engines():
    return list_engines()


@router.get("/available")
def get_available_engines():
    return list_available_engines()
