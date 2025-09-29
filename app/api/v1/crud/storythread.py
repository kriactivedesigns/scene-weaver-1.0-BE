from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .... import models, schemas
import uuid
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# StoryThread CRUD functions
def get_storythread(db: Session, storythread_id: uuid.UUID) -> Optional[models.StoryThread]:
    """Get a single story thread by ID."""
    return db.query(models.StoryThread).filter(models.StoryThread.id == storythread_id).first()

def get_storythread_by_project(db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[models.StoryThread]:
    """Get all story threads for a project with pagination, ordered by sequence."""
    return db.query(models.StoryThread).filter(
        models.StoryThread.projectId == project_id
    ).order_by(
        models.StoryThread.order
    ).offset(skip).limit(limit).all()

def create_storythread(db: Session, storythread: schemas.StoryThreadCreate, project_id: uuid.UUID) -> models.StoryThread:
    """
    Create a new story thread for a project.
    
    Args:
        db: Database session
        storythread: Story thread data to create
        project_id: UUID of the project to add the story thread to
        
    Returns:
        The created story thread
        
    Raises:
        ValueError: If project is not found or validation fails
        SQLAlchemyError: If database operation fails
    """
    try:
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

def update_storythread(db: Session, storythread_id: uuid.UUID, storythread: schemas.StoryThreadUpdate) -> Optional[models.StoryThread]:
    """
    Update an existing story thread.
    
    Args:
        db: Database session
        storythread_id: UUID of the story thread to update
        storythread: Updated story thread data
        
    Returns:
        The updated story thread or None if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
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

def delete_storythread(db: Session, storythread_id: uuid.UUID) -> bool:
    """
    Delete a story thread from the database.
    
    Args:
        db: Database session
        storythread_id: UUID of the story thread to delete
        
    Returns:
        True on success, False if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
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
