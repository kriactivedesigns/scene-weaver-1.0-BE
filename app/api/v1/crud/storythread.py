from sqlalchemy.orm import Session
from .... import models, schemas
import uuid

# StoryThread CRUD functions
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
