from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import uuid
from .... import  schemas, crud
from ....database import SessionLocal
from ....services.task_manager import job_manager, run_storyboard_generation_task
from ....services.connection_manager import manager

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/storyboards/generate", status_code=status.HTTP_202_ACCEPTED)
def generate_storyboards(project_id: uuid.UUID, request: schemas.StoryboardsGenerate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    job_manager[job_id] = {"cancelled": False}
    
    background_tasks.add_task(
        run_storyboard_generation_task, 
        job_id, project_id, request.scene_ids, db
    )
    
    return {"message": "Storyboard generation process started.", "job_id": job_id}

@router.post("/storyboards/cancel/{job_id}", status_code=status.HTTP_200_OK)
def cancel_generation_job(job_id: str):
    if job_id not in job_manager:
        raise HTTPException(status_code=404, detail="Job not found.")
    job_manager[job_id]["cancelled"] = True
    return {"message": "Job cancellation requested."}

@router.websocket("/ws/storyboard-updates/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        while True:
            # This loop just keeps the connection open. All messages are pushed from the server.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id)

@router.get("/projects/{project_id}/storyboards", response_model=List[schemas.StoryboardImage])
def get_project_storyboards(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieves all existing storyboard images for a specific project,
    ordered by scene number.
    """
    storyboard_images = crud.get_storyboards_by_project(db=db, project_id=project_id)
    return storyboard_images
