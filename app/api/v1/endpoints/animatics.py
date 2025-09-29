from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import uuid
import logging
from .... import schemas
from ...dependencies import get_db
from ....services.task_manager import job_manager, run_animatic_generation_task
from ....services.connection_manager import manager
from ..crud.animatics import get_animatics_by_project

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/projects/{project_id}/animatics/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_project_animatics_route(
    project_id: uuid.UUID, 
    request: schemas.AnimaticsGenerateRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Starts an asynchronous job to generate animatics for the specified scene IDs.
    
    Args:
        project_id: UUID of the project
        request: Animatics generation request with scene IDs
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Job information with job_id for tracking
        
    Raises:
        HTTPException: If request validation fails
    """
    try:
        # Validate input
        if not request.scene_ids:
            logger.warning(f"Empty scene IDs list for animatics generation: {project_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Scene IDs list cannot be empty"
            )
        
        logger.info(f"Starting animatics generation for project {project_id} with {len(request.scene_ids)} scenes")
        
        job_id = str(uuid.uuid4())
        job_manager[job_id] = {"cancelled": False}
        
        background_tasks.add_task(
            run_animatic_generation_task,
            job_id, project_id, request.scene_ids, db
        )
        
        logger.info(f"Animatics generation job started: {job_id}")
        return {"message": "Animatic generation process started.", "job_id": job_id}
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to start animatics generation for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start animatics generation"
        )

@router.post("/animatics/cancel/{job_id}", status_code=status.HTTP_200_OK)
def cancel_animatic_generation_route(job_id: str):
    """
    Requests the cancellation of an ongoing animatic generation job.
    
    Args:
        job_id: ID of the job to cancel
        
    Returns:
        Cancellation confirmation message
        
    Raises:
        HTTPException: If job not found
    """
    try:
        logger.info(f"Cancelling animatics generation job: {job_id}")
        
        if job_id not in job_manager:
            logger.warning(f"Animatics generation job not found: {job_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Job not found."
            )
        
        job_manager[job_id]["cancelled"] = True
        logger.info(f"Animatics generation job cancellation requested: {job_id}")
        return {"message": "Animatic job cancellation requested."}
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Failed to cancel animatics generation job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )

@router.websocket("/ws/animatics-updates/{job_id}")
async def animatic_websocket_endpoint_route(websocket: WebSocket, job_id: str):
    """
    Establishes a WebSocket connection to receive real-time updates for an
    animatic generation job.
    """
    await manager.connect(job_id, websocket)
    try:
        while True:
            # Keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)

@router.get("/projects/{project_id}/animatics", response_model=List[schemas.AnimaticsScene])
def get_project_animatics_route(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves all existing animatic scenes for a specific project,
    ordered by scene number.
    
    Args:
        project_id: UUID of the project to get animatics for
        db: Database session
        
    Returns:
        List of animatic scenes for the project
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Retrieving animatics for project: {project_id}")
        animatic_scenes = get_animatics_by_project(db=db, project_id=project_id)
        logger.info(f"Retrieved {len(animatic_scenes)} animatics for project: {project_id}")
        return animatic_scenes
    except Exception as e:
        logger.error(f"Failed to retrieve animatics for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve animatics"
        )