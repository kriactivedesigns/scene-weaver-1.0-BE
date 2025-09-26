from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from . import models, schemas
import uuid
import markdown2

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