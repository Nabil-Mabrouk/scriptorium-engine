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

app = FastAPI(title="Scriptorium-Engine", version=settings.APP_VERSION)

# NEW: CORS Configuration
origins = [
    "http://localhost:5173",  # This is the default port for Vite dev server
    # Add any other origins where your frontend might be hosted in development or production
    # e.g., "https://your.production.domain"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allows all headers
)

@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    task_queue.configure(settings.REDIS_URL)
    await task_queue.connect()

    # NEW: Initialize FastAPILimiter with Redis
    redis_client = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_client)
    print("⚡ FastAPILimiter initialized.")

@app.on_event("shutdown")
async def shutdown_event():
    await task_queue.close()
    # NEW: Close FastAPILimiter connections
    await FastAPILimiter.close()
    print("🔌 FastAPILimiter closed.")

app.include_router(project_router)
app.include_router(chapter_router)
# NEW: Include the new part_router
app.include_router(part_router)
app.include_router(crew_router)

@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}