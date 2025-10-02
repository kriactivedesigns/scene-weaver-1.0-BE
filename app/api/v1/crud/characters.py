from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
from .... import models, schemas
from ....services.user_context import UserContextService
import uuid
import logging
from typing import List, Optional
from ....services.storage import storage_provider
from ....services.ai_services import generative_services, prompt_builder

logger = logging.getLogger(__name__)

# Character CRUD functions
def get_character(db: Session, character_id: uuid.UUID, user_context: UserContextService) -> Optional[models.Character]:
    """Get a single character by ID with user validation."""
    # Validate user can access this character
    if not user_context.user_can_access_character(character_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
    
    return db.query(models.Character).filter(models.Character.id == character_id).first()

def get_characters_by_project(db: Session, project_id: uuid.UUID, user_context: UserContextService, skip: int = 0, limit: int = 100) -> List[models.Character]:
    """Get all characters for a project with pagination and user validation."""
    # Validate user can access this project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return db.query(models.Character).filter(models.Character.projectId == project_id).offset(skip).limit(limit).all()

async def create_character(db: Session, character: schemas.CharacterCreate, project_id: uuid.UUID, user_context: UserContextService) -> models.Character:
    """
    Create a new character with optional image generation.
    If image generation fails, the character will be deleted from the database.
    
    Args:
        db: Database session
        character: Character data to create
        project_id: UUID of the project to add the character to
        user_context: User context for validation
        
    Returns:
        The created character with optional image path
        
    Raises:
        ValueError: If project is not found
        SQLAlchemyError: If database operation fails
    """
    db_character = None
    try:
        # Validate user can access this project
        if not user_context.user_owns_project(project_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        # Verify project exists
        db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not db_project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # First, create the character entry in the database
        db_character = models.Character(projectId=project_id, **character.model_dump())
        db.add(db_character)
        db.commit()
        db.refresh(db_character)
        
        logger.info(f"Created character '{db_character.name}' ({db_character.id}) for project {project_id}")

        # Immediately generate the image if a description is provided
        if db_character.description:
            try:
                logger.debug(f"Generating image for character: {db_character.id}")
                full_prompt = prompt_builder.build_character_prompt(db_character.description, db_project.visualStyle)
                image_bytes = await generative_services.generate_image_from_prompt(prompt=full_prompt, aspect_ratio="3:4")
                
                if image_bytes:
                    # Save the generated image using the storage provider
                    destination_blob = f"characters/{db_character.id}.png"
                    public_url = storage_provider.upload_file(
                        file_bytes=image_bytes,
                        destination_blob_name=destination_blob,
                        content_type="image/png"
                    )
                    if public_url:
                        db_character.imagePath = public_url
                        db.commit()
                        db.refresh(db_character)
                        logger.info(f"Successfully generated and uploaded image for character: {db_character.id}")
                    else:
                        raise Exception("Failed to upload character image")
                else:
                    raise Exception("AI service failed to generate image")
            except Exception as e:
                logger.error(f"Error during image generation for character {db_character.id}: {str(e)}")
                # Delete character if any part of image generation fails
                db.rollback()
                logger.info(f"Rolled back character creation {db_character.id} due to image generation failure")
                db.rollback()
                raise Exception(f"Character creation failed due to image generation error: {str(e)}")
        
        return db_character
        
    except ValueError:
        if db_character:
            db.rollback()
        raise  # Re-raise validation errors
    except SQLAlchemyError as e:
        if db_character:
            db.rollback()
        logger.error(f"Database error creating character: {str(e)}")
        raise
    except Exception as e:
        if db_character:
            db.rollback()
        logger.error(f"Unexpected error creating character: {str(e)}")
        raise

def update_character(db: Session, character_id: uuid.UUID, character: schemas.CharacterUpdate, user_context: UserContextService) -> Optional[models.Character]:
    """
    Update an existing character.
    
    Args:
        db: Database session
        character_id: UUID of the character to update
        character: Updated character data
        user_context: User context for validation
        
    Returns:
        The updated character or None if not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user can access this character
        if not user_context.user_can_access_character(character_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
        
        db_character = db.query(models.Character).filter(models.Character.id == character_id).first()
        if db_character:
            update_data = character.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_character, key, value)
            db.commit()
            db.refresh(db_character)
            logger.info(f"Successfully updated character: {character_id}")
        return db_character
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating character {character_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating character {character_id}: {str(e)}")
        raise

async def update_character_image(db: Session, character_id: uuid.UUID, new_prompt: str, user_context: UserContextService) -> models.Character:
    """
    Updates a character's image by generating a new one based on an additional prompt.
    The new prompt is combined with the original description for context.
    
    Args:
        db: Database session
        character_id: UUID of the character to update
        new_prompt: Additional prompt for image modification
        user_context: User context for validation
        
    Returns:
        The updated character
        
    Raises:
        ValueError: If character not found or has no existing image
        IOError: If file operations fail
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user can access this character
        if not user_context.user_can_access_character(character_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
        
        db_character = get_character(db, character_id=character_id, user_context=user_context)
        if not db_character:
            raise ValueError(f"Character with ID {character_id} not found")

        db_project = db.query(models.Project).filter(models.Project.id == db_character.projectId).first()
        if not db_project:
            raise ValueError(f"Project for character {character_id} not found")
        
        if not db_character.imagePath:
            raise ValueError("Character has no existing image to update.")
        
        logger.debug(f"Updating image for character: {character_id}")
        
        # Download original image using storage provider
        original_blob_name = f"characters/{character_id}.png"
        original_image_bytes = storage_provider.download_file_as_bytes(original_blob_name)
        if not original_image_bytes:
            raise IOError("Failed to retrieve original image from storage.")
        
        
        # Generate new prompt and create edited image
        full_prompt = prompt_builder.build_modify_character_prompt(
            original_prompt=db_character.description,
            prompt=new_prompt,
            visual_style=db_project.visualStyle
        )
        
        logger.info("Full prompt: %s", full_prompt)
        
        new_image_bytes = await generative_services.edit_image_from_prompt(
            prompt=full_prompt,
            original_image_bytes=original_image_bytes
        )

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

        # Update character record
        db_character.imagePath = public_url
        db.commit()
        db.refresh(db_character)
        
        logger.info(f"Successfully updated image for character: {character_id}")
        return db_character
        
    except (ValueError, IOError):
        raise  # Re-raise validation and IO errors
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error updating character image {character_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating character image {character_id}: {str(e)}")
        raise

def delete_character(db: Session, character_id: uuid.UUID, user_context: UserContextService) -> bool:
    """
    Finds a character by its ID, deletes its associated image from storage,
    and then deletes the database record.
    
    Args:
        db: Database session
        character_id: UUID of the character to delete
        user_context: User context for validation
        
    Returns:
        True on success, False if the character is not found
        
    Raises:
        SQLAlchemyError: If database operation fails
    """
    try:
        # Validate user can access this character
        if not user_context.user_can_access_character(character_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Character not found")
        
        # Find the character record in the database
        db_character = db.query(models.Character).filter(models.Character.id == character_id).first()

        if not db_character:
            logger.warning(f"Character not found for deletion: {character_id}")
            return False
        
        logger.info(f"Deleting character '{db_character.name}' ({character_id})")

        # If an imagePath exists, delete the object from storage
        if db_character.imagePath:
            try:
                blob_name = f"characters/{character_id}.png"
                storage_provider.delete_file(blob_name)
                logger.debug(f"Deleted storage file for character: {character_id}")
            except Exception as e:
                # Log the error but continue to delete the DB record
                logger.warning(f"Could not delete storage file for character {character_id}: {str(e)}")

        # Delete the database record
        db.delete(db_character)
        db.commit()
        
        logger.info(f"Successfully deleted character: {character_id}")
        return True
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting character {character_id}: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting character {character_id}: {str(e)}")
        raise
