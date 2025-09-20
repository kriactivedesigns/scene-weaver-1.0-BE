from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from .... import crud, schemas
from ....database import SessionLocal

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/worlds", response_model=schemas.World, status_code=status.HTTP_201_CREATED)
def create_world_for_project(project_id: uuid.UUID, world: schemas.WorldCreate, db: Session = Depends(get_db)):
    return crud.create_world(db=db, world=world, project_id=project_id)

@router.get("/projects/{project_id}/worlds", response_model=List[schemas.World])
def read_worlds_for_project(project_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_worlds_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.get("/worlds/{world_id}", response_model=schemas.World)
def read_world(world_id: uuid.UUID, db: Session = Depends(get_db)):
    db_world = crud.get_world(db=db, world_id=world_id)
    if db_world is None:
        raise HTTPException(status_code=404, detail="World not found")
    return db_world

@router.put("/worlds/{world_id}", response_model=schemas.World)
def update_world(world_id: uuid.UUID, world: schemas.WorldUpdate, db: Session = Depends(get_db)):
    db_world = crud.update_world(db=db, world_id=world_id, world=world)
    if db_world is None:
        raise HTTPException(status_code=404, detail="World not found")
    return db_world

@router.delete("/worlds/{world_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_world(world_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a world by its ID.
    """
    success = crud.delete_world(db=db, world_id=world_id)
    if not success:
        raise HTTPException(status_code=404, detail="World not found")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)