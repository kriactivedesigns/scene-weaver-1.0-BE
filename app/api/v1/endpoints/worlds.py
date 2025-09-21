import os
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from typing import List
import uuid

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

@router.post("/worlds/{world_id}/generate-image", response_model=schemas.World, status_code=status.HTTP_200_OK)
def generate_world_image(
    world_id: uuid.UUID,
    request: schemas.ImageGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generates an image for a character based on a prompt, saves it,
    and updates the character's imagePath
    """
    db_world = crud.get_world(db, world_id=world_id)
    if not db_world:
        raise HTTPException(status_code=404, detail="Character not found")
    
    db_project = crud.get_project(db, project_id=db_world.projectId)

    full_prompt = prompt_builder.build_world_prompt(request.prompt, db_project.visualStyle)

    image_bytes = ai_srevices.generate_image_from_prompt(prompt=full_prompt)

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