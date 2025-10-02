from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
import uuid
import logging
from .... import schemas
from ...dependencies import get_db, get_user_service
from ....services.user_context import UserContextService
from ....services.ai_services import generative_services
from ..crud.projects import get_project
from ..crud.story import get_story_for_project, create_or_update_story_for_project, get_story, update_story, delete_story
from ..crud.story import get_characters_for_project, get_storythreads_for_project, get_worlds_for_project

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/projects/{project_id}/generate-story", response_model=schemas.Story, status_code=status.HTTP_201_CREATED)
def generate_story_route(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    user_context: UserContextService = Depends(get_user_service)
):
    """
    Generates a new story for a project based on its context.
    If a story already exists for this project, it will be overwritten with the new content.
    
    Args:
        project_id: UUID of the project to generate story for
        db: Database session
        user_context: User context for validation
        
    Returns:
        The generated story
        
    Raises:
        HTTPException: If project not found or story generation fails
    """
    try:
        logger.info(f"Generating story for project: {project_id}")
        
        # Verify project exists
        project = get_project(db, project_id=project_id, user_context=user_context)
        if not project:
            logger.warning(f"Project not found for story generation: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Project with ID {project_id} not found"
            )
        
        # Gather project context
        threads = get_storythreads_for_project(db=db, project_id=project_id, user_context=user_context)
        characters = get_characters_for_project(db=db, project_id=project_id, user_context=user_context)
        worlds = get_worlds_for_project(db=db, project_id=project_id, user_context=user_context)

        project_context = {
            "project": project,
            "threads": threads,
            "characters": characters,
            "worlds": worlds
        }
        
        logger.debug(f"Generating story with context: {len(threads)} threads, {len(characters)} characters, {len(worlds)} worlds")
        
        # Call the AI service to generate the story
        generated_story = generative_services.generate_story_from_project_context(project_context=project_context)

        if not generated_story:
            logger.error(f"AI service returned empty story for project: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="AI service failed to generate story content"
            )
        
        # Create story data
        title = project.projectName
        story_data = schemas.StoryCreate(title=title, content=generated_story)
        
        # Create or update the story
        db_story = create_or_update_story_for_project(db=db, story=story_data, project_id=project_id, user_context=user_context)
        
        logger.info(f"Successfully generated story for project: {project_id}")
        return db_story
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to generate story for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to generate story"
        )
    
@router.get("/projects/{project_id}/story", response_model=schemas.Story)
def read_story_of_project_route(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    user_context: UserContextService = Depends(get_user_service)
):
    """
    Retrieve the story for a specific project.
    
    Args:
        project_id: UUID of the project to get the story for
        db: Database session
        user_context: User context for validation
        
    Returns:
        The story for the project
        
    Raises:
        HTTPException: If story is not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving story for project: {project_id}")
        db_story = get_story_for_project(db=db, project_id=project_id, user_context=user_context)
        if db_story is None:
            logger.warning(f"Story not found for project: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Story not found for project {project_id}"
            )
        return db_story
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to retrieve story for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve story"
        )

@router.get("/stories/{story_id}", response_model=schemas.Story)
def read_story_route(
    story_id: uuid.UUID, 
    db: Session = Depends(get_db),
    user_context: UserContextService = Depends(get_user_service)
):
    """
    Retrieve a single story by its ID.
    
    Args:
        story_id: UUID of the story to retrieve
        db: Database session
        
    Returns:
        The requested story
        
    Raises:
        HTTPException: If story is not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving story: {story_id}")
        db_story = get_story(db, story_id=story_id, user_context=user_context)
        if db_story is None:
            logger.warning(f"Story not found: {story_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Story with ID {story_id} not found"
            )
        return db_story
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to retrieve story {story_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve story"
        )

@router.put("/stories/{story_id}", response_model=schemas.Story)
def update_story_route(
    story_id: uuid.UUID, 
    story: schemas.StoryContentUpdate, 
    db: Session = Depends(get_db),
    user_context: UserContextService = Depends(get_user_service)
):
    """
    Update a story's title or content.
    
    Args:
        story_id: UUID of the story to update
        story: Updated story data
        db: Database session
        
    Returns:
        The updated story
        
    Raises:
        HTTPException: If story is not found or update fails
    """
    try:
        logger.info(f"Updating story: {story_id}")
        db_story = update_story(db=db, story_id=story_id, story=story, user_context=user_context)
        if db_story is None:
            logger.warning(f"Story not found for update: {story_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Story with ID {story_id} not found"
            )
        logger.info(f"Successfully updated story: {story_id}")
        return db_story
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to update story {story_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update story"
        )

@router.delete("/stories/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_story_route(
    story_id: uuid.UUID, 
    db: Session = Depends(get_db),
    user_context: UserContextService = Depends(get_user_service)
):
    """
    Delete a story by its ID.
    
    Args:
        story_id: UUID of the story to delete
        db: Database session
        
    Returns:
        Empty response with 204 status
        
    Raises:
        HTTPException: If story is not found or deletion fails
    """
    try:
        logger.info(f"Deleting story: {story_id}")
        was_deleted = delete_story(db=db, story_id=story_id, user_context=user_context)
        if not was_deleted:
            logger.warning(f"Story not found for deletion: {story_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Story with ID {story_id} not found"
            )
        logger.info(f"Successfully deleted story: {story_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to delete story {story_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete story"
        )
