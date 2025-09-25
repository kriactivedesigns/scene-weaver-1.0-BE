import os
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid
import logging

from .... import crud, schemas
from ....database import SessionLocal
from .... import ai_srevices
from .... import prompt_builder

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
    """
    Creates a World for a project and generates an initial image based on its description.
    """
    db_world = crud.create_world(db=db, world=world, project_id=project_id)
    # Immediately generate the image if a description is provided
    db_project = crud.get_project(db, project_id=db_world.projectId)
    if not db_project:
        # This should not happen if project_id is valid, but good practice to check
        raise HTTPException(status_code=404, detail="Project not found")
    
    full_prompt = prompt_builder.build_world_prompt(db_world.description, db_project.visualStyle)
    image_bytes = ai_srevices.generate_image_from_prompt(prompt=full_prompt, aspect_ratio=db_project.aspectRatio)

    if image_bytes:
        # Save the generated image locally
        file_path = f"static/images/{db_world.id}.png"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        # Update the world's image path in database
        db_world.imagePath = "/" + file_path
        db.commit()
        db.refresh(db_world)
    else:
        # You might want to handle this case, e.g., by logging it
        print(f"Warning: Failed to generate initial image for character {db_world.id}")

    return db_world

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
    # First, retrieve the character from the database
    db_world = crud.get_world(db=db, world_id=world_id)

    if not db_world:
        # If the character doesn't exist, there's nothing to do
        raise HTTPException(status_code=404, detail="World not found")

    # If an image path exists, attempt to delete the file
    if db_world.imagePath:
        # Convert the URL path to a valid relative file path by removing the leading '/'
        relative_file_path = db_world.imagePath.lstrip('/')
        
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
    db.delete(db_world)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/worlds/{world_id}/upadte-image", response_model=schemas.World, status_code=status.HTTP_200_OK)
def generate_world_image(
    world_id: uuid.UUID,
    request: schemas.ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Updates a World's image by generating a new one based on an additional prompt.
    The new prompt is combined with the original description for context.
    """
    db_world = crud.get_world(db, world_id=world_id)
    if not db_world:
        raise HTTPException(status_code=404, detail="Character not found")
    
    db_project = crud.get_project(db, project_id=db_world.projectId)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    full_prompt = prompt_builder.build_modify_world_prompt(request.prompt, db_project.visualStyle)
    image_path_from_db = db_world.imagePath
    relative_file_path = image_path_from_db.lstrip('/')
    image_bytes = ai_srevices.edit_image_from_prompt(
        prompt=full_prompt,
        original_image_path=relative_file_path
    )

    if not image_bytes:
        raise HTTPException(status_code=500, detail="Failed to generate image AI Servoces!")
    
    file_path = f"static/images/{world_id}.png"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(image_bytes)

    db_world.imagePath = "/" + file_path
    db.commit()
    db.refresh(db_world)

    return db_world