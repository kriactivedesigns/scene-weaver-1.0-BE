from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from .... import models, schemas
from ....services.user_context import UserContextService
import uuid
import logging
import markdown2

logger = logging.getLogger(__name__)

# Story CRUD functions
def create_or_update_story_for_project(db: Session, story: schemas.StoryCreate, project_id: uuid.UUID, user_context: UserContextService) -> models.Story:
    """
    Finds the story for the project. If it exists, updates it. 
    If not, creates a new one.
    
    Args:
        db: Database session
        story: Story data to create or update
        project_id: UUID of the project
        user_context: User context for validation
        
    Returns:
        The created or updated story
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user owns the project
        if not user_context.user_owns_project(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
        # Validate input
        if not story.content or not story.content.strip():
            raise ValueError("Story content cannot be empty")
        
        # Convert markdown to HTML
        html_content = markdown2.markdown(story.content)
        
        existing_story = get_story_for_project(db=db, project_id=project_id)
        if existing_story:
            # Story exists, so update its content and title
            logger.info(f"Updating existing story for project: {project_id}")
            existing_story.title = story.title
            existing_story.content = html_content
            existing_story.version += 1  # Increment version on update
            db.commit()
            db.refresh(existing_story)
            logger.info(f"Successfully updated story for project: {project_id}")
            return existing_story
        else:
            # Story does not exist, create a new one
            logger.info(f"Creating new story for project: {project_id}")
            new_story = models.Story(
                projectId=project_id,
                title=story.title,
                content=html_content
            )
            db.add(new_story)
            db.commit()
            db.refresh(new_story)
            logger.info(f"Successfully created story for project: {project_id}")
            return new_story
            
    except ValueError:
        raise  # Re-raise validation errors
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating/updating story for project {project_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating/updating story for project {project_id}: {str(e)}")
        raise
    
def get_story_for_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> Optional[models.Story]:
    """Fetches the single story associated with a project with user validation."""
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return db.query(models.Story).filter(models.Story.projectId == project_id).first()

def get_story(db: Session, story_id: uuid.UUID, user_context: UserContextService) -> Optional[models.Story]:
    """
    Retrieves a single story by its ID with user validation.
    """
    # Validate user can access this story
    if not user_context.user_can_access_entity_by_project(story_id, models.Story, 'projectId'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
    
    return db.query(models.Story).filter(models.Story.id == story_id).first()

def update_story(db: Session, story_id: uuid.UUID, story: schemas.StoryContentUpdate, user_context: UserContextService) -> Optional[models.Story]:
    """
    Updates a story's attributes with user validation.
    
    Args:
        db: Database session
        story_id: UUID of the story to update
        story: Updated story data
        user_context: User context for validation
        
    Returns:
        The updated story or None if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user can access this story
        if not user_context.user_can_access_entity_by_project(story_id, models.Story, 'projectId'):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
        
        db_story = db.query(models.Story).filter(models.Story.id == story_id).first()
        if db_story:
            # Use exclude_unset=True for efficient PATCH-like updates
            update_data = story.model_dump(exclude_unset=True)
            
            # Convert content to HTML if it's being updated
            if 'content' in update_data and update_data['content']:
                update_data['content'] = markdown2.markdown(update_data['content'])
            
            # If we're updating content or title, increment version
            if update_data:
                db_story.version += 1
            
            for key, value in update_data.items():
                setattr(db_story, key, value)
            db.commit()
            db.refresh(db_story)
            logger.info(f"Successfully updated story: {story_id}")
        return db_story
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating story {story_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating story {story_id}: {str(e)}")
        raise

def delete_story(db: Session, story_id: uuid.UUID, user_context: UserContextService) -> bool:
    """
    Deletes a story from the database.
    
    Args:
        db: Database session
        story_id: UUID of the story to delete
        user_context: User context for validation
        
    Returns:
        True on success, False if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user can access this story
        if not user_context.user_can_access_entity_by_project(story_id, models.Story, 'projectId'):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story not found")
        
        db_story = db.query(models.Story).filter(models.Story.id == story_id).first()
        if db_story:
            logger.info(f"Deleting story: {story_id}")
            db.delete(db_story)
            db.commit()
            logger.info(f"Successfully deleted story: {story_id}")
            return True
        else:
            logger.warning(f"Story not found for deletion: {story_id}")
            return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting story {story_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting story {story_id}: {str(e)}")
        raise

def get_storythreads_for_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> List[models.StoryThread]:
    """Retrieves all story threads for a project, ordered correctly with user validation."""
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return db.query(models.StoryThread).filter(models.StoryThread.projectId == project_id).order_by(models.StoryThread.order).all()

def get_characters_for_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> List[models.Character]:
    """Retrieves all characters for a project with user validation."""
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Assuming you have a 'Character' model defined
    return db.query(models.Character).filter(models.Character.projectId == project_id).all()

def get_worlds_for_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> List[models.World]:
    """Retrieves all worlds for a project with user validation."""
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Assuming you have a 'World' model defined
    return db.query(models.World).filter(models.World.projectId == project_id).all()
