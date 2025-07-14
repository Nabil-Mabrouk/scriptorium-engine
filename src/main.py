# src/main.py
from fastapi import FastAPI
from src.core.config import settings
from src.core.database import Base, engine
from src.core.task_queue import task_queue # <<< IMPORT OUR ABSTRACTION
from src.project.chapter_router import router as chapter_router
from src.project.router import router as project_router
from src.crew.router import router as crew_router

app = FastAPI(title="Scriptorium-Engine", version=settings.APP_VERSION)


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Configure and then connect the task queue
    task_queue.configure(settings.REDIS_URL)
    await task_queue.connect()

@app.on_event("shutdown")
async def shutdown_event():
    # Close the task queue connection
    await task_queue.close()

app.include_router(project_router)
app.include_router(chapter_router)
app.include_router(crew_router)

@app.get("/", tags=["Health Check"])
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}