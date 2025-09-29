from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from typing import List
import uuid
from .... import schemas
from ....database import SessionLocal
from .... import ai_services
from ..crud.screenplay import create_screenplay_scenes_for_project, get_screenlay_scenes_for_project, add_new_scene_to_project, update_screenplay_scene, delete_scene_and_reorder
from ..crud.story import get_story_for_project

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/generate-screenplay", response_model=List[schemas.ScreenplayScene])
def generate_screenplay_route(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generates a full screenplay from the project's story, overwriting any
    existing scenes for this project.
    """
    # 1. Fetch the project's story
    story = get_story_for_project(db=db, project_id=project_id)
    if not story or not story.content:
        raise HTTPException(status_code=404, detail="A story with content must exist for this project before generating a screenplay.")
    
    # 2. Convert story's html to plain text
    soup = BeautifulSoup(story.content, "html.parser")
    plain_text_story = soup.get_text(separator='\\n', strip=True)
    
    # 3. Call the AI service to get scene data
    scenes_data = ai_services.generate_scenes_from_story(story_content=plain_text_story)
    if not scenes_data:
        raise HTTPException(status_code=500, detail="AI service failed to generate screenplay scenes.")
    
    # 4. Use Pydantic to validate the AI's output
    validated_scenes = [schemas.ScreenplaySceneCreate(**data) for data in scenes_data]
    
    # 5. Save the new scenes to the database
    new_scenes = create_screenplay_scenes_for_project(db=db, scenes=validated_scenes, project_id=project_id)
    return new_scenes

@router.post("/projects/{project_id}/screenplayscenes", response_model=schemas.ScreenplayScene, status_code=status.HTTP_201_CREATED)
def add_new_scene_route(project_id: uuid.UUID, scene_data: schemas.NewScreenplayScene, db: Session = Depends(get_db)):
    """
    Manually adds a new scene to the end of a project's screenplay.
    The sceneNumber is calculated automatically by the server.
    """
    # Call the CRUD function to handle the database logic
    new_scene = add_new_scene_to_project(db=db, scene_data=scene_data, project_id=project_id)
    return new_scene

@router.patch("/screenplayscenes/{scene_id}", response_model=schemas.ScreenplayScene)
def update_screenplay_scene_route(scene_id: uuid.UUID, scene_update: schemas.ScreenplaySceneUpdate, db: Session = Depends(get_db)):
    """
    Update a single screenplay scene's content, duration, or scene number.
    """
    db_scene = update_screenplay_scene(db=db, scene_id=scene_id, scene=scene_update)
    if db_scene is None:
        raise HTTPException(status_code=404, detail="Screenplay scene not found")
        
    return db_scene

@router.get("/projects/{project_id}/screenplay", response_model=List[schemas.ScreenplayScene])
def get_screenplay_route(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve all scenes for a project's screenplay."""
    return get_screenlay_scenes_for_project(db=db, project_id=project_id)

@router.delete("/screenplayscenes/{scene_id}", response_model=List[schemas.ScreenplayScene])
def delete_screenplay_scene_route(scene_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Deletes a screenplay scene and re-orders the remaining scenes.
    Returns the complete, updated list of scenes for the project.
    """
    updated_scenes = delete_scene_and_reorder(db=db, scene_id=scene_id)
    
    if updated_scenes is None:
        raise HTTPException(status_code=404, detail="Screenplay scene not found")
        
    return updated_scenes