from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging
from .... import schemas
from ...dependencies import get_db
from ..crud.storythread import create_storythread, get_storythread_by_project, get_storythread, update_storythread, delete_storythread

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/projects/{project_id}/storythreads", response_model=schemas.StoryThread, status_code=status.HTTP_201_CREATED)
def create_storythread_for_project_route(project_id: uuid.UUID, storythread: schemas.StoryThreadCreate, db: Session = Depends(get_db)):
    """
    Creates a story thread for a project.
    
    Args:
        project_id: UUID of the project to add the story thread to
        storythread: Story thread data to create
        db: Database session
        
    Returns:
        The created story thread
        
    Raises:
        HTTPException: If project not found or story thread creation fails
    """
    try:
        logger.info(f"Creating story thread for project: {project_id}")
        db_storythread = create_storythread(db=db, storythread=storythread, project_id=project_id)
        logger.info(f"Successfully created story thread: {db_storythread.id}")
        return db_storythread
    except ValueError as e:
        logger.warning(f"Invalid request for story thread creation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create story thread for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create story thread"
        )

@router.get("/projects/{project_id}/storythreads", response_model=List[schemas.StoryThread])
def read_storythreads_for_project_route(
    project_id: uuid.UUID, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retrieve all story threads for a specific project with pagination.
    
    Args:
        project_id: UUID of the project to get story threads for
        skip: Number of story threads to skip (default: 0)
        limit: Maximum number of story threads to return (default: 100, max: 1000)
        db: Database session
        
    Returns:
        List of story threads for the project
    """
    # Validate pagination parameters
    if limit > 1000:
        limit = 1000
    if skip < 0:
        skip = 0
        
    try:
        logger.info(f"Retrieving story threads for project {project_id} with skip={skip}, limit={limit}")
        return get_storythread_by_project(db=db, project_id=project_id, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Failed to retrieve story threads for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve story threads"
        )

@router.get("/storythreads/{storythread_id}", response_model=schemas.StoryThread)
def read_storythread_route(storythread_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a single story thread by its ID.
    
    Args:
        storythread_id: UUID of the story thread to retrieve
        db: Database session
        
    Returns:
        The requested story thread
        
    Raises:
        HTTPException: If story thread is not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving story thread: {storythread_id}")
        db_storythread = get_storythread(db=db, storythread_id=storythread_id)
        if db_storythread is None:
            logger.warning(f"Story thread not found: {storythread_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Story thread with ID {storythread_id} not found"
            )
        return db_storythread
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to retrieve story thread {storythread_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve story thread"
        )

@router.put("/storythreads/{storythread_id}", response_model=schemas.StoryThread)
def update_storythread_route(storythread_id: uuid.UUID, storythread: schemas.StoryThreadUpdate, db: Session = Depends(get_db)):
    """
    Update a story thread's information.
    
    Args:
        storythread_id: UUID of the story thread to update
        storythread: Updated story thread data
        db: Database session
        
    Returns:
        The updated story thread
        
    Raises:
        HTTPException: If story thread is not found or update fails
    """
    try:
        logger.info(f"Updating story thread: {storythread_id}")
        db_storythread = update_storythread(db=db, storythread_id=storythread_id, storythread=storythread)
        if db_storythread is None:
            logger.warning(f"Story thread not found for update: {storythread_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Story thread with ID {storythread_id} not found"
            )
        logger.info(f"Successfully updated story thread: {storythread_id}")
        return db_storythread
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update story thread {storythread_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update story thread"
        )

@router.delete("/storythreads/{storythread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storythread_route(storythread_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a story thread by its ID.
    
    Args:
        storythread_id: UUID of the story thread to delete
        db: Database session
        
    Returns:
        Empty response with 204 status
        
    Raises:
        HTTPException: If story thread is not found or deletion fails
    """
    try:
        logger.info(f"Deleting story thread: {storythread_id}")
        was_deleted = delete_storythread(db=db, storythread_id=storythread_id)
        if not was_deleted:
            logger.warning(f"Story thread not found for deletion: {storythread_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Story thread with ID {storythread_id} not found"
            )
        logger.info(f"Successfully deleted story thread: {storythread_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to delete story thread {storythread_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete story thread"
        )



