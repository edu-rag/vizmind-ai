import os
import uvicorn
from app.core.config import (
    settings,
)  # To potentially use settings for host/port if defined

if __name__ == "__main__":
    # Get host/port from environment or use defaults
    # Render sets PORT environment variable automatically
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    # Disable reload in production (when PORT is set by Render)
    reload = not bool(os.getenv("PORT"))

    # Check if LOG_LEVEL from settings should influence Uvicorn's log level
    log_level_uvicorn = settings.LOG_LEVEL.lower()

    print(
        f"Starting Uvicorn server on {host}:{port} with reload: {reload}, log-level: {log_level_uvicorn}"
    )
    uvicorn.run(
        "app.main:app",  # Path to your FastAPI app instance
        host=host,
        port=port,
        reload=reload,
        log_level=log_level_uvicorn,
    )
