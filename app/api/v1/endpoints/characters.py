from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import os

from .... import crud, schemas
from ....database import SessionLocal
from .... import ai_srevices
from .... import prompt_builder

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

@router.post("/characters/{character_id}/generate-image", response_model=schemas.Character, status_code=status.HTTP_200_OK)
def generate_character_image(
    character_id: uuid.UUID,
    request: schemas.ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generates an image for a character based on a prompt, saves it,
    and updates the character's imagePath
    """
    db_character = crud.get_character(db, character_id=character_id)
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    db_project = crud.get_project(db, project_id=db_character.projectId)

    full_prompt = prompt_builder.build_character_prompt(request.prompt, db_project.visualStyle)

    image_bytes = ai_srevices.generate_image_from_prompt(prompt=full_prompt)

    if not image_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate image AI Servoces!")
    
    file_path = f"static/images/{character_id}.png"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    db_character.imagePath = "/" + file_path
    db.commit()
    db.refresh(db_character)

    return db_character