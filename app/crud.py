from sqlalchemy.orm import Session
from . import models, schemas
import uuid


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