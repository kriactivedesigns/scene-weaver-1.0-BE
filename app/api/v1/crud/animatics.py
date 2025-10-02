from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from bs4 import BeautifulSoup
from .... import models, schemas
from ....services.user_context import UserContextService
import uuid
from ....services.storage import storage_provider
from ....services.ai_services import generative_services
import logging

logger = logging.getLogger(__name__)

# Animatics Crud functions
async def create_animatics_for_scene(db: Session, project_id: uuid.UUID, scene_id: uuid.UUID, user_context: UserContextService) -> models.AnimaticsScene:
    """
    Orchestrates creating or updating an animatic video for a single scene,
    uploading the final asset to storage.
    
    Args:
        db: Database session
        project_id: UUID of the project
        scene_id: UUID of the scene to create animatic for
        user_context: User context for validation
        
    Returns:
        Created or updated animatic scene model
        
    Raises:
        ValueError: If scene or storyboard not found
        IOError: If AI service or storage operation fails
        Exception: If database operation fails
    """
    try:
        # Validate user owns the project
        if not user_context.user_owns_project(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        
        logger.info(f"Creating animatics for scene {scene_id} in project {project_id}")
        
        scene = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
        if not scene:
            logger.error(f"Scene not found: {scene_id}")
            raise ValueError("Scene not found")
        
        storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.sceneId == scene_id).first()
        if not storyboard:
            logger.error(f"Storyboard image for scene {scene_id} not found")
            raise ValueError("Storyboard image for scene not found. Generate storyboard first.")

        # --- This section for gathering context and building the prompt ---
        soup = BeautifulSoup(scene.content or "", "html.parser")
        plain_text_prompt = soup.get_text(separator=" ", strip=True)
        if not plain_text_prompt.strip():
            plain_text_prompt = "A cinematic, animated scene."
            logger.warning(f"Empty scene content for {scene_id}, using default prompt")

        # These paths are now storage URLs, which the AI service can access if needed.
        character_image_paths = [char.imagePath for char in db.query(models.Character).filter(models.Character.projectId == project_id).all()]
        world_image_paths = [world.imagePath for world in db.query(models.World).filter(models.World.projectId == project_id).all()]
        
        logger.debug(f"Found {len(character_image_paths)} character images and {len(world_image_paths)} world images for scene {scene_id}")

        # Await the async AI service call to get the video bytes
        logger.debug(f"Generating animatics video for scene {scene_id}")
        video_bytes = await generative_services.generate_animatics_video_from_references(
            prompt=plain_text_prompt,
            storyboard_image_path=storyboard.imagePath,
            character_image_paths=character_image_paths,
            world_image_paths=world_image_paths,
            duration_in_seconds=scene.duration
        )
        if not video_bytes:
            logger.error(f"AI service failed to generate animatics video for scene {scene_id}")
            raise IOError("AI service failed to generate animatic video bytes.")

        # --- This section is updated to use storage abstraction for video storage ---
        db_animatic = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.sceneId == scene_id).first()

        if db_animatic:
            # If animatic exists, overwrite the video in storage
            destination_blob = f"animatics/{db_animatic.id}.mp4"
            public_url = storage_provider.upload_file(
                file_bytes=video_bytes,
                destination_blob_name=destination_blob,
                content_type='video/mp4'
            )
            
            if public_url:
                db_animatic.version += 1
                logger.info(f"Updated animatics video for scene {scene_id}: {db_animatic.id}")
            else:
                raise IOError(f"Failed to upload updated animatic to storage for scene {scene_id}")
        else:
            # If new, create the animatic record
            animatics_id = uuid.uuid4()
            destination_blob = f"animatics/{animatics_id}.mp4"
            public_url = storage_provider.upload_file(
                file_bytes=video_bytes,
                destination_blob_name=destination_blob,
                content_type='video/mp4'
            )

            if not public_url:
                raise IOError(f"Failed to upload initial animatic to storage for scene {scene_id}")

            db_animatic = models.AnimaticsScene(
                id=animatics_id,
                projectId=project_id,
                sceneId=scene_id,
                duration=scene.duration,
                aspectRatio="16:9",
                videoPath=public_url # Store the public storage URL
            )
            db.add(db_animatic)
            logger.info(f"Created new animatics for scene {scene_id}: {animatics_id}")

        db.commit()
        db.refresh(db_animatic)
        logger.info(f"Successfully processed animatics for scene {scene_id}: {db_animatic.id}")
        return db_animatic
        
    except Exception as e:
        logger.error(f"Failed to create animatics for scene {scene_id}: {str(e)}")
        db.rollback()
        raise

