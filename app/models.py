import uuid
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    TIMESTAMP,
    func,
    Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "Users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "Projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("Users.id"), nullable=False, index=True)  # Add index for performance
    projectName = Column(String(255), nullable=False)
    aspectRatio = Column(String(50), nullable=False, default="16:9")
    visualStyle = Column(String(100))
    description = Column(Text)
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="projects")
    worlds = relationship("World", back_populates="project", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    storyThreads = relationship("StoryThread", back_populates="project", uselist=False, cascade="all, delete-orphan")
    story = relationship("Story", back_populates="project", cascade="all, delete-orphan")
    screenplayScenes = relationship("ScreenplayScene", back_populates="project", cascade="all, delete-orphan")

class World(Base):
    __tablename__ = "Worlds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projectId = Column(UUID(as_uuid=True), ForeignKey("Projects.id"), nullable=False, index=True)  # Add index
    name = Column(String(255), nullable=False)
    description = Column(Text)
    imagePath = Column(String, nullable=True) 
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="worlds")

class Character(Base):
    __tablename__ = "Characters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projectId = Column(UUID(as_uuid=True), ForeignKey("Projects.id"), nullable=False, index=True)  # Add index
    name = Column(String(255), nullable=False)
    description = Column(Text)
    imagePath = Column(String, nullable=True) 
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="characters")

class StoryThread(Base):
    __tablename__ = "StoryThreads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projectId = Column(UUID(as_uuid=True), ForeignKey("Projects.id"), nullable=False, index=True)  # Add index
    content = Column(Text, nullable=False)
    order = Column("order", Integer, nullable=False)
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="storyThreads")

class Story(Base):
    __tablename__ = "Stories"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projectId = Column(UUID(as_uuid=True), ForeignKey("Projects.id"), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    version = Column(Integer, nullable=False, default=1)
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="story", uselist=False)

class ScreenplayScene(Base):
    __tablename__ = "ScreenplayScenes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projectId = Column(UUID(as_uuid=True), ForeignKey("Projects.id"), nullable=False, index=True)  # Add index
    sceneNumber = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    content = Column(Text)
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="screenplayScenes")
    storyboardImage = relationship("StoryboardImage", back_populates="scene", uselist=False, cascade="all, delete-orphan")
    animaticScene = relationship("AnimaticsScene", back_populates="scene", uselist=False, cascade="all, delete-orphan")

class StoryboardImage(Base):
    __tablename__ = "StoryboardImages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projectId = Column(UUID(as_uuid=True), ForeignKey("Projects.id"), nullable=False, index=True)  # Add index
    sceneId = Column(UUID(as_uuid=True), ForeignKey("ScreenplayScenes.id"), nullable=False, unique=True, index=True)  # Add index
    aspectRatio = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    imagePath = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())
    
    scene = relationship("ScreenplayScene", back_populates="storyboardImage")

class AnimaticsScene(Base):
    __tablename__ = "AnimaticScenes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    projectId = Column(UUID(as_uuid=True), ForeignKey("Projects.id"), nullable=False, index=True)  # Add index
    sceneId = Column(UUID(as_uuid=True), ForeignKey("ScreenplayScenes.id"), nullable=False, unique=True, index=True)  # Add index
    duration = Column(Integer, nullable=False)
    aspectRatio = Column(String(50), nullable=False)
    videoPath = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    createdAt = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    scene = relationship("ScreenplayScene", back_populates="animaticScene")