from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .... import models, schemas
from ....services.user_context import UserContextService
import uuid
import markdown2
from .storyboard import delete_storyboard
from .animatics import delete_animatics

# Screenplay Crud functions
def create_screenplay_scenes_for_project(db: Session, scenes: List[schemas.ScreenplaySceneCreate], project_id: uuid.UUID, user_context: UserContextService) -> List[models.ScreenplayScene]:
    """
    Deletes all existing screenplay scenes for a project and creates a new set.
    This ensures the screenplay is always in sync with the latest generation.
    """
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # 1. Delete existing scenes for this project
    db.query(models.ScreenplayScene).filter(models.ScreenplayScene.projectId == project_id).delete()

    # 2. Prepare the new scenes with HTML content
    db_scenes_to_create = []
    for scene in scenes:
        # Convert the Markdown content to HTML
        html_content = markdown2.markdown(scene.content or "")

        # Create a dictionary from the pydantic model
        scene_data = scene.model_dump()

        # Overwrite the 'content' with the new HTML version
        scene_data["content"] = html_content

        db_scenes_to_create.append(models.ScreenplayScene(projectId=project_id, **scene_data))


    # 3. Add all new scenes in a single transaction
    db.add_all(db_scenes_to_create)
    db.commit()

    # 4. Query and return the newly created scenes
    return db.query(models.ScreenplayScene).filter(models.ScreenplayScene.projectId == project_id).order_by(models.ScreenplayScene.sceneNumber).all()

def add_new_scene_to_project(db: Session, scene_data: schemas.NewScreenplayScene, project_id: uuid.UUID, user_context: UserContextService) -> models.ScreenplayScene:
    """
    Adds a new scene to the end of a project's screenplay sequence.
    """
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    max_scene_number = db.query(func.max(models.ScreenplayScene.sceneNumber))\
        .filter(models.ScreenplayScene.projectId == project_id)\
        .scalar() or 0
        
    # 2. For consistency, convert the incoming content to HTML before saving.
    html_content = markdown2.markdown(scene_data.content or "")

    # 3. Create the new scene instance with the next available scene number.
    new_scene = models.ScreenplayScene(
        projectId=project_id,
        sceneNumber=max_scene_number + 1,
        duration=scene_data.duration,
        content=html_content
    )
    
    db.add(new_scene)
    db.commit()
    db.refresh(new_scene)
    
    return new_scene

def update_screenplay_scene(db: Session, scene_id: uuid.UUID, scene: schemas.ScreenplaySceneUpdate, user_context: UserContextService) -> Optional[models.ScreenplayScene]:
    """
    Updates a screenplay scene's attributes (e.g., content, duration).
    """
    # Validate user can access this scene
    if not user_context.user_can_access_entity_by_project(scene_id, models.ScreenplayScene, 'projectId'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    
    db_scene = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    
    if db_scene:
        # Get the update data, excluding any fields the client didn't send
        update_data = scene.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_scene, key, value)
        
        db.commit()
        db.refresh(db_scene)
        
    return db_scene

def get_screenlay_scenes_for_project(db: Session, project_id: uuid.UUID, user_context: UserContextService) -> List[models.ScreenplayScene]:
    """Retrieves all screenplay scenes for a project, ordered by scene number."""
    # Validate user owns the project
    if not user_context.user_owns_project(project_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    return db.query(models.ScreenplayScene).filter(models.ScreenplayScene.projectId == project_id).order_by(models.ScreenplayScene.sceneNumber).all()

def delete_scene_and_reorder(db: Session, scene_id: uuid.UUID, user_context: UserContextService) -> bool:
    """
    Deletes a scene from the database. Returns True on success, False if not found.
    """
    # Validate user can access this scene
    if not user_context.user_can_access_entity_by_project(scene_id, models.ScreenplayScene, 'projectId'):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scene not found")
    
    scene_to_delete = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    if not scene_to_delete:
        return None

    linked_storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.sceneId == scene_id).first()
    if linked_storyboard:
        delete_storyboard(db=db, storyboard_id=linked_storyboard.id, user_context=user_context)

    linked_animatics = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.sceneId == scene_id).first()
    if linked_animatics:
        delete_animatics(db=db, animatics_id=linked_animatics.id, user_context=user_context)
    
    project_id = scene_to_delete.projectId
    db.delete(scene_to_delete)

    scenes_to_renumber = db.query(models.ScreenplayScene)\
        .filter(
            models.ScreenplayScene.projectId == project_id,
            models.ScreenplayScene.sceneNumber > scene_to_delete.sceneNumber
        )\
        .order_by(models.ScreenplayScene.sceneNumber)\
        .all()
    for scene in scenes_to_renumber:
            scene.sceneNumber -= 1
    
    db.commit()
    
    updated_scenes = db.query(models.ScreenplayScene)\
        .filter(models.ScreenplayScene.projectId == project_id)\
        .order_by(models.ScreenplayScene.sceneNumber)\
        .all()
    
    return updated_scenes
