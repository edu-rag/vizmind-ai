from fastapi import APIRouter
from app.api.v1.endpoints import auth_ep, concept_maps_ep

api_router_v1 = APIRouter()
api_router_v1.include_router(auth_ep.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(
    concept_maps_ep.router, prefix="/concept-maps", tags=["Concept Maps"]
)
