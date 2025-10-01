from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging
from .... import schemas
from ...dependencies import get_db
from ..crud.projects import create_project, get_projects, get_project, delete_project, update_project

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project_route(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.
    
    Args:
        project: Project data to create
        db: Database session
        
    Returns:
        The created project
        
    Raises:
        HTTPException: If project creation fails
    """
    try:
        logger.info(f"Creating new project: {project.projectName}")
        return create_project(db=db, project=project)
    except Exception as e:
        logger.error(f"Failed to create project {project.projectName}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )

@router.get("/", response_model=List[schemas.Project])
def read_projects_route(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """
    Retrieve all projects with pagination.
    
    Args:
        skip: Number of projects to skip (default: 0)
        limit: Maximum number of projects to return (default: 100, max: 1000)
        db: Database session
        
    Returns:
        List of projects
    """
    # Validate pagination parameters
    if limit > 1000:
        limit = 1000
    if skip < 0:
        skip = 0
        
    try:
        logger.info(f"Retrieving projects with skip={skip}, limit={limit}")
        return get_projects(db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Failed to retrieve projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )

@router.get("/{project_id}", response_model=schemas.Project)
def read_project_route(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a single project by its ID.
    
    Args:
        project_id: UUID of the project to retrieve
        db: Database session
        
    Returns:
        The requested project
        
    Raises:
        HTTPException: If project is not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving project: {project_id}")
        project = get_project(db, project_id=project_id)
        if project is None:
            logger.warning(f"Project not found: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Project with ID {project_id} not found"
            )
        return project
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to retrieve project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )

@router.put("/{project_id}", response_model=schemas.Project)
def update_project_route(project_id: uuid.UUID, project_update: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    """
    Update an existing project with partial data.
    
    Args:
        project_id: UUID of the project to update
        project_update: Partial project data to update
        db: Database session
        
    Returns:
        The updated project
        
    Raises:
        HTTPException: If project is not found or update fails
    """
    try:
        logger.info(f"Updating project: {project_id}")
        updated_project = update_project(db, project_id=project_id, project_update=project_update)
        if updated_project is None:
            logger.warning(f"Project not found for update: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        logger.info(f"Successfully updated project: {project_id}")
        return updated_project
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_route(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a project and all its related data.
    
    This operation cascades to delete all related entities including:
    - Characters and their images
    - Worlds and their images
    - Storyboards and their images
    - Animatics and their videos
    - Story threads and screenplay scenes
    
    Args:
        project_id: UUID of the project to delete
        db: Database session
        
    Returns:
        Empty response with 204 status
        
    Raises:
        HTTPException: If project is not found or deletion fails
    """
    try:
        logger.info(f"Deleting project: {project_id}")
        success = delete_project(db, project_id)
        if not success:
            logger.warning(f"Project not found for deletion: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Project with ID {project_id} not found"
            )
        logger.info(f"Successfully deleted project: {project_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to delete project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )