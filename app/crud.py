import asyncio
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup
from . import models, schemas
import uuid
import markdown2
import os
from .services.image_helper import get_relative_path, save_image_in_db, get_image_path_to_save
from .services.video_helper import save_video_in_db, get_video_path_to_save

from . import ai_services

# Project CRUD functions
def get_project(db: Session, project_id: uuid.UUID):
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate):
    # Create a SQLAlchemy model instance from the Pydantic schema
    db_project = models.Project(
        projectName=project.projectName,
        description=project.description
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: uuid.UUID):
    """
    Deleted a project by its ID
    Returns True if deletion was successful, False otherwise
    """
    db_project = get_project(db, project_id)
    if db_project:
        db.delete(db_project)
        db.commit()
        return True
    return False

# World Crud functions
def get_world(db: Session, world_id: uuid.UUID):
    return db.query(models.World).filter(models.World.id == world_id).first()

def get_worlds_by_project(db: Session, project_id = uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.World).filter(models.World.projectId == project_id).offset(skip).limit(limit).all()

def create_world(db: Session, world: schemas.WorldCreate, project_id: uuid.UUID):
    db_world = models.World(projectId=project_id, **world.model_dump())
    db.add(db_world)
    db.commit()
    db.refresh(db_world)
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

def delete_world(db: Session, world_id: uuid.UUID) -> bool:
    db_world = db.query(models.World).filter(models.World.id == world_id).first()
    if db_world:
        db.delete(db_world)
        db.commit()
        return True
    return False

# Character CRUD functions
def get_character(db: Session, character_id: uuid.UUID):
    return db.query(models.Character).filter(models.Character.id == character_id).first()

def get_characters_by_project(db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Character).filter(models.Character.projectId == project_id).offset(skip).limit(limit).all()

def create_character(db: Session, character: schemas.CharacterCreate, project_id: uuid.UUID):
    db_character = models.Character(projectId=project_id, **character.model_dump())
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
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

def delete_character(db: Session, character_id: uuid.UUID) -> bool:
    db_character = db.query(models.Character).filter(models.Character.id == character_id).first()
    if db_character:
        db.delete(db_character)
        db.commit()
        return True
    return False

# StoryThread CRUD fuunctions
def get_storythread(db: Session, storythread_id: uuid.UUID):
    return db.query(models.StoryThread).filter(models.StoryThread.id == storythread_id).first()

def get_storythread_by_project(db: Session, project_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.StoryThread).filter(models.StoryThread.projectId == project_id).offset(skip).limit(limit).all()

def create_storythread(db: Session, storythread: schemas.StoryThreadCreate, project_id: uuid.UUID):
    db_storythread = models.StoryThread(projectId=project_id, **storythread.model_dump())
    db.add(db_storythread)
    db.commit()
    db.refresh(db_storythread)
    return db_storythread

def update_storythread(db: Session, storythread_id: uuid.UUID, storythread: schemas.StoryThreadUpdate):
    db_storythread = db.query(models.StoryThread).filter(models.StoryThread.id == storythread_id).first()
    if db_storythread:
        update_data = storythread.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_storythread, key, value)
        db.commit()
        db.refresh(db_storythread)
    return db_storythread

def delete_storythread(db: Session, storythread_id: uuid.UUID) -> bool:
    db_storythread = db.query(models.StoryThread).filter(models.StoryThread.id == storythread_id).first()
    if db_storythread:
        db.delete(db_storythread)
        db.commit()
        return True
    return False

# Story Crud functions
def crate_or_update_story_for_project(db: Session, story: schemas.StoryCreate, project_id: uuid.UUID):
    """
    Finds the story for the project. If it exists, updates it. 
    If not, creates a new one.
    """

    html_content = markdown2.markdown(story.content)
    
    existing_story = get_story_for_project(db=db, project_id=project_id)
    if existing_story:
        # Story exists, so update its content and title
        existing_story.title = story.title
        existing_story.content = html_content
        db.commit()
        db.refresh(existing_story)
        return existing_story
    else:
        # Story does not exist, create a new one
        new_story = models.Story(
            projectId=project_id,
            title=story.title,
            content=html_content
        )
        db.add(new_story)
        db.commit()
        db.refresh(new_story)
        return new_story
    
def get_story_for_project(db: Session, project_id: uuid.UUID):
    """Fetches the single story associated with a project."""
    return db.query(models.Story).filter(models.Story.projectId == project_id).first()

def get_story(db: Session, story_id: uuid.UUID):
    """
    Retrieves a single story by its ID.
    """
    return db.query(models.Story).filter(models.Story.id == story_id).first()

def update_story(db: Session, story_id: uuid.UUID, story: schemas.StoryContentUpdate):
    """
    Updates a story's attributes.
    """
    db_story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if db_story:
        # Use exclude_unset=True for efficient PATCH-like updates
        update_data = story.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_story, key, value)
        db.commit()
        db.refresh(db_story)
    return db_story

def delete_story(db: Session, story_id: uuid.UUID) -> bool:
    """
    Deletes a story from the database. Returns True on success, False if not found.
    """
    db_story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if db_story:
        db.delete(db_story)
        db.commit()
        return True
    return False

def get_storythreads_for_project(db: Session, project_id: uuid.UUID) -> List[models.StoryThread]:
    """Retrieves all story threads for a project, ordered correctly."""
    return db.query(models.StoryThread).filter(models.StoryThread.projectId == project_id).order_by(models.StoryThread.order).all()

def get_characters_for_project(db: Session, project_id: uuid.UUID) -> List[models.Character]:
    """Retrieves all characters for a project."""
    # Assuming you have a 'Character' model defined
    return db.query(models.Character).filter(models.Character.projectId == project_id).all()

def get_worlds_for_project(db: Session, project_id: uuid.UUID) -> List[models.World]:
    """Retrieves all worlds for a project."""
    # Assuming you have a 'World' model defined
    return db.query(models.World).filter(models.World.projectId == project_id).all()

# Screenplay Crud functions
def create_screenplay_scenes_for_project(db: Session, scenes: List[schemas.ScreenplaySceneCreate], project_id: uuid.UUID) -> List[models.ScreenplayScene]:
    """
    Deletes all existing screenplay scenes for a project and creates a new set.
    This ensures the screenplay is always in sync with the latest generation.
    """
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

def add_new_scene_to_project(db: Session, scene_data: schemas.NewScreenplayScene, project_id: uuid.UUID) -> models.ScreenplayScene:
    """
    Adds a new scene to the end of a project's screenplay sequence.
    """
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

def update_screenplay_scene(db: Session, scene_id: uuid.UUID, scene: schemas.ScreenplaySceneUpdate) -> Optional[models.ScreenplayScene]:
    """
    Updates a screenplay scene's attributes (e.g., content, duration).
    """
    db_scene = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    
    if db_scene:
        # Get the update data, excluding any fields the client didn't send
        update_data = scene.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_scene, key, value)
        
        db.commit()
        db.refresh(db_scene)
        
    return db_scene

def get_screenlay_scenes_for_project(db: Session, project_id: uuid.UUID) -> List[models.ScreenplayScene]:
    """Retrieves all screenplay scenes for a project, ordered by scene number."""
    return db.query(models.ScreenplayScene).filter(models.ScreenplayScene.projectId == project_id).order_by(models.ScreenplayScene.sceneNumber).all()

def delete_scene_and_reorder(db: Session, scene_id: uuid.UUID) -> bool:
    """
    Deletes a scene from the database. Returns True on success, False if not found.
    """
    scene_to_delete = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    if not scene_to_delete:
        return None

    linked_storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.sceneId == scene_id).first()
    if linked_storyboard:
        delete_storyboard(db=db, storyboard_id=linked_storyboard.id)

    linked_animatics = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.sceneId == scene_id).first()
    if linked_animatics:
        delete_animatics(db=db, animatics_id=linked_animatics.id)
    
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

# Storyboard Crud functions
def create_storyboard_for_scene(db: Session, project_id: uuid.UUID, scene_id: uuid.UUID) -> models.StoryboardImage:
    """
    Orchestrates the entire process of creating a single storyboard image.
    """
    scene = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    if not scene:
        raise ValueError("Scene not found")

    soup = BeautifulSoup(scene.content or "", "html.parser")
    plain_text_scene = soup.get_text(separator=" ", strip=True)
    
    entities = ai_services.extract_entities_from_scene(plain_text_scene)

    print("entities", entities)

    character_names_lower = [name.lower() for name in entities.get("characters", [])]
    world_names_lower = [name.lower() for name in entities.get("worlds", [])]

    character_paths = [
        get_relative_path(char.imagePath) for char in 
        db.query(models.Character).filter(
            models.Character.projectId == project_id,
            func.lower(models.Character.name).in_(character_names_lower)
        ).all()
    ]

    world_paths = [
        get_relative_path(world.imagePath) for world in 
        db.query(models.World).filter(
            models.World.projectId == project_id,
            func.lower(models.World.name).in_(world_names_lower)
        ).all()
    ]

    print("character paths",character_paths)
    print("world paths",world_paths)

    final_prompt = f"Cinematic storyboard image depicting: {plain_text_scene}"

    if not final_prompt:
        scene_text = plain_text_scene.strip() if plain_text_scene else ""
        if scene_text:
            final_prompt = f"Cinematic storyboard image depicting: {scene_text}"
    
    if not final_prompt:
        final_prompt = "A visually interesting, high-quality cinematic storyboard image."

    image_bytes = ai_services.generate_storyboard_image_from_references(final_prompt, character_paths, world_paths)

    db_storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.sceneId == scene_id).first()
    if db_storyboard:
        # Update existing storyboard
        image_path = db_storyboard.imagePath
        save_image_in_db(image_path=image_path, image_bytes=image_bytes)
        db_storyboard.prompt = final_prompt
        db_storyboard.version += 1
    else:
        # Create new storyboard
        storyboard_id = uuid.uuid4()
        image_path = os.path.join(f"{get_image_path_to_save()}/{storyboard_id}.png")
        save_image_in_db(image_path=image_path, image_bytes=image_bytes)
        db_storyboard = models.StoryboardImage(
            id=storyboard_id,
            projectId=project_id,
            sceneId=scene_id,
            aspectRatio="16:9",
            prompt=final_prompt,
            imagePath=image_path
        )
        db.add(db_storyboard)

    db.commit()
    db.refresh(db_storyboard)
    
    return db_storyboard

