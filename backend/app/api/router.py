from fastapi import APIRouter

from app.api.routes import exports, jobs, songs

api_router = APIRouter()
api_router.include_router(songs.router)
api_router.include_router(jobs.router)
api_router.include_router(exports.router)
