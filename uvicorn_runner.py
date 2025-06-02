import uvicorn
from app.core.config import (
    settings,
)  # To potentially use settings for host/port if defined

if __name__ == "__main__":
    # You can get host/port from settings if you add them there
    # e.g., host = settings.APP_HOST, port = settings.APP_PORT
    host = "0.0.0.0"
    port = 8000
    reload = True  # Set to False in production or use environment variable

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
