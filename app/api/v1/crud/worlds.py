from sqlalchemy.orm import Session
from app import prompt_builder
from .... import models, schemas
import uuid
from ....services import gcs_helper
from .... import ai_services

# World Crud functions
def get_world(db: Session, world_id: uuid.UUID):
    return db.query(models.World).filter(models.World.id == world_id).first()

def get_worlds_by_project(db: Session, project_id = uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.World).filter(models.World.projectId == project_id).offset(skip).limit(limit).all()

def create_world(db: Session, world: schemas.WorldCreate, project_id: uuid.UUID):
    """
    Synchronously creates a world, generates its image, uploads it to GCS,
    and returns the final, complete world object.
    """
    db_world = models.World(projectId=project_id, **world.model_dump())
    db.add(db_world)
    db.commit()
    db.refresh(db_world)

    if db_world.description:
        try:
            db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
            if not db_project:
                raise ValueError("Associated project not found.")

            full_prompt = prompt_builder.build_world_prompt(db_world.description, db_project.visualStyle)
            image_bytes = ai_services.generate_image_from_prompt(prompt=full_prompt, aspect_ratio=db_project.aspectRatio)

            if image_bytes:
                destination_blob = f"worlds/{db_world.id}.png"
                public_url = gcs_helper.upload_file_from_bytes(image_bytes, destination_blob)
                if public_url:
                    db_world.imagePath = public_url
                    db.commit()
                    db.refresh(db_world)
        except Exception as e:
            print(f"An error occurred during image generation for world {db_world.id}: {e}")
    return db_world

def update_world(db: Session, world_id: uuid.UUID, world: schemas.WorldUpdate):
    db_world = db.query(models.World).filter(models.World.id == world_id).first()
    if db_world:
        update_data = world.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_world, key, value)
        db.commit()
        db.refresh(db_world)
    return db_world

def update_world_image(db: Session, world_id: uuid.UUID, new_prompt: str) -> models.World:
    """
    Synchronously updates a world's image by downloading from GCS,
    editing with AI, and re-uploading the new image.
    """
    db_world = get_world(db, world_id=world_id)
    if not db_world:
        raise ValueError("World not found")
    
    db_project = db.query(models.Project).filter(models.Project.id == db_world.projectId).first()
    if not db_project:
        raise ValueError("Project not found")

    if not db_world.imagePath:
        raise ValueError("World has no existing image to update.")

    original_blob_name = f"worlds/{world_id}.png"
    original_image_bytes = gcs_helper.download_file_as_bytes(original_blob_name)
    if not original_image_bytes:
        raise IOError("Failed to retrieve original image from Cloud Storage.")

    full_prompt = prompt_builder.build_modify_world_prompt(new_prompt, db_project.visualStyle)
    new_image_bytes = ai_services.edit_image_from_prompt(full_prompt, original_image_bytes)
    if not new_image_bytes:
        raise Exception("AI service failed to generate edited image.")

    public_url = gcs_helper.upload_file_from_bytes(new_image_bytes, original_blob_name)
    if not public_url:
        raise IOError("Failed to upload updated image to Cloud Storage.")

    db.commit()
    db.refresh(db_world)
    return db_world

def delete_world(db: Session, world_id: uuid.UUID) -> bool:
    """
    Finds a world, deletes its image from GCS, and then deletes the DB record.
    """
    db_world = db.query(models.World).filter(models.World.id == world_id).first()
    if not db_world:
        return False
    if db_world.imagePath:
        try:
            blob_name = f"worlds/{world_id}.png"
            gcs_helper.delete_file(blob_name)
        except Exception as e:
            print(f"Notice: Could not delete GCS file for world {world_id}. Error: {e}")
    db.delete(db_world)
    db.commit()
    return True
