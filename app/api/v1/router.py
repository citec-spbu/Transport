from fastapi import APIRouter
from app.api.v1.endpoints import auth, datasets, analysis

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
