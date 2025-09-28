from sqlalchemy.orm import Session
from app import prompt_builder
from .... import models, schemas
import uuid
from ....services import gcs_helper
from .... import ai_services

# Character CRUD functions
def get_character(db: Session, character_id: uuid.UUID):
    return db.query(models.Character).filter(models.Character.id == character_id).first()

def get_characters_by_project(db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Character).filter(models.Character.projectId == project_id).offset(skip).limit(limit).all()

def create_character(db: Session, character: schemas.CharacterCreate, project_id: uuid.UUID):
    
    # First, create the character entry in the database
    db_character = models.Character(projectId=project_id, **character.model_dump())
    db.add(db_character)
    db.commit()
    db.refresh(db_character)

    # Immediately generate the image if a description is provided
    if db_character.description:
        try:
            # Get the project's visual style to build the correct prompt
            db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
            if not db_project:
                # This should not happen if project_id is valid, but good practice to check
                raise ValueError("Project not found")

            full_prompt = prompt_builder.build_character_prompt(db_character.description, db_project.visualStyle)
            image_bytes = ai_services.generate_image_from_prompt(prompt=full_prompt, aspect_ratio="3:4")
            
            if image_bytes:
                # Save the generated image locally
                destination_blob = f"characters/{db_character.id}.png"
                public_url = gcs_helper.upload_file_from_bytes(
                    file_bytes=image_bytes,
                    destination_blob_name=destination_blob
                )
                if public_url:
                    db_character.imagePath = public_url
                    db.commit()
                    db.refresh(db_character)
                else:
                    print(f"Warning: Failed to upload character image to GCS for character {db_character.id}")
            else:
                # You might want to handle this case, e.g., by logging it
                print(f"Warning: AI service failed to generate image for character {db_character.id}")
        except Exception as e:
            print(f"An error occurred during image generation for character {db_character.id}: {e}")
    
    return db_character

def update_character(db: Session, character_id: uuid.UUID, character: schemas.CharacterUpdate):
    db_character = db.query(models.Character).filter(models.Character.id == character_id).first()
    if db_character:
        update_data = character.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_character, key, value)
        db.commit()
        db.refresh(db_character)
    return db_character

def update_character_image(db: Session, character_id: uuid.UUID,  new_prompt: str) -> models.Character:
    """
    Updates a character's image by generating a new one based on an additional prompt.
    The new prompt is combined with the original description for context.
    """
 
    db_character = get_character(db, character_id=character_id)
    if not db_character:
        raise ValueError("Character not found")

    db_project = db.query(models.Project).filter(models.Project.id == db_character.projectId).first()
    if not db_project:
        raise ValueError("Character not found")
    
    if not db_character.imagePath:
        raise ValueError("Character has no existing image to update.")
    
    original_blob_name = f"characters/{character_id}.png"
    original_image_bytes = gcs_helper.download_file_as_bytes(original_blob_name)
    if not original_image_bytes:
        raise IOError("Failed to retrieve original image from Cloud Storage.")
    
    full_prompt = prompt_builder.build_modify_character_prompt(
        original_prompt=db_character.description,
        prompt=new_prompt,
        visual_style=db_project.visualStyle
    )
    
    new_image_bytes = ai_services.edit_image_from_prompt(
        prompt=full_prompt,
        original_image_bytes=original_image_bytes
    )

    if not new_image_bytes:
        raise Exception("AI service failed to generate edited image.")
    
    # Overwrite the existing image file
    public_url = gcs_helper.upload_file_from_bytes(
        file_bytes=new_image_bytes,
        destination_blob_name=original_blob_name # Use the same blob name to overwrite
    )

    if not public_url:
        raise IOError("Failed to upload updated image to Cloud Storage.")

    # The imagePath doesn't change, but we commit and refresh to update timestamps
    db_character.imagePath = public_url
    db.commit()
    db.refresh(db_character)

    return db_character

def delete_character(db: Session, character_id: uuid.UUID) -> bool:
    """
    Finds a character by its ID, deletes its associated image from GCS,
    and then deletes the database record.
    Returns True on success, False if the character is not found.
    """
    # 1. Find the character record in the database
    db_character = db.query(models.Character).filter(models.Character.id == character_id).first()

    if not db_character:
        # Character does not exist
        return False

    # 2. If an imagePath exists, delete the object from GCS
    if db_character.imagePath:
        try:
            blob_name = f"characters/{character_id}.png"
            gcs_helper.delete_file(blob_name)
        except Exception as e:
            # Log the error but continue to delete the DB record.
            print(f"Notice: Could not delete file from GCS for character {character_id}. Error: {e}")

    # 3. Delete the database record
    db.delete(db_character)
    db.commit()
    
    return True
