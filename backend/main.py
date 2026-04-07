from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from database import get_database
from common.api_models.user_model import UserCreate
from backend.services.user_service import UserService
from backend.services.tag_service import TagService, TagCreate
from common.middleware import setup_middleware
from common.logging_config import setup_basic_logging

# Configure unified logging
logger = setup_basic_logging("backend")

# Initialize FastAPI app
app = FastAPI(
    title="丹炉 (Danloo) API",
    description="AI-powered technical content extraction system",
    version="1.0.0",
)

# Setup common middleware
setup_middleware(app, "backend")

# Setup security middleware
from backend.middleware.security import create_security_middleware, create_material_upload_security_middleware
app.add_middleware(create_security_middleware)
app.add_middleware(create_material_upload_security_middleware)

# Database models are managed by Alembic migrations


def create_initial_user():
    """Create initial admin user if none exists"""
    try:
        db = next(get_database())
        user_service = UserService()

        # Check if any user exists
        existing_user = user_service.get_user_by_email(db, "admin@danloo.com")
        if existing_user:
            logger.info("Initial admin user already exists")
            return

        # Create initial admin user
        initial_user = UserCreate(
            email="admin@danloo.com", username="admin", password="Test123!@#"
        )

        created_user = user_service.create_user(db, initial_user)
        logger.info(
            f"Created initial admin user: {created_user.email} (ID: {created_user.id})"
        )

    except Exception as e:
        logger.error(f"Failed to create initial user: {str(e)}")
    finally:
        db.close()


def create_initial_tags():
    """Create initial tags if none exist"""
    try:
        db = next(get_database())
        tag_service = TagService()

        # Check if any tags exist
        existing_tags = tag_service.get_all_tags(db)
        if existing_tags:
            logger.info(f"Initial tags already exist ({len(existing_tags)} tags found)")
            return

        # Define initial tags
        initial_tags = [
            TagCreate(id="tag-1", name="General", color="#808080", description="General knowledge and information"),
            TagCreate(id="tag-2", name="Technology", color="#4A90E2", description="Technology-related content"),
            TagCreate(id="tag-3", name="Business", color="#7ED321", description="Business and entrepreneurship"),
            TagCreate(id="tag-4", name="Science", color="#F5A623", description="Scientific knowledge and research"),
            TagCreate(id="tag-5", name="Health", color="#BD10E0", description="Health and wellness information"),
            TagCreate(id="tag-6", name="Education", color="#B8E986", description="Educational content and learning"),
            TagCreate(id="tag-7", name="Finance", color="#50E3C2", description="Financial knowledge and advice"),
            TagCreate(id="tag-8", name="Personal", color="#D0021B", description="Personal development and growth"),
            TagCreate(id="gold", name="gold", color="#FFD700", description="高质量丹药，经过精心提炼"),
            TagCreate(id="public", name="public", color="#10B981", description="公开分享的丹药内容"),
            TagCreate(id="special", name="special", color="#3B82F6", description="具有特殊价值的丹药"),
            TagCreate(id="normal", name="normal", color="#6B7280", description="普通质量丹药"),
        ]

        # Create initial tags
        for tag_data in initial_tags:
            created_tag = tag_service.create_tag(db, tag_data)
            logger.info(f"Created initial tag: {created_tag.name} (ID: {created_tag.id})")

        logger.info(f"Created {len(initial_tags)} initial tags")

    except Exception as e:
        logger.error(f"Failed to create initial tags: {str(e)}")
    finally:
        db.close()


# Create initial data on startup
@app.on_event("startup")
async def startup_event():
    create_initial_user()
    create_initial_tags()
    
    # Start task scheduler
    from backend.scheduler import startup_scheduler
    await startup_scheduler()
    logger.info("Task scheduler started")


@app.on_event("shutdown")
async def shutdown_event():
    # Stop task scheduler
    from backend.scheduler import shutdown_scheduler
    await shutdown_scheduler()
    logger.info("Task scheduler stopped")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from backend.controllers import (
    user_controller,
    material_controller,
    pellet_controller,
    internal_controller,
    file_controller,
    job_controller,
    quota_controller,
)
from backend.controllers.admin import quota_controller as admin_quota_controller
from backend.controllers.admin import scheduler_controller as admin_scheduler_controller
from backend.controllers.admin import blacklist_controller as admin_blacklist_controller

# Include routers
app.include_router(user_controller.router, prefix="/api/v1/users", tags=["users"])
app.include_router(
    material_controller.router, prefix="/api/v1/materials", tags=["materials"]
)
app.include_router(pellet_controller.router, prefix="/api/v1/pellets", tags=["pellets"])
app.include_router(file_controller.router, prefix="/api/v1/files", tags=["files"])
app.include_router(job_controller.router, prefix="/api/v1", tags=["jobs"])
app.include_router(quota_controller.router, prefix="/api/v1/quota", tags=["quota"])
app.include_router(admin_quota_controller.router, prefix="/api/v1/admin/quota", tags=["admin-quota"])
app.include_router(admin_scheduler_controller.router, prefix="/api/v1/admin/scheduler", tags=["admin-scheduler"])
app.include_router(admin_blacklist_controller.router, prefix="/api/v1/admin/blacklist", tags=["admin-blacklist"])

# Internal API routes (for service-to-service communication)
app.include_router(
    internal_controller.router, prefix="/api/v1/internal", tags=["internal"]
)


@app.get("/")
async def root():
    return {"message": "Welcome to 丹炉 (Danloo) API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "hot_reload": "working_perfectly", "timestamp": "2025-09-03", "reload_dirs": "configured"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
