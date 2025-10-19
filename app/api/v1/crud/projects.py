from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from .... import models, schemas
from ....services.user_context import UserContextService
import uuid
import logging
from typing import List, Optional
from .characters import delete_character
from .worlds import delete_world
from .storyboard import delete_storyboard
from .animatics import delete_animatics

logger = logging.getLogger(__name__)

# Project CRUD functions
def get_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> Optional[models.Project]:
    """Get a single project by ID with user validation."""
    # Validate user owns this project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, user_context: UserContextService, skip: int = 0, limit: int = 100) -> List[models.Project]:
    """Get all projects for the current user with pagination."""
    return db.query(models.Project).filter(models.Project.owner_id == user_context.get_user_id()).offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate, user_context: UserContextService) -> models.Project:
    """Create a new project with user ownership."""
    try:
        # Prepare project data and assign user ownership
        project_data = project.model_dump()
        project_data = user_context.assign_user_ownership(project_data)
        
        # Set default values
        project_data['aspectRatio'] = project_data.get('aspectRatio') or "16:9"
        project_data['visualStyle'] = project_data.get('visualStyle') or "Monochromatic B&W Dynamic Sketch"
        
        # Create a SQLAlchemy model instance
        db_project = models.Project(**project_data)
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        logger.info(f"Successfully created project: {db_project.projectName} ({db_project.id})")
        return db_project
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating project {project.projectName}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating project {project.projectName}: {str(e)}")
        raise

def update_project(db: Session, project_id: uuid.UUID, project_update: schemas.ProjectUpdate, user_context: UserContextService) -> Optional[models.Project]:
    """Update an existing project with partial data and user validation."""
    try:
        # Validate user owns this project
        if not user_context.user_owns_project(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
        db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not db_project:
            logger.warning(f"Project not found for update: {project_id}")
            return None
            
        # Update only the fields that are provided (not None)
        update_data = project_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_project, field):
                setattr(db_project, field, value)
                
        db.commit()
        db.refresh(db_project)
        logger.info(f"Successfully updated project: {db_project.projectName} ({db_project.id})")
        return db_project
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating project {project_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating project {project_id}: {str(e)}")
        raise

def delete_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> bool:
    """
    Deletes a project and all of its associated entities and cloud assets.
    This function performs a full cascade delete at the application level.
    
    Args:
        db: Database session
        project_id: UUID of the project to delete
        user_context: User context for validation
        
    Returns:
        True if deletion was successful, False if project not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user owns this project
        if not user_context.user_owns_project(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
        project_to_delete = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project_to_delete:
            logger.warning(f"Project not found for deletion: {project_id}")
            return False

        logger.info(f"Starting deletion for project: {project_to_delete.projectName} ({project_id})")

        # Delete Characters
        characters = db.query(models.Character).filter(models.Character.projectId == project_id).all()
        for char in characters:
            logger.debug(f"Deleting character: {char.name}")
            delete_character(db=db, character_id=char.id)

        # Delete Worlds
        worlds = db.query(models.World).filter(models.World.projectId == project_id).all()
        for world in worlds:
            logger.debug(f"Deleting world: {world.name}")
            delete_world(db=db, world_id=world.id)

        # Delete Storyboards
        storyboards = db.query(models.StoryboardImage).filter(models.StoryboardImage.projectId == project_id).all()
        for sb in storyboards:
            logger.debug(f"Deleting storyboard for scene: {sb.sceneId}")
            delete_storyboard(db=db, storyboard_id=sb.id)

        # Delete Animatics
        animatics = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.projectId == project_id).all()
        for anim in animatics:
            logger.debug(f"Deleting animatic for scene: {anim.sceneId}")
            delete_animatics(db=db, animatics_id=anim.id)

        # Delete simple database records that have no cloud assets
        logger.debug("Deleting story threads and screenplay scenes...")
        db.query(models.StoryThread).filter(models.StoryThread.projectId == project_id).delete()
        db.query(models.ScreenplayScene).filter(models.ScreenplayScene.projectId == project_id).delete()
        db.query(models.Story).filter(models.Story.projectId == project_id).delete()

        # Finally, delete the project record itself
        logger.debug("Deleting project record...")
        db.delete(project_to_delete)

        # Commit all changes in a single transaction
        db.commit()
        logger.info(f"Successfully deleted project {project_id}")
        
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting project {project_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting project {project_id}: {str(e)}")
        raise
