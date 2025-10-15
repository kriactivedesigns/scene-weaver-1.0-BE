from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from bs4 import BeautifulSoup
from .... import models, schemas
from ....services.user_context import UserContextService
import uuid
from ....services.storage import storage_provider
from ....services.ai_services import generative_services
from ....services.ai_services.prompt_builder import build_storyboard_prompt
import logging

logger = logging.getLogger(__name__)

# Storyboard Crud functions
async def create_storyboard_for_scene(db: Session, project_id: uuid.UUID, scene_id: uuid.UUID, user_context: UserContextService) -> models.StoryboardImage:
    """
    Orchestrates the asynchronous creation of a single storyboard image,
    uploading the final asset to Google Cloud Storage.
    """
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    scene = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    if not scene:
        raise ValueError("Scene not found")

    # Get project to access visual style
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")

    # --- This section for gathering context and building the prompt remains the same ---
    soup = BeautifulSoup(scene.content or "", "html.parser")
    plain_text_scene = soup.get_text(separator=" ", strip=True)
    
    entities = generative_services.extract_entities_from_scene(plain_text_scene)
    character_names_lower = [name.lower() for name in entities.get("characters", [])]
    world_names_lower = [name.lower() for name in entities.get("worlds", [])]

    # Note: These paths are now GCS URLs, which is what the AI service expects.
    character_paths = [char.imagePath for char in db.query(models.Character).filter(
        models.Character.projectId == project_id,
        func.lower(models.Character.name).in_(character_names_lower)
    ).all()]
    world_paths = [world.imagePath for world in db.query(models.World).filter(
        models.World.projectId == project_id,
        func.lower(models.World.name).in_(world_names_lower)
    ).all()]

    # Build style-aware prompt using the project's visual style
    scene_description = f"Cinematic storyboard scene: {plain_text_scene}"
    
    # Use the project's visual style to build the prompt with proper styling
    if project.visualStyle:
        final_prompt = build_storyboard_prompt(scene_description, project.visualStyle)
        logger.info(f"Applied visual style '{project.visualStyle}' to storyboard generation")
    else:
        final_prompt = f"Cinematic storyboard image depicting: {plain_text_scene}"
        logger.warning(f"No visual style found for project {project_id}, using default prompt")

    # Await the async AI service call to get the image bytes
    image_bytes = await generative_services.generate_storyboard_image_from_references(final_prompt, character_paths, world_paths)
    if not image_bytes:
        raise IOError("AI service failed to generate storyboard image bytes.")

    # --- This section is updated to use GCS instead of local files ---
    db_storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.sceneId == scene_id).first()

    if db_storyboard:
        # If storyboard exists, overwrite the image in storage
        try:
            destination_blob = f"storyboards/{db_storyboard.id}.png"
            public_url = storage_provider.upload_file(
                file_bytes=image_bytes,
                destination_blob_name=destination_blob,
                content_type="image/png"
            )
            
            if public_url:
                db_storyboard.prompt = final_prompt
                db_storyboard.version += 1
                logger.info(f"Updated storyboard image for scene {scene_id}: {db_storyboard.id}")
            else:
                raise IOError(f"Failed to upload updated storyboard image to storage for scene {scene_id}")
        except Exception as e:
            logger.error(f"Failed to update storyboard for scene {scene_id}: {str(e)}")
            raise
    else:
        # If new, create the storyboard record
        try:
            storyboard_id = uuid.uuid4()
            destination_blob = f"storyboards/{storyboard_id}.png"
            public_url = storage_provider.upload_file(
                file_bytes=image_bytes,
                destination_blob_name=destination_blob,
                content_type="image/png"
            )

            if not public_url:
                raise IOError(f"Failed to upload initial storyboard image to storage for scene {scene_id}")

            db_storyboard = models.StoryboardImage(
                id=storyboard_id,
                projectId=project_id,
                sceneId=scene_id,
                aspectRatio="16:9",
                prompt=final_prompt,
                imagePath=public_url # Store the public storage URL
            )
            db.add(db_storyboard)
            logger.info(f"Created new storyboard for scene {scene_id}: {storyboard_id}")
        except Exception as e:
            logger.error(f"Failed to create storyboard for scene {scene_id}: {str(e)}")
            raise

    db.commit()
    db.refresh(db_storyboard)
    return db_storyboard

def get_storyboards_by_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> List[models.StoryboardImage]:
    """
    Retrieves all storyboard images for a given project, ordered by the scene number.
    """
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return db.query(models.StoryboardImage)\
        .join(models.ScreenplayScene, models.StoryboardImage.sceneId == models.ScreenplayScene.id)\
        .filter(models.StoryboardImage.projectId == project_id)\
        .order_by(models.ScreenplayScene.sceneNumber)\
        .all()

def get_storyboard_by_id(db: Session, storyboard_id: uuid.UUID, user_context: UserContextService) -> Optional[models.StoryboardImage]:
    """
    Retrieves a specific storyboard by its ID with user validation.
    
    Args:
        db: Database session
        storyboard_id: UUID of the storyboard to retrieve
        user_context: User context for validation
        
    Returns:
        Storyboard image model if found, None otherwise
        
    Raises:
        Exception: If database query fails
    """
    try:
        # Validate user can access this storyboard
        if not user_context.user_can_access_entity_by_project(storyboard_id, models.StoryboardImage, 'projectId'):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storyboard not found")
        
        logger.debug(f"Retrieving storyboard: {storyboard_id}")
        
        storyboard = db.query(models.StoryboardImage).filter(
            models.StoryboardImage.id == storyboard_id
        ).first()
        
        if storyboard:
            logger.debug(f"Found storyboard: {storyboard_id}")
        else:
            logger.debug(f"Storyboard not found: {storyboard_id}")
            
        return storyboard
    except Exception as e:
        logger.error(f"Failed to retrieve storyboard {storyboard_id}: {str(e)}")
        raise


def delete_storyboard(db: Session, storyboard_id: uuid.UUID, user_context: UserContextService) -> bool:
    """
    Finds a storyboard, deletes its image from storage, and then deletes the DB record.
    
    Args:
        db: Database session
        storyboard_id: UUID of the storyboard to delete
        user_context: User context for validation
        
    Returns:
        True if deleted successfully, False if not found
        
    Raises:
        Exception: If deletion fails
    """
    try:
        # Validate user can access this storyboard
        if not user_context.user_can_access_entity_by_project(storyboard_id, models.StoryboardImage, 'projectId'):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Storyboard not found")
        
        logger.info(f"Deleting storyboard: {storyboard_id}")
        
        db_storyboard = db.query(models.StoryboardImage).filter(
            models.StoryboardImage.id == storyboard_id
        ).first()
        
        if not db_storyboard:
            logger.warning(f"Storyboard not found for deletion: {storyboard_id}")
            return False

        # Delete the image from storage if it exists
        if db_storyboard.imagePath:
            try:
                # Construct the blob name to delete from storage
                blob_name = f"storyboards/{storyboard_id}.png"
                storage_provider.delete_file(blob_name)
                logger.debug(f"Deleted storyboard image from storage: {blob_name}")
            except Exception as e:
                logger.warning(f"Could not delete storage file for storyboard {storyboard_id}: {str(e)}")

        # Delete the database record
        db.delete(db_storyboard)
        db.commit()
        
        logger.info(f"Successfully deleted storyboard: {storyboard_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete storyboard {storyboard_id}: {str(e)}")
        db.rollback()
        raise
