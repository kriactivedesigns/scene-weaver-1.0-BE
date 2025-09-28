from typing import List
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from .... import models
import uuid
from ....services import gcs_helper
from .... import ai_services

# Animatics Crud functions
async def create_animatics_for_scene(db: Session, project_id: uuid.UUID, scene_id: uuid.UUID) -> models.AnimaticsScene:
    """
    Orchestrates creating or updating an animatic video for a single scene,
    uploading the final asset to Google Cloud Storage.
    """
    print("create_animatics_for_scene called")
    
    scene = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    if not scene:
        raise ValueError("Scene not found")
    
    storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.sceneId == scene_id).first()
    if not storyboard:
        raise ValueError("Storyboard image for scene not found. Generate storyboard first.")

    # --- This section for gathering context and building the prompt remains the same ---
    soup = BeautifulSoup(scene.content or "", "html.parser")
    plain_text_prompt = soup.get_text(separator=" ", strip=True)
    if not plain_text_prompt.strip():
        plain_text_prompt = "A cinematic, animated scene."

    # These paths are now GCS URLs, which the AI service can access if needed.
    character_image_paths = [char.imagePath for char in db.query(models.Character).filter(models.Character.projectId == project_id).all()]
    world_image_paths = [world.imagePath for world in db.query(models.World).filter(models.World.projectId == project_id).all()]

    # Await the async AI service call to get the video bytes
    video_bytes = await ai_services.generate_animatics_video_from_references(
        prompt=plain_text_prompt,
        storyboard_image_path=storyboard.imagePath,
        character_image_paths=character_image_paths,
        world_image_paths=world_image_paths,
        duration_in_seconds=scene.duration
    )
    if not video_bytes:
        raise IOError("AI service failed to generate animatic video bytes.")

    # --- This section is updated to use GCS for video storage ---
    db_animatic = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.sceneId == scene_id).first()

    if db_animatic:
        # If animatic exists, overwrite the video in GCS
        destination_blob = f"animatics/{db_animatic.id}.mp4"
        public_url = gcs_helper.upload_file_from_bytes(video_bytes, destination_blob, content_type='video/mp4')
        
        if public_url:
            db_animatic.version += 1
        else:
            raise IOError(f"Failed to upload updated animatic to GCS for scene {scene_id}")
    else:
        # If new, create the animatic record
        animatics_id = uuid.uuid4()
        destination_blob = f"animatics/{animatics_id}.mp4"
        public_url = gcs_helper.upload_file_from_bytes(video_bytes, destination_blob, content_type='video/mp4')

        if not public_url:
            raise IOError(f"Failed to upload initial animatic to GCS for scene {scene_id}")

        db_animatic = models.AnimaticsScene(
            id=animatics_id,
            projectId=project_id,
            sceneId=scene_id,
            duration=scene.duration,
            aspectRatio="16:9",
            videoPath=public_url # Store the public GCS URL
        )
        db.add(db_animatic)

    db.commit()
    db.refresh(db_animatic)
    return db_animatic

def get_animatics_by_project(db: Session, project_id: uuid.UUID) -> List[models.AnimaticsScene]:
    """Retrieves all animatic scenes for a project, ordered by scene number."""
    return db.query(models.AnimaticsScene)\
        .join(models.ScreenplayScene, models.AnimaticsScene.sceneId == models.ScreenplayScene.id)\
        .filter(models.AnimaticsScene.projectId == project_id)\
        .order_by(models.ScreenplayScene.sceneNumber)\
        .all()

def delete_animatics(db: Session, animatics_id: uuid.UUID) -> bool:
    """
    Finds an animatic, deletes its video from GCS, and then deletes the DB record.
    """
    db_animatic = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.id == animatics_id).first()
    if not db_animatic:
        return False

    # Check for the videoPath (correcting from your original code's imagePath)
    if db_animatic.videoPath:
        try:
            # Directly construct the blob name to delete from GCS
            blob_name = f"animatics/{animatics_id}.mp4"
            gcs_helper.delete_file(blob_name)
        except Exception as e:
            print(f"Notice: Could not delete GCS file for animatic {animatics_id}. Error: {e}")

    db.delete(db_animatic)
    db.commit() # Commit the deletion
    return True