def get_animatics_by_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> List[models.AnimaticsScene]:
    """
    Retrieves all animatic scenes for a project, ordered by scene number.
    
    Args:
        db: Database session
        project_id: UUID of the project
        user_context: User context for validation to get animatics for
        
    Returns:
        List of animatic scenes for the project
        
    Raises:
        Exception: If database query fails
    """
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    try:
        logger.debug(f"Retrieving animatics for project: {project_id}")
        
        animatics = db.query(models.AnimaticsScene)\
            .join(models.ScreenplayScene, models.AnimaticsScene.sceneId == models.ScreenplayScene.id)\
            .filter(models.AnimaticsScene.projectId == project_id)\
            .order_by(models.ScreenplayScene.sceneNumber)\
            .all()
        
        logger.debug(f"Found {len(animatics)} animatics for project: {project_id}")
        return animatics
    except Exception as e:
        logger.error(f"Failed to retrieve animatics for project {project_id}: {str(e)}")
        raise


def get_animatic_by_id(db: Session, animatic_id: uuid.UUID, user_context: UserContextService) -> Optional[models.AnimaticsScene]:
    """
    Retrieves a specific animatic by its ID.
    
    Args:
        db: Database session
        animatic_id: UUID of the animatic to retrieve
        user_context: User context for validation
        
    Returns:
        Animatic scene model if found, None otherwise
        
    Raises:
        Exception: If database query fails
    """
    # Validate user can access this animatic
    if not user_context.user_can_access_entity_by_project(animatic_id, models.AnimaticsScene, 'projectId'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animatic not found")
    
    try:
        logger.debug(f"Retrieving animatic: {animatic_id}")
        
        animatic = db.query(models.AnimaticsScene).filter(
            models.AnimaticsScene.id == animatic_id
        ).first()
        
        if animatic:
            logger.debug(f"Found animatic: {animatic_id}")
        else:
            logger.debug(f"Animatic not found: {animatic_id}")
            
        return animatic
    except Exception as e:
        logger.error(f"Failed to retrieve animatic {animatic_id}: {str(e)}")
        raise


def delete_animatics(db: Session, animatics_id: uuid.UUID, user_context: UserContextService) -> bool:
    """
    Finds an animatic, deletes its video from storage, and then deletes the DB record.
    
    Args:
        db: Database session
        animatics_id: UUID of the animatic to delete
        user_context: User context for validation
        
    Returns:
        True if deleted successfully, False if not found
        
    Raises:
        Exception: If deletion fails
    """
    # Validate user can access this animatic
    if not user_context.user_can_access_entity_by_project(animatics_id, models.AnimaticsScene, 'projectId'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Animatic not found")
    
    try:
        logger.info(f"Deleting animatic: {animatics_id}")
        
        db_animatic = db.query(models.AnimaticsScene).filter(
            models.AnimaticsScene.id == animatics_id
        ).first()
        
        if not db_animatic:
            logger.warning(f"Animatic not found for deletion: {animatics_id}")
            return False

        # Delete the video from storage if it exists
        if db_animatic.videoPath:
            try:
                # Construct the blob name to delete from storage
                blob_name = f"animatics/{animatics_id}.mp4"
                storage_provider.delete_file(blob_name)
                logger.debug(f"Deleted animatic video from storage: {blob_name}")
            except Exception as e:
                logger.warning(f"Could not delete storage file for animatic {animatics_id}: {str(e)}")

        # Delete the database record
        db.delete(db_animatic)
        db.commit()
        
        logger.info(f"Successfully deleted animatic: {animatics_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete animatic {animatics_id}: {str(e)}")
        db.rollback()
        raise
