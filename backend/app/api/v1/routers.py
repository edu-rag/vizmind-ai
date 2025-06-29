from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth_ep, maps_ep

api_router_v1 = APIRouter()
api_router_v1.include_router(auth_ep.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(maps_ep.router, prefix="/maps", tags=["Maps"])

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your allowed origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router_v1, prefix="/api/v1")
