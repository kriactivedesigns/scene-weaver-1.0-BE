from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from .... import schemas
from ....database import SessionLocal
from ..crud.characters import create_character, get_characters_by_project, get_character, update_character, delete_character, update_character_image

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/projects/{project_id}/characters", response_model=schemas.Character, status_code=status.HTTP_201_CREATED)
def create_character_for_project(project_id: uuid.UUID, character: schemas.CharacterCreate, db: Session = Depends(get_db)):
    """
    Creates a Character for a project and generates an initial image based on its description.
    """
    try:
        # Call the single CRUD function that handles the entire synchronous process
        db_character = create_character(
            db=db, 
            project_id=project_id, 
            character=character
        )
        return db_character
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred during character creation: {e}")

@router.get("/projects/{project_id}/characters", response_model=List[schemas.Character])
def read_characters_for_project(project_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_characters_by_project(db=db, project_id=project_id, skip=skip, limit=limit)

@router.get("/characters/{character_id}", response_model=schemas.Character)
def read_character(character_id: uuid.UUID, db: Session = Depends(get_db)):
    db_character = get_character(db=db, character_id=character_id)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return db_character

@router.put("/characters/{character_id}", response_model=schemas.Character)
def update_character(character_id: uuid.UUID, character: schemas.CharacterUpdate, db: Session = Depends(get_db)):
    db_character = update_character(db=db, character_id=character_id, character=character)
    if db_character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return db_character

@router.delete("/characters/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(character_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Deletes a character and its associated assets by its ID.
    """
    # Call the single CRUD function that handles the entire deletion process
    was_deleted = delete_character(db=db, character_id=character_id)

    if not was_deleted:
        # If the CRUD function returns False, it means the character was not found
        raise HTTPException(status_code=404, detail="Character not found")

    # If successful, return a 204 No Content response, which has no body
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/characters/{character_id}/update-image", response_model=schemas.Character, status_code=status.HTTP_200_OK)
def update_character_image(character_id: uuid.UUID, request: schemas.ImageGenerateRequest, db: Session = Depends(get_db)):
    """
    Synchronously updates a character's image by regenerating it based on a new prompt.
    """
    try:
        # Call the single CRUD function that handles the entire synchronous process
        db_character = update_character_image(
            db=db, 
            character_id=character_id, 
            new_prompt=request.prompt
        )
        return db_character
    except (ValueError, IOError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {e}")