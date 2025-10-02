from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging
from .... import schemas
from ...dependencies import get_db
from ..crud.worlds import create_world, get_worlds_by_project, get_world, update_world, update_world_image, delete_world

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/projects/{project_id}/worlds", response_model=schemas.World, status_code=status.HTTP_201_CREATED)
async def create_world_for_project_route(project_id: uuid.UUID, world: schemas.WorldCreate, db: Session = Depends(get_db)):
    """
    Creates a World for a project and generates its image.
    If image generation fails, the world will be deleted from the database.
    
    Args:
        project_id: UUID of the project to add the world to
        world: World data to create
        db: Database session
        
    Returns:
        The created world with generated image
        
    Raises:
        HTTPException: If project not found or world creation fails
    """
    try:
        logger.info(f"Creating world '{world.name}' for project: {project_id}")
        db_world = await create_world(db=db, project_id=project_id, world=world)
        logger.info(f"Successfully created world: {db_world.id}")
        return db_world
    except ValueError as e:
        logger.warning(f"Invalid request for world creation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create world for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An internal error occurred during world creation"
        )

@router.get("/projects/{project_id}/worlds", response_model=List[schemas.World])
def read_worlds_for_project_route(
    project_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retrieve all worlds for a specific project with pagination.
    
    Args:
        project_id: UUID of the project to get worlds for
        skip: Number of worlds to skip (default: 0)
        limit: Maximum number of worlds to return (default: 100, max: 1000)
        db: Database session
        
    Returns:
        List of worlds for the project
    """
    # Validate pagination parameters
    if limit > 1000:
        limit = 1000
    if skip < 0:
        skip = 0
        
    try:
        logger.info(f"Retrieving worlds for project {project_id} with skip={skip}, limit={limit}")
        return get_worlds_by_project(db=db, project_id=project_id, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Failed to retrieve worlds for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve worlds"
        )

@router.get("/worlds/{world_id}", response_model=schemas.World)
def read_world_route(world_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a single world by its ID.
    
    Args:
        world_id: UUID of the world to retrieve
        db: Database session
        
    Returns:
        The requested world
        
    Raises:
        HTTPException: If world is not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving world: {world_id}")
        db_world = get_world(db=db, world_id=world_id)
        if db_world is None:
            logger.warning(f"World not found: {world_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"World with ID {world_id} not found"
            )
        return db_world
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to retrieve world {world_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve world"
        )

@router.put("/worlds/{world_id}", response_model=schemas.World)
def update_world_route(world_id: uuid.UUID, world: schemas.WorldUpdate, db: Session = Depends(get_db)):
    """
    Update a world's information.
    
    Args:
        world_id: UUID of the world to update
        world: Updated world data
        db: Database session
        
    Returns:
        The updated world
        
    Raises:
        HTTPException: If world is not found or update fails
    """
    try:
        logger.info(f"Updating world: {world_id}")
        db_world = update_world(db=db, world_id=world_id, world=world)
        if db_world is None:
            logger.warning(f"World not found for update: {world_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"World with ID {world_id} not found"
            )
        logger.info(f"Successfully updated world: {world_id}")
        return db_world
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update world {world_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update world"
        )

@router.delete("/worlds/{world_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_world_route(world_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Deletes a world and its associated assets.
    
    Args:
        world_id: UUID of the world to delete
        db: Database session
        
    Returns:
        Empty response with 204 status
        
    Raises:
        HTTPException: If world is not found or deletion fails
    """
    try:
        logger.info(f"Deleting world: {world_id}")
        was_deleted = delete_world(db=db, world_id=world_id)
        if not was_deleted:
            logger.warning(f"World not found for deletion: {world_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"World with ID {world_id} not found"
            )
        logger.info(f"Successfully deleted world: {world_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to delete world {world_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete world"
        )

@router.put("/worlds/{world_id}/update-image", response_model=schemas.World, status_code=status.HTTP_200_OK)
async def generate_world_image_route(world_id: uuid.UUID, request: schemas.ImageGenerateRequest, db: Session = Depends(get_db)):
    """
    Updates a world's image by regenerating it based on a new prompt.
    
    Args:
        world_id: UUID of the world to update the image for
        request: Image generation request with new prompt
        db: Database session
        
    Returns:
        The updated world with new image
        
    Raises:
        HTTPException: If world not found or image update fails
    """
    try:
        logger.info(f"Updating image for world: {world_id}")
        db_world = await update_world_image(db=db, world_id=world_id, new_prompt=request.prompt)
        logger.info(f"Successfully updated image for world: {world_id}")
        return db_world
    except (ValueError, IOError) as e:
        logger.warning(f"Invalid request for image update: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update image for world {world_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An internal error occurred during image update"
        )