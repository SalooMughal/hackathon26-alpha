from fastapi import APIRouter

from app.api.v1.endpoints import summary, team, updates

api_router = APIRouter()
api_router.include_router(team.router, tags=["team"])
api_router.include_router(updates.router, tags=["updates"])
api_router.include_router(summary.router, tags=["summary"])
