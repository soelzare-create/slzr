"""DaranX API entrypoint.

Wires the presentation layer (routers) on top of the logic and data layers.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import activities, auth, inventory, parties, team, users
from app.config import settings
from app.database import Base, engine

# Import models so their tables are registered on Base before create_all.
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # For development we auto-create tables. In production use migrations.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=f"{settings.app_name} API",
    version=__version__,
    description="سیستم یکپارچه مدیریت فرآیند — «همه چیز سر جای خودش»",
    lifespan=lifespan,
)

# CORS — allow the React dev server to talk to the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(team.router)
app.include_router(parties.router)
app.include_router(activities.router)
app.include_router(inventory.router)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "app": settings.app_name,
        "version": __version__,
        "motto": "همه چیز سر جای خودش",
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
