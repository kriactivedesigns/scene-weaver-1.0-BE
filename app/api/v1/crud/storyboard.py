from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from .... import models
import uuid
from ....services import gcs_helper
from .... import ai_services

# Storyboard Crud functions
async def create_storyboard_for_scene(db: Session, project_id: uuid.UUID, scene_id: uuid.UUID) -> models.StoryboardImage:
    """
    Orchestrates the asynchronous creation of a single storyboard image,
    uploading the final asset to Google Cloud Storage.
    """
    scene = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    if not scene:
        raise ValueError("Scene not found")

    # --- This section for gathering context and building the prompt remains the same ---
    soup = BeautifulSoup(scene.content or "", "html.parser")
    plain_text_scene = soup.get_text(separator=" ", strip=True)
    
    entities = ai_services.extract_entities_from_scene(plain_text_scene)
    character_names_lower = [name.lower() for name in entities.get("characters", [])]
    world_names_lower = [name.lower() for name in entities.get("worlds", [])]

    # Note: These paths are now GCS URLs, which is what the AI service expects.
    character_paths = [char.imagePath for char in db.query(models.Character).filter(
        models.Character.projectId == project_id,
        func.lower(models.Character.name).in_(character_names_lower)
    ).all()]
    world_paths = [world.imagePath for world in db.query(models.World).filter(
        models.World.projectId == project_id,
        func.lower(models.World.name).in_(world_names_lower)
    ).all()]

    final_prompt = f"Cinematic storyboard image depicting: {plain_text_scene}"

    # Await the async AI service call to get the image bytes
    image_bytes = await ai_services.generate_storyboard_image_from_references(final_prompt, character_paths, world_paths)
    if not image_bytes:
        raise IOError("AI service failed to generate storyboard image bytes.")

    # --- This section is updated to use GCS instead of local files ---
    db_storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.sceneId == scene_id).first()

    if db_storyboard:
        # If storyboard exists, overwrite the image in GCS
        destination_blob = f"storyboards/{db_storyboard.id}.png"
        public_url = gcs_helper.upload_file_from_bytes(image_bytes, destination_blob)
        
        if public_url:
            db_storyboard.prompt = final_prompt
            db_storyboard.version += 1
        else:
            raise IOError(f"Failed to upload updated storyboard image to GCS for scene {scene_id}")
    else:
        # If new, create the storyboard record
        storyboard_id = uuid.uuid4()
        destination_blob = f"storyboards/{storyboard_id}.png"
        public_url = gcs_helper.upload_file_from_bytes(image_bytes, destination_blob)

        if not public_url:
            raise IOError(f"Failed to upload initial storyboard image to GCS for scene {scene_id}")

        db_storyboard = models.StoryboardImage(
            id=storyboard_id,
            projectId=project_id,
            sceneId=scene_id,
            aspectRatio="16:9",
            prompt=final_prompt,
            imagePath=public_url # Store the public GCS URL
        )
        db.add(db_storyboard)

    db.commit()
    db.refresh(db_storyboard)
    return db_storyboard

def get_storyboards_by_project(db: Session, project_id: uuid.UUID) -> List[models.StoryboardImage]:
    """
    Retrieves all storyboard images for a given project, ordered by the scene number.
    """
    return db.query(models.StoryboardImage)\
        .join(models.ScreenplayScene, models.StoryboardImage.sceneId == models.ScreenplayScene.id)\
        .filter(models.StoryboardImage.projectId == project_id)\
        .order_by(models.ScreenplayScene.sceneNumber)\
        .all()

def delete_storyboard(db: Session, storyboard_id: uuid.UUID) -> bool:
    """
    Finds a storyboard, deletes its image from GCS, and then deletes the DB record.
    """
    db_storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.id == storyboard_id).first()
    if not db_storyboard:
        return False

    # This check is now against the imagePath URL
    if db_storyboard.imagePath:
        try:
            # Directly construct the blob name to delete from GCS
            blob_name = f"storyboards/{storyboard_id}.png"
            gcs_helper.delete_file(blob_name)
        except Exception as e:
            print(f"Notice: Could not delete GCS file for storyboard {storyboard_id}. Error: {e}")

    db.delete(db_storyboard)
    db.commit() # Commit the deletion
    return True
