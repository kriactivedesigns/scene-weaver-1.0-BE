from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import uuid
from .... import  schemas, crud
from ....database import SessionLocal
from ....services.task_manager import job_manager, run_animatic_generation_task
from ....services.connection_manager import manager

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/animatics/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_project_animatics(project_id: uuid.UUID, request: schemas.AnimaticsGenerateRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Starts an asynchronous job to generate animatics for the specified scene IDs.
    """
    job_id = str(uuid.uuid4())
    job_manager[job_id] = {"cancelled": False}
    
    background_tasks.add_task(
        run_animatic_generation_task,
        job_id, project_id, request.scene_ids, db
    )
    
    return {"message": "Animatic generation process started.", "job_id": job_id}

def cancel_animatic_generation(job_id: str):
    """
    Requests the cancellation of an ongoing animatic generation job.
    """
    if job_id not in job_manager:
        raise HTTPException(status_code=404, detail="Job not found.")
    job_manager[job_id]["cancelled"] = True
    return {"message": "Animatic job cancellation requested."}

@router.websocket("/ws/animatics-updates/{job_id}")
async def animatic_websocket_endpoint(websocket: WebSocket, job_id: str):
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
def get_project_animatics(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves all existing animatic scenes for a specific project,
    ordered by scene number.
    """
    animatic_scenes = crud.get_animatics_by_project(db=db, project_id=project_id)
    return animatic_scenes