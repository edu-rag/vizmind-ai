# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings, logger
from app.api.v1.routers import api_router_v1
from app.db.mongodb_utils import init_mongodb, get_mongo_client
from app.services.s3_service import S3Service


@asynccontextmanager
async def lifespan(
    app_instance: FastAPI,
):  # Renamed app to app_instance to avoid conflict
    logger.info("Application startup...")
    init_mongodb()

    # S3 Service initialization
    s3_service = S3Service()
    app_instance.state.s3_service = s3_service  # Store the service instance
    if s3_service.is_configured():
        logger.info(
            "S3 service configured and client initialized successfully on startup."
        )
    else:
        logger.warning(
            "⚠️ S3 service not fully configured or client failed to initialize."
        )

    logger.info("LangGraph app initialized.")
    yield
    logger.info("Application shutdown...")
    mongo_cli = get_mongo_client()
    if mongo_cli:
        mongo_cli.close()
        logger.info("MongoDB connection closed.")


# FastAPI App Instance
app = FastAPI(
    title="CMVS API - Structured with JWT Auth",
    description="Concept Map Visual Synthesizer API. "
    "Authenticate by clicking the 'Authorize' button and pasting your JWT Bearer token.",
    version="1.1.0",  # Updated version
    lifespan=lifespan,
    # Define how security schemes are described in OpenAPI (for Swagger UI)
    openapi_components={
        "securitySchemes": {
            "BearerAuth": {  # This is a custom name for the scheme in OpenAPI doc
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",  # Helps clients understand it's a JWT
                "description": "Enter your JWT in the format: Bearer &lt;token&gt;",
            }
        }
    },
    # Note: You might not need to explicitly add security=[{"BearerAuth": []}] to each
    # route if FastAPI correctly infers it from the HTTPBearer dependency.
    # However, if it doesn't show the lock icon, you might add it to the router:
    # api_router_v1 = APIRouter(security=[{"BearerAuth": []}])
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include the v1 API router
app.include_router(api_router_v1, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to the Secure CMVS API (JWT Auth)!"}
