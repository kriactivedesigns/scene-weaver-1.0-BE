from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .api.v1.endpoints import projects, worlds, characters, storythread, story, screenplay # Import projects router

# This line creates all the database tables based on the SQLAlchemy Models
# For Production environment, we will want to manage this with migrations (Alembic).
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CausalSyntax SceneWeaver API",
    description="Backend services for the SceneWeaver AI Application",
    version="0.1.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Define the list of allowed origins
# For development, this includes typical localhost port for frontend frameworks.
# We  must add the production domain before deploying
origins = [
    "http://localhost",
    "http://localhost:4200",
    "https://www.causalsyntax.com",
]

# Add the CORS middleware to the application.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include the router for the projects endpoints
app.include_router(
    projects.router,
    prefix="/api/v1/projects",
    tags=["Projects"]
)

# Include the router for Worlds
app.include_router(
    worlds.router,
    prefix="/api/v1",
    tags=["Worlds"]
)

# Include the router for Characters
app.include_router(
    characters.router,
    prefix="/api/v1",
    tags=["Characters"]
)

# Include the router for Story thread
app.include_router(
    storythread.router,
    prefix="/api/v1",
    tags=["Story Thread"]
)

# Include the router for Story 
app.include_router(
    story.router,
    prefix="/api/v1",
    tags=["Story"]
)

# Include the router for Screenplay Scene 
app.include_router(
    screenplay.router,
    prefix="/api/v1",
    tags=["Screenplay"]
)

@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return { "message": "Welcome to the CausalSyntax SceneWeaver API"}