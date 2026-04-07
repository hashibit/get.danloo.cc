from fastapi import FastAPI
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from common.middleware import setup_middleware
from common.logging_config import setup_basic_logging

# Configure unified logging
logger = setup_basic_logging("process")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for FastAPI app"""
    # Startup
    logger.info("Starting Process Service...")

    # Start database job scheduler
    from process.services.database_job_scheduler import database_job_scheduler

    database_job_scheduler.start()
    logger.info("Database job scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down Process Service...")
    database_job_scheduler.stop()
    logger.info("Database job scheduler stopped")


# Initialize FastAPI app
app = FastAPI(
    title="Process API",
    description="Microservice providing content processing capabilities",
    version="1.0.0",
    lifespan=lifespan,
)

# Setup common middleware
setup_middleware(app, "process")

# Import routes
from process.controllers import api_controller

# Database tables are managed by Alembic migrations

# Include routers
app.include_router(
    api_controller.router, prefix="/api/v1/processing", tags=["processing"]
)


@app.get("/")
async def root():
    return {"message": "Welcome to Process API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
