import os
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging
from .... import schemas
from ....database import SessionLocal
from ..crud.worlds import create_world, get_worlds_by_project, get_world, update_world_image, delete_world

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/worlds", response_model=schemas.World, status_code=status.HTTP_201_CREATED)
def create_world_for_project(project_id: uuid.UUID, world: schemas.WorldCreate, db: Session = Depends(get_db)):
    """Creates a World and synchronously generates its image, storing it in GCS."""
    try:
        db_world = create_world(db=db, project_id=project_id, world=world)
        return db_world
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")

@router.get("/projects/{project_id}/worlds", response_model=List[schemas.World])
def read_worlds_for_project(project_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_worlds_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.get("/worlds/{world_id}", response_model=schemas.World)
def read_world(world_id: uuid.UUID, db: Session = Depends(get_db)):
    db_world = get_world(db=db, world_id=world_id)
    if db_world is None:
        raise HTTPException(status_code=404, detail="World not found")
    return db_world

@router.put("/worlds/{world_id}", response_model=schemas.World)
def update_world(world_id: uuid.UUID, world: schemas.WorldUpdate, db: Session = Depends(get_db)):
    db_world = update_world(db=db, world_id=world_id, world=world)
    if db_world is None:
        raise HTTPException(status_code=404, detail="World not found")
    return db_world

@router.delete("/worlds/{world_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_world(world_id: uuid.UUID, db: Session = Depends(get_db)):
    """Deletes a world and its associated assets from GCS."""
    was_deleted = delete_world(db=db, world_id=world_id)
    if not was_deleted:
        raise HTTPException(status_code=404, detail="World not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/worlds/{world_id}/update-image", response_model=schemas.World, status_code=status.HTTP_200_OK)
def generate_world_image(world_id: uuid.UUID, request: schemas.ImageGenerateRequest, db: Session = Depends(get_db)):
    """Synchronously updates a world's image by regenerating it based on a new prompt."""
    try:
        db_world = update_world_image(db=db, world_id=world_id, new_prompt=request.prompt)
        return db_world
    except (ValueError, IOError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")