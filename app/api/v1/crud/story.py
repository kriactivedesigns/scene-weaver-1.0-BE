from typing import List
from sqlalchemy.orm import Session
from .... import models, schemas
import uuid
import markdown2

# Story Crud functions
def crate_or_update_story_for_project(db: Session, story: schemas.StoryCreate, project_id: uuid.UUID):
    """
    Finds the story for the project. If it exists, updates it. 
    If not, creates a new one.
    """

    html_content = markdown2.markdown(story.content)
    
    existing_story = get_story_for_project(db=db, project_id=project_id)
    if existing_story:
        # Story exists, so update its content and title
        existing_story.title = story.title
        existing_story.content = html_content
        db.commit()
        db.refresh(existing_story)
        return existing_story
    else:
        # Story does not exist, create a new one
        new_story = models.Story(
            projectId=project_id,
            title=story.title,
            content=html_content
        )
        db.add(new_story)
        db.commit()
        db.refresh(new_story)
        return new_story
    
def get_story_for_project(db: Session, project_id: uuid.UUID):
    """Fetches the single story associated with a project."""
    return db.query(models.Story).filter(models.Story.projectId == project_id).first()

def get_story(db: Session, story_id: uuid.UUID):
    """
    Retrieves a single story by its ID.
    """
    return db.query(models.Story).filter(models.Story.id == story_id).first()

def update_story(db: Session, story_id: uuid.UUID, story: schemas.StoryContentUpdate):
    """
    Updates a story's attributes.
    """
    db_story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if db_story:
        # Use exclude_unset=True for efficient PATCH-like updates
        update_data = story.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_story, key, value)
        db.commit()
        db.refresh(db_story)
    return db_story

def delete_story(db: Session, story_id: uuid.UUID) -> bool:
    """
    Deletes a story from the database. Returns True on success, False if not found.
    """
    db_story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if db_story:
        db.delete(db_story)
        db.commit()
        return True
    return False

def get_storythreads_for_project(db: Session, project_id: uuid.UUID) -> List[models.StoryThread]:
    """Retrieves all story threads for a project, ordered correctly."""
    return db.query(models.StoryThread).filter(models.StoryThread.projectId == project_id).order_by(models.StoryThread.order).all()

def get_characters_for_project(db: Session, project_id: uuid.UUID) -> List[models.Character]:
    """Retrieves all characters for a project."""
    # Assuming you have a 'Character' model defined
    return db.query(models.Character).filter(models.Character.projectId == project_id).all()

def get_worlds_for_project(db: Session, project_id: uuid.UUID) -> List[models.World]:
    """Retrieves all worlds for a project."""
    # Assuming you have a 'World' model defined
    return db.query(models.World).filter(models.World.projectId == project_id).all()
