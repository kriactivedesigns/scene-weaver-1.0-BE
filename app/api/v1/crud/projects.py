from sqlalchemy.orm import Session
from .... import models, schemas
import uuid
from .characters import delete_character
from .worlds import delete_world
from .storyboard import delete_storyboard
from .animatics import delete_animatics

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
    Deletes a project and all of its associated entities and cloud assets.
    This function performs a full cascade delete at the application level.
    """
    project_to_delete = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project_to_delete:
        return False

    print(f"Starting deletion for project: {project_to_delete.projectName} ({project_id})")


    # Delete Characters
    characters = db.query(models.Character).filter(models.Character.projectId == project_id).all()
    for char in characters:
        print(f"Deleting character: {char.name}")
        delete_character(db=db, character_id=char.id)

    # Delete Worlds
    worlds = db.query(models.World).filter(models.World.projectId == project_id).all()
    for world in worlds:
        print(f"Deleting world: {world.name}")
        delete_world(db=db, world_id=world.id)

    # Delete Storyboards
    storyboards = db.query(models.StoryboardImage).filter(models.StoryboardImage.projectId == project_id).all()
    for sb in storyboards:
        print(f"Deleting storyboard for scene: {sb.sceneId}")
        delete_storyboard(db=db, storyboard_id=sb.id)

    # Delete Animatics
    animatics = db.query(models.AnimaticsScene).filter(models.AnimaticsScene.projectId == project_id).all()
    for anim in animatics:
        print(f"Deleting animatic for scene: {anim.sceneId}")
        delete_animatics(db=db, animatics_id=anim.id)

    # 2. Delete simple database records that have no cloud assets.
    print("Deleting story threads and screenplay scenes...")
    db.query(models.StoryThread).filter(models.StoryThread.projectId == project_id).delete()
    db.query(models.ScreenplayScene).filter(models.ScreenplayScene.projectId == project_id).delete()
    db.query(models.Story).filter(models.Story.projectId == project_id).delete()

    # 3. Finally, delete the project record itself.
    print("Deleting project record...")
    db.delete(project_to_delete)

    # 4. Commit all changes in a single transaction.
    db.commit()
    print(f"Successfully deleted project {project_id}.")
    
    return True
