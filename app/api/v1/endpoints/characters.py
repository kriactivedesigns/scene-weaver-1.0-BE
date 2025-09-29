from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging
from .... import schemas
from ...dependencies import get_db
from ..crud.characters import create_character, get_characters_by_project, get_character, update_character, delete_character, update_character_image

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/projects/{project_id}/characters", response_model=schemas.Character, status_code=status.HTTP_201_CREATED)
def create_character_for_project_route(project_id: uuid.UUID, character: schemas.CharacterCreate, db: Session = Depends(get_db)):
    """
    Creates a Character for a project and generates an initial image based on its description.
    
    Args:
        project_id: UUID of the project to add the character to
        character: Character data to create
        db: Database session
        
    Returns:
        The created character with generated image
        
    Raises:
        HTTPException: If project not found or character creation fails
    """
    try:
        logger.info(f"Creating character '{character.name}' for project: {project_id}")
        # Call the single CRUD function that handles the entire synchronous process
        db_character = create_character(
            db=db, 
            project_id=project_id, 
            character=character
        )
        logger.info(f"Successfully created character: {db_character.id}")
        return db_character
    except ValueError as e:
        logger.warning(f"Invalid request for character creation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create character for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An internal error occurred during character creation"
        )

@router.get("/projects/{project_id}/characters", response_model=List[schemas.Character])
def read_characters_for_project_route(
    project_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retrieve all characters for a specific project with pagination.
    
    Args:
        project_id: UUID of the project to get characters for
        skip: Number of characters to skip (default: 0)
        limit: Maximum number of characters to return (default: 100, max: 1000)
        db: Database session
        
    Returns:
        List of characters for the project
    """
    # Validate pagination parameters
    if limit > 1000:
        limit = 1000
    if skip < 0:
        skip = 0
        
    try:
        logger.info(f"Retrieving characters for project {project_id} with skip={skip}, limit={limit}")
        return get_characters_by_project(db=db, project_id=project_id, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Failed to retrieve characters for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve characters"
        )

@router.get("/characters/{character_id}", response_model=schemas.Character)
def read_character_route(character_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a single character by its ID.
    
    Args:
        character_id: UUID of the character to retrieve
        db: Database session
        
    Returns:
        The requested character
        
    Raises:
        HTTPException: If character is not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving character: {character_id}")
        db_character = get_character(db=db, character_id=character_id)
        if db_character is None:
            logger.warning(f"Character not found: {character_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Character with ID {character_id} not found"
            )
        return db_character
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to retrieve character {character_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve character"
        )

@router.put("/characters/{character_id}", response_model=schemas.Character)
def update_character_route(character_id: uuid.UUID, character: schemas.CharacterUpdate, db: Session = Depends(get_db)):
    """
    Update a character's information.
    
    Args:
        character_id: UUID of the character to update
        character: Updated character data
        db: Database session
        
    Returns:
        The updated character
        
    Raises:
        HTTPException: If character is not found or update fails
    """
    try:
        logger.info(f"Updating character: {character_id}")
        db_character = update_character(db=db, character_id=character_id, character=character)
        if db_character is None:
            logger.warning(f"Character not found for update: {character_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Character with ID {character_id} not found"
            )
        logger.info(f"Successfully updated character: {character_id}")
        return db_character
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update character {character_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update character"
        )

@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character_route(character_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Deletes a character and its associated assets by its ID.
    
    Args:
        character_id: UUID of the character to delete
        db: Database session
        
    Returns:
        Empty response with 204 status
        
    Raises:
        HTTPException: If character is not found or deletion fails
    """
    try:
        logger.info(f"Deleting character: {character_id}")
        # Call the single CRUD function that handles the entire deletion process
        was_deleted = delete_character(db=db, character_id=character_id)

        if not was_deleted:
            logger.warning(f"Character not found for deletion: {character_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Character with ID {character_id} not found"
            )

        logger.info(f"Successfully deleted character: {character_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to delete character {character_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete character"
        )

@router.put("/characters/{character_id}/update-image", response_model=schemas.Character, status_code=status.HTTP_200_OK)
def update_character_image_route(character_id: uuid.UUID, request: schemas.ImageGenerateRequest, db: Session = Depends(get_db)):
    """
    Synchronously updates a character's image by regenerating it based on a new prompt.
    
    Args:
        character_id: UUID of the character to update the image for
        request: Image generation request with new prompt
        db: Database session
        
    Returns:
        The updated character with new image
        
    Raises:
        HTTPException: If character not found or image update fails
    """
    try:
        logger.info(f"Updating image for character: {character_id}")
        # Call the single CRUD function that handles the entire synchronous process
        db_character = update_character_image(
            db=db, 
            character_id=character_id, 
            new_prompt=request.prompt
        )
        logger.info(f"Successfully updated image for character: {character_id}")
        return db_character
    except (ValueError, IOError) as e:
        logger.warning(f"Invalid request for image update: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update image for character {character_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An internal error occurred during image update"
        )