def get_storyboards_by_project(db: Session, project_id: uuid.UUID) -> List[models.StoryboardImage]:
    """
    Retrieves all storyboard images for a given project, ordered by the scene number
    of their associated screenplay scene.
    """
    return db.query(models.StoryboardImage)\
        .join(models.ScreenplayScene, models.StoryboardImage.sceneId == models.ScreenplayScene.id)\
        .filter(models.StoryboardImage.projectId == project_id)\
        .order_by(models.ScreenplayScene.sceneNumber)\
        .all()

def delete_storyboard(db: Session, storyboard_id: uuid.UUID) -> bool:
    """
    Finds a storyboard by its ID, deletes its associated image file from
    the filesystem, and then deletes the database record.
    Returns True on success, False if the storyboard is not found.
    """
    storyboard_to_delete = db.query(models.StoryboardImage).filter(models.StoryboardImage.id == storyboard_id).first()

    if not storyboard_to_delete:
        return False
    
    if storyboard_to_delete.imagePath:
        try:
            relative_file_path = get_relative_path(storyboard_to_delete.imagePath)
            os.remove(relative_file_path)
            print(f"Deleted storyboard image file: {relative_file_path}")
        except OSError as e:
            # Log the error (e.g., file not found) but continue the process.
            print(f"Notice: Could not delete file {relative_file_path}: {e}")

    db.delete(storyboard_to_delete)
    return True

# Animatics Crud funcations
async def create_animatics_for_scene(db: Session, project_id: uuid.UUID, scene_id: uuid.UUID) -> models.AnimaticsScene:
    """
    Orchestrates creating or updating an animatic for a single scene.
    """
    print("create_animatics_for_scene called")
    
    scene = db.query(models.ScreenplayScene).filter(models.ScreenplayScene.id == scene_id).first()
    if not scene:
        raise ValueError("Scene not found")
    
    storyboard = db.query(models.StoryboardImage).filter(models.StoryboardImage.sceneId == scene_id).first()
    if not storyboard:
        raise ValueError("Storyboard image for scene not found. Generate storyboard first.")

    soup = BeautifulSoup(scene.content or "", "html.parser")
    plain_text_prompt = soup.get_text(separator=" ", strip=True)
    if not plain_text_prompt.strip():
        plain_text_prompt = "A cinematic, animated scene."

    character_image_paths = [
        get_relative_path(char.imagePath) for char in 
        db.query(models.Character).filter(models.Character.projectId == project_id).all()
    ]

    world_image_paths = [
        get_relative_path(world.imagePath) for world in 
        db.query(models.World).filter(models.World.projectId == project_id).all()
    ]

    video_bytes = await ai_services.generate_animatics_video_from_references(
        prompt=plain_text_prompt,
        storyboard_image_path=storyboard.imagePath,
        character_image_paths=character_image_paths,
        world_image_paths=world_image_paths,
        duration_in_seconds=scene.duration
    )

    db_animatics = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.sceneId == scene_id).first()

    if db_animatics:
        # Update existing animatic
        video_path = db_animatics.videoPath
        save_video_in_db(video_path, video_bytes)
        db_animatics.version += 1
    else:
        # Create new animatic
        animatics_id = uuid.uuid4()
        save_directory = get_video_path_to_save()
        video_path = os.path.join(save_directory, f"{animatics_id}.mp4")
        save_video_in_db(video_path, video_bytes)

        db_animatic = models.AnimaticsScene(
            id=animatics_id,
            projectId=project_id,
            sceneId=scene_id,
            duration=scene.duration,
            aspectRatio="16:9",
            videoPath=video_path
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
    Finds an Animatics by its ID, deletes its associated image file from
    the filesystem, and then deletes the database record.
    Returns True on success, False if the storyboard is not found.
    """
    animatics_to_delete = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.id == animatics_id).first()

    if not animatics_to_delete:
        return False
    
    if animatics_to_delete.imagePath:
        try:
            relative_file_path = get_relative_path(animatics_to_delete.imagePath)
            os.remove(relative_file_path)
            print(f"Deleted storyboard image file: {relative_file_path}")
        except OSError as e:
            # Log the error (e.g., file not found) but continue the process.
            print(f"Notice: Could not delete file {relative_file_path}: {e}")

    db.delete(animatics_to_delete)
    return True














