from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from .... import crud, schemas
from ....database import SessionLocal

router = APIRouter()

# This is a dependancy that provides database session to the endpoint
# and ensures it's closed after the request is finished
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()

@router.post("/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.
    """
    return crud.create_project(db=db, project=project)

@router.get("/", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all projects
    """
    projects = crud.get_projects(db, skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
def read_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a single project by its ID.
    """
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found!")
    return db_project