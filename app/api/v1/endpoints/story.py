from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
import uuid

from .... import crud, schemas
from ....database import SessionLocal
from .... import ai_srevices

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/generate-story", response_model=schemas.Story, status_code=status.HTTP_201_CREATED)
def generate_story(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Generates a new story. If a story already exists for this project,
    it will be overwritten with the new content.
    """
    project = crud.get_project(db, project_id=project_id) # Verify project exists
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    threads = crud.get_storythreads_for_project(db=db, project_id=project_id)
    characters = crud.get_characters_for_project(db=db, project_id=project_id)
    worlds = crud.get_worlds_for_project(db=db, project_id=project_id)

    project_context = {
        "project": project,
        "threads": threads,
        "characters": characters,
        "worlds": worlds
    }
    
    try:
        # Call the AI service to do the heavy lifting
        generated_story = ai_srevices.generate_story_from_project_context(project_context=project_context)

        if not generate_story:
            raise HTTPException(status_code=500, detail="AI Service returned an empty story")
        
        # Simple logic to extract a title from the first line of the Markdown
        title = project.projectName
        
        story_data = schemas.StoryCreate(title=title, content=generated_story)
        db_story = crud.crate_or_update_story_for_project(db=db, story=story_data, project_id=project_id)
        return db_story
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate story: {str(e)}")
    
@router.get("/projects/{project_id}/story", response_model=schemas.Story)
def read_story_of_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve the single story for a specific project."""
    db_story = crud.get_story_for_project(db=db, project_id=project_id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return db_story

@router.get("/stories/{story_id}", response_model=schemas.Story)
def read_story(story_id: uuid.UUID, db: Session = Depends(get_db)):
    """Retrieve a single story by its ID."""
    db_story = crud.get_story(db, story_id=story_id)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return db_story

@router.put("/stories/{story_id}", response_model=schemas.Story)
def update_story(story_id: uuid.UUID, story: schemas.StoryContentUpdate, db: Session = Depends(get_db)):
    """Update a story's title or content."""
    db_story = crud.update_story(db=db, story_id=story_id, story=story)
    if db_story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return db_story

@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story(story_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a story by its ID."""
    was_deleted = crud.delete_story(db=db, story_id=story_id)
    if not was_deleted:
        raise HTTPException(status_code=404, detail="Story not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
