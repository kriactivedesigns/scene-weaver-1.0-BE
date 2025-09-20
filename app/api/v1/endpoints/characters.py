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

@router.post("/projects/{project_id}/characters", response_model=schemas.Character, status_code=status.HTTP_201_CREATED)
def create_character_for_project(project_id: uuid.UUID, character: schemas.CharacterCreate, db: Session = Depends(get_db)):
    return crud.create_character(db=db, character=character, project_id=project_id)

@router.get("/projects/{project_id}/characters", response_model=List[schemas.Character])
def read_characters_for_project(project_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_characters_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.get("/characters/{character_id}", response_model=schemas.Character)
def read_character(character_id: uuid.UUID, db: Session = Depends(get_db)):
    db_character = crud.get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return db_character

@router.put("/characters/{character_id}", response_model=schemas.Character)
def update_character(character_id: uuid.UUID, character: schemas.CharacterUpdate, db: Session = Depends(get_db)):
    db_character = crud.update_character(db=db, character_id=character_id, character=character)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return db_character

@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(character_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a character by its ID.
    """
    success = crud.delete_character(db=db, character_id=character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
        
    return Response(status_code=status.HTTP_204_NO_CONTENT)