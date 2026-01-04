"""aPI routes package"""

from fastapi import APIRouter

from app.api.routes import materials, search, compare, predict, phase_diagram

router = APIRouter()

router.include_router(materials.router, prefix="/materials", tags=["materials"])
router.include_router(search.router, prefix="/search", tags=["search"])
router.include_router(compare.router, prefix="/compare", tags=["compare"])
router.include_router(predict.router, prefix="/predict", tags=["predict"])
router.include_router(phase_diagram.router, prefix="/phase-diagram", tags=["phase-diagram"])
