import logging
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from ..ai import ai_provider

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def generate_image_from_prompt(prompt: str, aspect_ratio: str) -> bytes:
    """
    Generates an image from a text prompt using the configured AI provider.
    """
    return ai_provider.generate_image_from_prompt(prompt, aspect_ratio)

def edit_image_from_prompt(prompt: str, original_image_bytes: bytes) -> bytes | None:
    """
    Edits an existing image using the configured AI provider.
    """
    return ai_provider.edit_image_from_prompt(prompt, original_image_bytes)
    
def generate_story_from_project_context(project_context: Dict[str, Any]) -> str:
    """
    Generates a story from project context using the configured AI provider.
    
    This function does NOT interact with the database.
    """
    return ai_provider.generate_story_from_project_context(project_context)

def generate_scenes_from_story(story_content: str) -> list[Dict[str, Any]]:
    """
    Takes story content and breaks it into screenplay scenes using the configured AI provider.
    """
    return ai_provider.generate_scenes_from_story(story_content)
    
def extract_entities_from_scene(scene_content: str) -> Dict[str, List[str]]:
    """
    Extracts character and world names from scene content using the configured AI provider.
    """
    return ai_provider.extract_entities_from_scene(scene_content)
    
async def generate_storyboard_image_from_references(prompt: str, character_image_paths: List[str], world_image_paths: List[str]) -> bytes:
    """
    Generates a storyboard image using reference images and a text prompt with the configured AI provider.
    """
    return await ai_provider.generate_storyboard_image_from_references(prompt, character_image_paths, world_image_paths)

async def generate_animatics_video_from_references(prompt: str, storyboard_image_path: str, character_image_paths: List[str], world_image_paths: List[str], duration_in_seconds: int) -> bytes:
    """
    Generates an animatic video using the configured AI provider.
    """
    return await ai_provider.generate_animatics_video_from_references(prompt, storyboard_image_path, character_image_paths, world_image_paths, duration_in_seconds)