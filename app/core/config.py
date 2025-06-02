import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # LLM & Embeddings
    GROQ_API_KEY: str
    MODEL_NAME_FOR_EMBEDDING: str = "paraphrase-multilingual-mpnet-base-v2"
    LLM_MODEL_NAME_GROQ: str = "llama-3.3-70b-versatile"

    # Langsmith
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str

    # MongoDB
    MONGODB_URI: str
    MONGODB_DATABASE_NAME: str = "cmvs_project"
    MONGODB_USERS_COLLECTION: str = "users"
    MONGODB_CMVS_COLLECTION: str = "concept_maps_api_s3_auth"
    MONGODB_CHUNKS_COLLECTION: str = "chunk_embeddings"

    # S3
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str

    # JWT Authentication
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Google OAuth
    GOOGLE_CLIENT_ID: str

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # For Pydantic V2, case_sensitive = False is default for .env
        # For Pydantic V1 settings, you might need case_sensitive = True if your .env keys are uppercase


settings = Settings()

# Basic Logging Setup (can be more sophisticated)
import logging

logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Validate critical settings
if not settings.JWT_SECRET_KEY:
    logger.critical("JWT_SECRET_KEY not set. Authentication will fail.")
if not settings.GOOGLE_CLIENT_ID:
    logger.critical("GOOGLE_CLIENT_ID not set. Google Sign-In verification will fail.")
