import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .api.v1.endpoints import projects, worlds, characters, storythread, story, screenplay, storyboard, animatics, auth # Import projects router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

# Set specific log levels for different modules
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Reduce SQLAlchemy verbosity
logging.getLogger("uvicorn").setLevel(logging.INFO)

# This line creates all the database tables based on the SQLAlchemy Models
# For Production environment, we will want to manage this with migrations (Alembic).
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="🎬 CausalSyntax SceneWeaver API",
    description="""
    ## SceneWeaver AI-Powered Story Creation Platform
    
    Welcome to the SceneWeaver API - a comprehensive backend service for AI-powered storytelling and content creation.
    
    ### Features:
    * 📚 **Project Management** - Organize your creative projects
    * 🌍 **World Building** - Create immersive story worlds
    * 👥 **Character Development** - Design compelling characters
    * 🧵 **Story Threading** - Weave narrative threads together
    * 📖 **Story Generation** - AI-powered story creation
    * 🎭 **Screenplay Writing** - Transform stories into screenplays
    * 🖼️ **Storyboard Creation** - Generate visual storyboards
    * 🎞️ **Animatics Production** - Create animated sequences
    
    ### AI Providers:
    * **Vertex AI** - Production-grade AI services
    * **Local Mock** - Development and testing
    
    ### Storage Options:
    * **Cloudflare R2** - Distributed cloud storage
    * **Google Cloud Storage** - Enterprise cloud storage
    * **Local Storage** - Development filesystem
    
    ---
    
    **🚀 Ready to create amazing stories with AI assistance!**
    """,
    version="1.0.0-beta",
    contact={
        "name": "CausalSyntax Inc.",
        "url": "https://www.causalsyntax.com",
        "email": "support@causalsyntax.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://www.causalsyntax.com/license"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    tags_metadata=[
        {
            "name": "Projects",
            "description": "Manage creative projects and their metadata"
        },
        {
            "name": "Worlds", 
            "description": "Create and manage story worlds and settings"
        },
        {
            "name": "Characters",
            "description": "Design and develop story characters"
        },
        {
            "name": "Story Thread",
            "description": "Manage narrative threads and plot points"
        },
        {
            "name": "Story",
            "description": "AI-powered story generation and management"
        },
        {
            "name": "Screenplay",
            "description": "Convert stories into screenplay format"
        },
        {
            "name": "Storyboard",
            "description": "Generate visual storyboards from scenes"
        },
        {
            "name": "Animatics",
            "description": "Create animated sequences and videos"
        },
        {
            "name": "Authentication",
            "description": "User authentication and authorization"
        }
    ]
)

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

# Include the router for Storyboard Images 
app.include_router(
    storyboard.router,
    prefix="/api/v1",
    tags=["Storyboard"]
)

# Include the router for Animatics Scenes
app.include_router(
    animatics.router,
    prefix="/api/v1",
    tags=["Animatics"]
)

# Include the router for Authentication
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

@app.get("/")
async def root():
    """
    Root endpoint for the API.
    """
    return { "message": "Welcome to the CausalSyntax SceneWeaver API"}