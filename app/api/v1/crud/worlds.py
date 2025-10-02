from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .... import models, schemas
import uuid
import logging
from typing import List, Optional
from ....services.storage import storage_provider
from ....services.ai_services import prompt_builder, generative_services

logger = logging.getLogger(__name__)

# World CRUD functions
def get_world(db: Session, world_id: uuid.UUID) -> Optional[models.World]:
    """Get a single world by ID."""
    return db.query(models.World).filter(models.World.id == world_id).first()

def get_worlds_by_project(db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[models.World]:
    """Get all worlds for a project with pagination."""
    return db.query(models.World).filter(models.World.projectId == project_id).offset(skip).limit(limit).all()

async def create_world(db: Session, world: schemas.WorldCreate, project_id: uuid.UUID) -> models.World:
    """
    Creates a world with image generation. If image generation fails, the world will be deleted.
    
    Args:
        db: Database session
        world: World data to create
        project_id: UUID of the project to add the world to
        
    Returns:
        The created world with optional image path
        
    Raises:
        ValueError: If project is not found
        SQLAlchemyError: If database operation fails
    """
    db_world = None
    try:
        # Verify project exists
        db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not db_project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Create the world entry in the database
        db_world = models.World(projectId=project_id, **world.model_dump())
        db.add(db_world)
        db.commit()
        db.refresh(db_world)
        
        logger.info(f"Created world '{db_world.name}' ({db_world.id}) for project {project_id}")

        # Generate image if description is provided
        if db_world.description:
            try:
                logger.debug(f"Generating image for world: {db_world.id}")
                full_prompt = prompt_builder.build_world_prompt(db_world.description, db_project.visualStyle)
                image_bytes = await generative_services.generate_image_from_prompt(
                    prompt=full_prompt, 
                    aspect_ratio=db_project.aspectRatio
                )

                if image_bytes:
                    # Save the generated image using the storage provider
                    destination_blob = f"worlds/{db_world.id}.png"
                    public_url = storage_provider.upload_file(
                        file_bytes=image_bytes,
                        destination_blob_name=destination_blob,
                        content_type="image/png"
                    )
                    if public_url:
                        db_world.imagePath = public_url
                        db.commit()
                        db.refresh(db_world)
                        logger.info(f"Successfully generated and uploaded image for world: {db_world.id}")
                    else:
                        logger.error(f"Failed to upload world image for world {db_world.id}")
                        # Delete world if image upload fails
                        db.delete(db_world)
                        db.commit()
                        raise Exception("Failed to upload world image")
                else:
                    logger.error(f"AI service failed to generate image for world {db_world.id}")
                    # Delete world if image generation fails
                    db.delete(db_world)
                    db.commit()
                    raise Exception("AI service failed to generate image")
            except Exception as e:
                logger.error(f"Error during image generation for world {db_world.id}: {str(e)}")
                # Delete world if any part of image generation fails
                if db_world:
                    try:
                        db.delete(db_world)
                        db.commit()
                        logger.info(f"Deleted world {db_world.id} due to image generation failure")
                    except Exception as cleanup_error:
                        logger.error(f"Failed to cleanup world after image generation failure: {cleanup_error}")
                        db.rollback()
                raise Exception(f"World creation failed due to image generation error: {str(e)}")
        
        return db_world
        
    except ValueError:
        if db_world:
            db.rollback()
        raise  # Re-raise validation errors
    except SQLAlchemyError as e:
        if db_world:
            db.rollback()
        logger.error(f"Database error creating world: {str(e)}")
        raise
    except Exception as e:
        if db_world:
            db.rollback()
        logger.error(f"Unexpected error creating world: {str(e)}")
        raise

def update_world(db: Session, world_id: uuid.UUID, world: schemas.WorldUpdate) -> Optional[models.World]:
    """
    Update an existing world.
    
    Args:
        db: Database session
        world_id: UUID of the world to update
        world: Updated world data
        
    Returns:
        The updated world or None if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        db_world = db.query(models.World).filter(models.World.id == world_id).first()
        if db_world:
            update_data = world.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_world, key, value)
            db.commit()
            db.refresh(db_world)
            logger.info(f"Successfully updated world: {world_id}")
        return db_world
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating world {world_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating world {world_id}: {str(e)}")
        raise

async def update_world_image(db: Session, world_id: uuid.UUID, new_prompt: str) -> models.World:
    """
    Synchronously updates a world's image by downloading from storage,
    editing with AI, and re-uploading the new image.
    
    Args:
        db: Database session
        world_id: UUID of the world to update
        new_prompt: New prompt for image modification
        
    Returns:
        The updated world
        
    Raises:
        ValueError: If world or project not found, or no existing image
        IOError: If storage operations fail
        SQLAlchemyError: If database operation fails
    """
    try:
        db_world = get_world(db, world_id=world_id)
        if not db_world:
            raise ValueError(f"World with ID {world_id} not found")
        
        db_project = db.query(models.Project).filter(models.Project.id == db_world.projectId).first()
        if not db_project:
            raise ValueError(f"Project for world {world_id} not found")

        if not db_world.imagePath:
            raise ValueError("World has no existing image to update.")
        
        logger.debug(f"Updating image for world: {world_id}")

        # Download original image using storage provider
        original_blob_name = f"worlds/{world_id}.png"
        original_image_bytes = storage_provider.download_file_as_bytes(original_blob_name)
        if not original_image_bytes:
            raise IOError("Failed to retrieve original image from storage.")

        # Generate new image
        full_prompt = prompt_builder.build_modify_world_prompt(new_prompt, db_project.visualStyle)
        new_image_bytes = await generative_services.edit_image_from_prompt(full_prompt, original_image_bytes)
        if not new_image_bytes:
            raise Exception("AI service failed to generate edited image.")

        # Upload new image using storage provider (overwrite existing)
        public_url = storage_provider.upload_file(
            file_bytes=new_image_bytes,
            destination_blob_name=original_blob_name,  # Use same blob name to overwrite
            content_type="image/png"
        )
        if not public_url:
            raise IOError("Failed to upload updated image to storage.")

        # Update world record
        db_world.imagePath = public_url
        db.commit()
        db.refresh(db_world)
        
        logger.info(f"Successfully updated image for world: {world_id}")
        return db_world
        
    except (ValueError, IOError):
        raise  # Re-raise validation and IO errors
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating world image {world_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating world image {world_id}: {str(e)}")
        raise

def delete_world(db: Session, world_id: uuid.UUID) -> bool:
    """
    Finds a world by its ID, deletes its associated image from storage,
    and then deletes the database record.
    
    Args:
        db: Database session
        world_id: UUID of the world to delete
        
    Returns:
        True on success, False if the world is not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Find the world record in the database
        db_world = db.query(models.World).filter(models.World.id == world_id).first()
        if not db_world:
            logger.warning(f"World not found for deletion: {world_id}")
            return False
        
        logger.info(f"Deleting world '{db_world.name}' ({world_id})")
        
        # If an imagePath exists, delete the object from storage
        if db_world.imagePath:
            try:
                blob_name = f"worlds/{world_id}.png"
                storage_provider.delete_file(blob_name)
                logger.debug(f"Deleted storage file for world: {world_id}")
            except Exception as e:
                # Log the error but continue to delete the DB record
                logger.warning(f"Could not delete storage file for world {world_id}: {str(e)}")
        
        # Delete the database record
        db.delete(db_world)
        db.commit()
        
        logger.info(f"Successfully deleted world: {world_id}")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting world {world_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting world {world_id}: {str(e)}")
        raise
