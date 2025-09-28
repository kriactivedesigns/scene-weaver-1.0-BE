from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import os

from .... import crud, schemas
from ....database import SessionLocal
from .... import ai_services
from .... import prompt_builder
from ....services.image_helper import get_relative_path, get_image_path_to_save, save_image_in_db

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
    # First, create the character entry in the database
    db_character = crud.create_character(db=db, character=character, project_id=project_id)
    
    # Immediately generate the image if a description is provided
    if db_character.description:
        # Get the project's visual style to build the correct prompt
        db_project = crud.get_project(db, project_id=db_character.projectId)
        if not db_project:
             # This should not happen if project_id is valid, but good practice to check
            raise HTTPException(status_code=404, detail="Project not found")

        full_prompt = prompt_builder.build_character_prompt(db_character.description, db_project.visualStyle)
        image_bytes = ai_services.generate_image_from_prompt(prompt=full_prompt, aspect_ratio="3:4")
        
        if image_bytes:
            # Save the generated image locally
            file_path = f"{get_image_path_to_save()}/{db_character.id}.png"
            save_image_in_db(image_path=file_path, image_bytes=image_bytes)
            db_character.imagePath = "/" + file_path
            db.commit()
            db.refresh(db_character)
        else:
            # You might want to handle this case, e.g., by logging it
            print(f"Warning: Failed to generate initial image for character {db_character.id}")

    return db_character

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
    # First, retrieve the character from the database
    db_character = crud.get_character(db=db, character_id=character_id)

    if not db_character:
        # If the character doesn't exist, there's nothing to do
        raise HTTPException(status_code=404, detail="Character not found")

    # If an image path exists, attempt to delete the file
    if db_character.imagePath:
        # Convert the URL path to a valid relative file path by removing the leading '/'
        relative_file_path = get_relative_path(db_character.imagePath)
        
        # Check if the file actually exists before trying to delete it
        if os.path.exists(relative_file_path):
            try:
                os.remove(relative_file_path)
                print(f"Successfully deleted image file: {relative_file_path}")
            except OSError as e:
                # Log the error but proceed with deleting the DB record.
                # An orphaned file is better than a failed DB operation.
                print(f"Error deleting file {relative_file_path}: {e}")

    # Finally, delete the character record from the database
    crud.delete_character(db=db, character_id=character_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/characters/{character_id}/update-image", response_model=schemas.Character, status_code=status.HTTP_200_OK)
def update_character_image(
    character_id: uuid.UUID,
    request: schemas.ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Updates a character's image by generating a new one based on an additional prompt.
    The new prompt is combined with the original description for context.
    """
 
    db_character = crud.get_character(db, character_id=character_id)
    if not db_character:
        raise HTTPException(status_code=404, detail="Character not found")

   
    db_project = crud.get_project(db, project_id=db_character.projectId)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    full_prompt = prompt_builder.build_modify_character_prompt(original_prompt=db_character.description, prompt=request.prompt, visual_style=db_project.visualStyle)
    image_path_from_db = db_character.imagePath
    relative_file_path = get_relative_path(image_path_from_db)
    image_bytes = ai_services.edit_image_from_prompt(
        prompt=full_prompt,
        original_image_path=relative_file_path
    )

    if not image_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate image from AI Services!")
    
    # Overwrite the existing image file
    file_path = f"{get_image_path_to_save()}/{character_id}.png"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    # The imagePath doesn't change, but we commit and refresh to update timestamps
    db_character.imagePath = "/" + file_path
    db.commit()
    db.refresh(db_character)

    return db_character