from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect, Response
from sqlalchemy.orm import Session
import uuid
import logging
from .... import schemas
from ...dependencies import get_db, get_user_service
from ....services.user_context import UserContextService
from ....services.task_manager import job_manager, run_storyboard_generation_task
from ....services.connection_manager import manager
from ..crud.storyboard import get_storyboards_by_project, delete_storyboard

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/projects/{project_id}/storyboards/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_project_storyboards_route(
    project_id: uuid.UUID, 
    request: schemas.StoryboardsGenerate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db),
    user_context: UserContextService = Depends(get_user_service)
):
    """
    Starts an asynchronous job to generate storyboards for the specified scene IDs.
    
    Args:
        project_id: UUID of the project
        request: Storyboard generation request with scene IDs
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Job information with job_id for tracking
        
    Raises:
        HTTPException: If request validation fails
    """
    try:
        # Validate user owns the project
        if not user_context.user_owns_project(project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Validate input
        if not request.scene_ids:
            logger.warning(f"Empty scene IDs list for storyboard generation: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scene IDs list cannot be empty"
            )
        
        logger.info(f"Starting storyboard generation for project {project_id} with {len(request.scene_ids)} scenes")
        
        job_id = str(uuid.uuid4())
        job_manager[job_id] = {"cancelled": False}
        
        background_tasks.add_task(
            run_storyboard_generation_task, 
            job_id, project_id, request.scene_ids, db, user_context
        )
        
        logger.info(f"Storyboard generation job started: {job_id}")
        return {"message": "Storyboard generation process started.", "job_id": job_id}
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to start storyboard generation for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start storyboard generation"
        )

@router.post("/storyboards/cancel/{job_id}", status_code=status.HTTP_200_OK)
def cancel_generation_job_route(job_id: str):
    """
    Requests the cancellation of an ongoing storyboard generation job.
    
    Args:
        job_id: ID of the job to cancel
        
    Returns:
        Cancellation confirmation message
        
    Raises:
        HTTPException: If job not found
    """
    try:
        logger.info(f"Cancelling storyboard generation job: {job_id}")
        
        if job_id not in job_manager:
            logger.warning(f"Storyboard generation job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Job not found."
            )
        
        job_manager[job_id]["cancelled"] = True
        logger.info(f"Storyboard generation job cancellation requested: {job_id}")
        return {"message": "Job cancellation requested."}
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to cancel storyboard generation job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )

@router.websocket("/ws/storyboard-updates/{job_id}")
async def websocket_endpoint_route(websocket: WebSocket, job_id: str):
    """
    Establishes a WebSocket connection to receive real-time updates for an
    animatic generation job.
    """
    await manager.connect(job_id, websocket)
    try:
        while True:
            # This loop just keeps the connection open. All messages are pushed from the server.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)

@router.get("/projects/{project_id}/storyboards", response_model=List[schemas.StoryboardImage])
def get_project_storyboards_route(
    project_id: uuid.UUID, 
    db: Session = Depends(get_db),
    user_context: UserContextService = Depends(get_user_service)
):
    """
    Retrieves all existing storyboard images for a specific project,
    ordered by scene number.
    
    Args:
        project_id: UUID of the project to get storyboards for
        db: Database session
        
    Returns:
        List of storyboard images for the project
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Retrieving storyboards for project: {project_id}")
        storyboard_images = get_storyboards_by_project(db=db, project_id=project_id, user_context=user_context)
        logger.info(f"Retrieved {len(storyboard_images)} storyboards for project: {project_id}")
        return storyboard_images
    except Exception as e:
        logger.error(f"Failed to retrieve storyboards for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storyboards"
        )

@router.delete("/storyboards/{storyboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storyboard_endpoint_route(
    storyboard_id: uuid.UUID, 
    db: Session = Depends(get_db),
    user_context: UserContextService = Depends(get_user_service)
):
    """
    Deletes a single storyboard image and its associated assets.
    
    Args:
        storyboard_id: UUID of the storyboard to delete
        db: Database session
        
    Returns:
        Empty response with 204 status
        
    Raises:
        HTTPException: If storyboard not found or deletion fails
    """
    try:
        logger.info(f"Deleting storyboard: {storyboard_id}")
        was_deleted = delete_storyboard(db=db, storyboard_id=storyboard_id, user_context=user_context)
        if not was_deleted:
            logger.warning(f"Storyboard not found for deletion: {storyboard_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Storyboard not found"
            )
        logger.info(f"Successfully deleted storyboard: {storyboard_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to delete storyboard {storyboard_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete storyboard"
        )