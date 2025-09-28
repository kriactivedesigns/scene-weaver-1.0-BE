from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from .... import schemas
from .... database import SessionLocal
from ..crud.storythread import create_storythread, get_storythread_by_project, get_storythread, update_storythread, delete_storythread

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/storythreads", response_model=schemas.StoryThread, status_code=status.HTTP_201_CREATED)
def create_storythread_for_project(project_id: uuid.UUID, storythread: schemas.StoryThreadCreate, db: Session = Depends(get_db)):
    """
    Creates a Story thread for a project
    """
    db_storythread = create_storythread(db=db, storythread=storythread, project_id=project_id)
    return db_storythread

@router.get("/projects/{project_id}/storythreads", response_model=List[schemas.StoryThread])
def read_storythreads_for_project(project_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_storythread_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.get("/storythreads/{storythread_id}", response_model=schemas.StoryThread)
def read_storythread(storythread_id: uuid.UUID, db: Session = Depends(get_db)):
    return get_storythread(db=db, storythread_id=storythread_id)

@router.put("/storythreads/{storythread_id}", response_model=schemas.StoryThread)
def update_storythread(storythread_id: uuid.UUID, storythread: schemas.StoryThread, db: Session = Depends(get_db)):
    db_storythread = update_storythread(db=db, storythread_id=storythread_id, storythread=storythread)
    if db_storythread is None:
        raise HTTPException(status_code=404, detail="Story thread not found")
    return db_storythread

@router.delete("/storythreads/{storythread_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_storythread(storythread_id: uuid.UUID, db: Session = Depends(get_db)):
    was_deleted = delete_storythread(db=db, storythread_id=storythread_id)
    if not was_deleted:
        raise HTTPException(status_code=404, detail="Story thread not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)



