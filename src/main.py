# src/main.py
from fastapi import FastAPI
from src.core.config import settings
from src.core.database import Base, engine
from src.core.task_queue import task_queue
from src.project.chapter_router import router as chapter_router
from src.project.router import router as project_router
from src.project.part_router import router as part_router
from src.crew.router import router as crew_router

# NEW IMPORTS for Rate Limiter
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis # Use async Redis client

# NEW: Import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

# NEW IMPORT: Import the logging configuration and Python's logging module
import logging
from src.core.logging import configure_logging

# Configure logging as early as possible
configure_logging()
logger = logging.getLogger(__name__) # Get a logger instance for this module

app = FastAPI(title="Scriptorium-Engine", version=settings.APP_VERSION)

# NEW: CORS Configuration
# Use settings.CORS_ORIGINS from config.py
origins = settings.CORS_ORIGINS.split(',') # Split the comma-separated string from settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup initiated.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema creation/check completed.")
    
    task_queue.configure(settings.REDIS_URL)
    await task_queue.connect()
    logger.info("Task queue connected to Redis.")

    redis_client = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_client)
    logger.info("⚡ FastAPILimiter initialized.")
    logger.info("Application startup complete.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown initiated.")
    await task_queue.close()
    await FastAPILimiter.close()
    logger.info("🔌 FastAPILimiter closed.")
    logger.info("Application shutdown complete.")


app.include_router(project_router)
app.include_router(chapter_router)
app.include_router(part_router)
app.include_router(crew_router)

@app.get("/", tags=["Health Check"])
async def health_check():
    logger.debug("Health check requested.") # Example of debug logging
    return {"status": "ok", "version": settings.APP_VERSION}