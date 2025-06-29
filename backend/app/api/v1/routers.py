from fastapi import APIRouter
from app.api.v1.endpoints import auth_ep, maps_ep

api_router_v1 = APIRouter()
api_router_v1.include_router(auth_ep.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(maps_ep.router, prefix="/maps", tags=["Maps"])
