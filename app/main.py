from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api_router import api_router
from app.db.session import Base, engine
from app.db import models  # noqa: F401  ensures tables are registered before create_all
from app.services.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


app = FastAPI(title="Ai agent gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
