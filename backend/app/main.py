"""
IndusIntel AI — FastAPI backend entrypoint.

Run locally:
    uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import health, products

# Create tables on startup (fine for SQLite/dev; use Alembic migrations in
# a real production Postgres deployment).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IndusIntel AI API",
    description="AI-Powered Product Intelligence for Industrial Commerce",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(products.router)


@app.get("/")
def root():
    return {"message": "IndusIntel AI API is running. See /docs for API documentation."}
