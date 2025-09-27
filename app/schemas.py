import uuid
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

# Project Schemas
class ProjectBase(BaseModel):
    projectName: str
    description: Optional[str] = None
    aspectRatio: Optional[str] = "16:9"
    visualStyle: Optional[str] = "Dynamic Line Art (Gesture Drawing)"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class Project(ProjectBase):
    id: uuid.UUID
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# World Schemas
class WorldBase(BaseModel):
    name: str
    description: Optional[str] = None
    imagePath: Optional[str] = None

class WorldCreate(WorldBase):
    pass

class WorldUpdate(WorldBase):
    name: Optional[str] = None
    description: Optional[str] = None
    imagePath: Optional[str] = None
    pass

class WorldDelete(WorldBase):
    pass

class World(WorldBase):
    id: uuid.UUID
    projectId: uuid.UUID
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Character schemas
class CharacterBase(BaseModel):
    name: str
    description: Optional[str] = None
    imagePath: Optional[str] = None

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(CharacterBase):
    name: Optional[str] = None
    description: Optional[str] = None
    imagePath: Optional[str] = None
    pass

class CharacterDelete(CharacterBase):
    pass

class Character(CharacterBase):
    id: uuid.UUID
    projectId: uuid.UUID
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

class ImageGenerateRequest(BaseModel):
    prompt: str

# StoryThread schemas
class StoryThreadBase(BaseModel):
    order: int
    content: Optional[str] = None

class StoryThreadCreate(StoryThreadBase):
    pass

class StoryThreadUpdate(StoryThreadBase):
    pass

class StoryThread(StoryThreadBase):
    id: uuid.UUID
    projectId: uuid.UUID
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Story schema
class StoryBase(BaseModel):
    title: str
    content: Optional[str] = None

class StoryCreate(StoryBase):
    pass

class StoryContentUpdate(BaseModel):
    content: Optional[str] = None

class Story(StoryBase):
    id: uuid.UUID
    projectId: uuid.UUID
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Screenplay schema
class ScreenplaySceneBase(BaseModel):
    sceneNumber: int
    duration: int
    content: Optional[str] = None

class ScreenplaySceneCreate(ScreenplaySceneBase):
    pass

class NewScreenplayScene(BaseModel):
    duration: int = 0
    content: str = ""

class ScreenplaySceneUpdate(BaseModel):
    sceneNumber: Optional[int] = None
    duration: Optional[int] = None
    content: Optional[str] = None

class ScreenplayScene(ScreenplaySceneBase):
    id: uuid.UUID
    projectId: uuid.UUID
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True

# Storyboard schema
class StoryboardsGenerate(BaseModel):
    scene_ids: List[uuid.UUID] = Field(..., min_length=1)

class StoryboardUpdate(BaseModel):
    prompt: str

class CancelJobRequest(BaseModel):
    job_id: str

class StoryboardImage(BaseModel):
    id: uuid.UUID
    projectId: uuid.UUID
    sceneId: uuid.UUID
    aspectRatio: str
    prompt: str
    imagePath: str 
    version: int
    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True