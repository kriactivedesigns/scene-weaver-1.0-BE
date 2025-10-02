"""
UserContextService: Simple user scope validation utility.

This service provides simple boolean checks for user ownership and assigns
user ownership when creating new entities. CRUD operations use this to
validate access before performing database operations.

Features:
- Simple True/False ownership checks
- User ownership assignment for new entities
- Lightweight and focused utility
"""

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_
from .. import models
import logging

logger = logging.getLogger(__name__)


class UserContextService:
    """
    Simple user scope validation utility.
    Provides boolean ownership checks and user assignment for CRUD operations.
    """
    
    def __init__(self, db: Session, user_id: uuid.UUID):
        """
        Initialize the validation service.
        
        Args:
            db: SQLAlchemy database session
            user_id: UUID of the current authenticated user
        """
        self.db = db
        self.user_id = user_id
    
    # ==========================================
    # OWNERSHIP CHECK METHODS
    # ==========================================
    
    def user_owns_project(self, project_id: uuid.UUID) -> bool:
        """
        Check if user owns a specific project.
        
        Args:
            project_id: UUID of project to check
            
        Returns:
            True if user owns the project, False otherwise
        """
        # Multiple ways to ensure we see the debug output
        # Convert to UUID objects to ensure proper comparison
        if isinstance(project_id, str):
            project_id = uuid.UUID(project_id)
        
        user_id = self.user_id
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        # Use direct SQL query to avoid any ORM comparison issues
        project = self.db.query(models.Project)\
            .filter(models.Project.id == project_id)\
            .filter(models.Project.owner_id == user_id)\
            .first()
        
        result = project is not None
        
        if project:
            project_debug = f"=== PROJECT DATA === ID: {project.id} | Owner: {project.owner_id} | Name: {getattr(project, 'name', 'N/A')}"
            print(project_debug)
            logger.info(project_debug)
        
        return result
    
    def user_owns_entity(self, entity_id: uuid.UUID, model_class, owner_field: str = 'owner_id') -> bool:
        """
        Generic ownership check for any entity with owner_id.
        
        Args:
            entity_id: UUID of entity to check
            model_class: SQLAlchemy model class
            owner_field: Name of the owner field (default: 'owner_id')
            
        Returns:
            True if user owns the entity, False otherwise
        """
        entity = self.db.query(model_class)\
            .filter(and_(
                getattr(model_class, 'id') == entity_id,
                getattr(model_class, owner_field) == self.user_id
            ))\
            .first()
        
        return entity is not None
    
    def user_can_access_entity_by_project(self, entity_id: uuid.UUID, model_class, project_field: str = 'projectId') -> bool:
        """
        Check if user can access an entity by validating ownership of its parent project.
        Used for entities like Worlds, Characters, Stories that belong to projects.
        
        Args:
            entity_id: UUID of entity to check
            model_class: SQLAlchemy model class (e.g., models.World, models.Character)
            project_field: Name of the project ID field (default: 'projectId')
            
        Returns:
            True if user owns the parent project, False otherwise
        """
        # First, get the entity to find its project ID
        entity = self.db.query(model_class)\
            .filter(getattr(model_class, 'id') == entity_id)\
            .first()
        
        if not entity:
            return False  # Entity doesn't exist
        
        # Get the project ID from the entity
        project_id = getattr(entity, project_field)
        if not project_id:
            return False  # Entity has no project
        
        # Check if user owns the parent project
        return self.user_owns_project(project_id)
    
    def user_can_access_world(self, world_id: uuid.UUID) -> bool:
        """
        Check if user can access a specific world.
        
        Args:
            world_id: UUID of world to check
            
        Returns:
            True if user owns the parent project, False otherwise
        """
        return self.user_can_access_entity_by_project(world_id, models.World, 'projectId')
    
    def user_can_access_character(self, character_id: uuid.UUID) -> bool:
        """
        Check if user can access a specific character.
        
        Args:
            character_id: UUID of character to check
            
        Returns:
            True if user owns the parent project, False otherwise
        """
        return self.user_can_access_entity_by_project(character_id, models.Character, 'projectId')
    
    def user_can_access_story(self, story_id: uuid.UUID) -> bool:
        """
        Check if user can access a specific story.
        
        Args:
            story_id: UUID of story to check
            
        Returns:
            True if user owns the parent project, False otherwise
        """
        return self.user_can_access_entity_by_project(story_id, models.Story, 'projectId')
    
    # ==========================================
    # OWNERSHIP ASSIGNMENT METHODS
    # ==========================================
    
    def assign_user_ownership(self, data: dict) -> dict:
        """
        Assign current user as owner of a Project.
        Only used when creating new Projects - other entities inherit access via projectId.
        
        Args:
            data: Dictionary of project data
            
        Returns:
            Project data with owner_id set to current user
        """
        data['owner_id'] = self.user_id
        return data
    
    def get_user_id(self) -> uuid.UUID:
        """
        Get the current user ID.
        
        Returns:
            UUID of the current user
        """
        return self.user_id