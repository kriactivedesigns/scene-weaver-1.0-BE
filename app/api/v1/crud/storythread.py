from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from .... import models, schemas
from ....services.user_context import UserContextService
import uuid
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# StoryThread CRUD functions
def get_storythread(db: Session, storythread_id: uuid.UUID, user_context: UserContextService) -> Optional[models.StoryThread]:
    """Get a single story thread by ID with user validation."""
    # Validate user can access this story thread
    if not user_context.user_can_access_entity_by_project(storythread_id, models.StoryThread, 'projectId'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story thread not found")
    
    return db.query(models.StoryThread).filter(models.StoryThread.id == storythread_id).first()

def get_storythread_by_project(db: Session, project_id: uuid.UUID, user_context: UserContextService, skip: int = 0, limit: int = 100) -> List[models.StoryThread]:
    """Get all story threads for a project with pagination, ordered by sequence and user validation."""
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return db.query(models.StoryThread).filter(
        models.StoryThread.projectId == project_id
    ).order_by(
        models.StoryThread.order
    ).offset(skip).limit(limit).all()

def create_storythread(db: Session, storythread: schemas.StoryThreadCreate, project_id: uuid.UUID, user_context: UserContextService) -> models.StoryThread:
    """
    Create a new story thread for a project.
    
    Args:
        db: Database session
        storythread: Story thread data to create
        project_id: UUID of the project to add the story thread to
        user_context: User context for validation
        
    Returns:
        The created story thread
        
    Raises:
        ValueError: If project is not found or validation fails
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user owns the project
        if not user_context.user_owns_project(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
        # Verify project exists
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        db_storythread = models.StoryThread(projectId=project_id, **storythread.model_dump())
        db.add(db_storythread)
        db.commit()
        db.refresh(db_storythread)
        
        logger.info(f"Successfully created story thread for project {project_id}: {db_storythread.id}")
        return db_storythread
        
    except ValueError:
        db.rollback()
        raise  # Re-raise validation errors
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating story thread: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating story thread: {str(e)}")
        raise

def update_storythread(db: Session, storythread_id: uuid.UUID, storythread: schemas.StoryThreadUpdate, user_context: UserContextService) -> Optional[models.StoryThread]:
    """
    Update an existing story thread.
    
    Args:
        db: Database session
        storythread_id: UUID of the story thread to update
        storythread: Updated story thread data
        user_context: User context for validation
        
    Returns:
        The updated story thread or None if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user can access this story thread
        if not user_context.user_can_access_entity_by_project(storythread_id, models.StoryThread, 'projectId'):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story thread not found")
        
        db_storythread = db.query(models.StoryThread).filter(models.StoryThread.id == storythread_id).first()
        if db_storythread:
            update_data = storythread.model_dump(exclude_unset=True)
            
            # Validate content if being updated
            if 'content' in update_data and not update_data['content'].strip():
                raise ValueError("Story thread content cannot be empty")
            
            for key, value in update_data.items():
                setattr(db_storythread, key, value)
            db.commit()
            db.refresh(db_storythread)
            logger.info(f"Successfully updated story thread: {storythread_id}")
        return db_storythread
    except ValueError:
        db.rollback()
        raise  # Re-raise validation errors
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating story thread {storythread_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating story thread {storythread_id}: {str(e)}")
        raise

def delete_storythread(db: Session, storythread_id: uuid.UUID, user_context: UserContextService) -> bool:
    """
    Delete a story thread from the database.
    
    Args:
        db: Database session
        storythread_id: UUID of the story thread to delete
        user_context: User context for validation
        
    Returns:
        True on success, False if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user can access this story thread
        if not user_context.user_can_access_entity_by_project(storythread_id, models.StoryThread, 'projectId'):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Story thread not found")
        
        db_storythread = db.query(models.StoryThread).filter(models.StoryThread.id == storythread_id).first()
        if db_storythread:
            logger.info(f"Deleting story thread: {storythread_id}")
            db.delete(db_storythread)
            db.commit()
            logger.info(f"Successfully deleted story thread: {storythread_id}")
            return True
        else:
            logger.warning(f"Story thread not found for deletion: {storythread_id}")
            return False
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting story thread {storythread_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting story thread {storythread_id}: {str(e)}")
        raise
