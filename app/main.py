from fastapi import FastAPI
from . import models
from .database import engine
from .api.v1.endpoints import projects # Import projects router

# This line creates all the database tables based on the SQLAlchemy Models
# For Production environment, we will want to manage this with migrations (Alembic).
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CausalSyntax SceneWeaver API",
    description="Backend services for the SceneWeaver AI Application",
    version="0.1.0"
)

# Include the router for the projects endpoints
app.include_router(
    projects.router,
    prefix="/api/v1/projects",
    tags=["Projects"]
)

@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return { "message": "Welcome to the CausalSyntax SceneWeaver API"}