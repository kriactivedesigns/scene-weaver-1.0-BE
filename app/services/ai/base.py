from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AIProvider(ABC):
    """
    An abstract interface for an AI provider.
    This defines the contract for all AI operations, ensuring that any provider 
    can be swapped in seamlessly.
    """
    
    @abstractmethod
    async def generate_image_from_prompt(self, prompt: str, aspect_ratio: str) -> Optional[bytes]:
        """
        Generates an image from a text prompt.

        Args:
            prompt: Text description for image generation.
            aspect_ratio: Desired aspect ratio for the image.

        Returns:
            Image data as bytes, or None if generation fails.
        """
        pass

    @abstractmethod
    async def edit_image_from_prompt(self, prompt: str, original_image_bytes: bytes) -> Optional[bytes]:
        """
        Edits an existing image based on a text prompt.

        Args:
            prompt: Text description for image editing.
            original_image_bytes: Original image data as bytes.

        Returns:
            Edited image data as bytes, or None if editing fails.
        """
        pass

    @abstractmethod
    def generate_story_from_project_context(self, project_context: Dict[str, Any]) -> str:
        """
        Generates a story from project context including characters, worlds, and threads.

        Args:
            project_context: Dictionary containing project, characters, worlds, and threads.

        Returns:
            Generated story as formatted text.
        """
        pass

    @abstractmethod
    def generate_scenes_from_story(self, story_content: str) -> List[Dict[str, Any]]:
        """
        Breaks down a story into screenplay scenes.

        Args:
            story_content: The story text to break down.

        Returns:
            List of scene dictionaries with sceneNumber, duration, and content.
        """
        pass

    @abstractmethod
    def extract_entities_from_scene(self, scene_content: str) -> Dict[str, List[str]]:
        """
        Extracts character and world names from scene content.

        Args:
            scene_content: The scene text to analyze.

        Returns:
            Dictionary with 'characters' and 'worlds' keys containing lists of names.
        """
        pass

    @abstractmethod
    async def generate_storyboard_image_from_references(
        self, 
        prompt: str, 
        character_image_paths: List[str], 
        world_image_paths: List[str]
    ) -> bytes:
        """
        Generates a storyboard image using reference images and a text prompt.

        Args:
            prompt: Scene description for the storyboard.
            character_image_paths: List of paths to character reference images.
            world_image_paths: List of paths to world reference images.

        Returns:
            Generated storyboard image data as bytes.
        """
        pass

    @abstractmethod
    async def generate_animatics_video_from_references(
        self,
        prompt: str,
        storyboard_image_path: str,
        character_image_paths: List[str],
        world_image_paths: List[str],
        duration_in_seconds: int
    ) -> bytes:
        """
        Generates an animatic video from references and storyboard.

        Args:
            prompt: Scene description for the animatic.
            storyboard_image_path: Path to the storyboard image.
            character_image_paths: List of paths to character reference images.
            world_image_paths: List of paths to world reference images.
            duration_in_seconds: Duration of the video in seconds.

        Returns:
            Generated video data as bytes.
        """
        pass