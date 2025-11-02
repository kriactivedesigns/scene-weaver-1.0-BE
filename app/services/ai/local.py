import os
import httpx
import logging
import base64
from typing import List, Dict, Any, Optional
import asyncio
from .base import AIProvider

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
timeout_config = httpx.Timeout(900.0, read=300.0, write=300.0, connect=30.0)

class LocalAIProvider(AIProvider):
    """
    Local AI implementation of the AI provider interface.
    This is a mock/placeholder implementation for development and testing.
    """
    
    def __init__(self):
        self.base_url = os.getenv("LOCAL_AI_SERVICE_URL")
        self.api_key = os.getenv("LOCAL_AI_API_KEY")

        if not self.base_url or not self.api_key:
            raise ValueError("LOCAL_AI_SERVICE_URL and LOCAL_AI_API_KEY must be set in environment variables.")
        
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }

        # Use an async client for making requests
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers, timeout=timeout_config)
        
        logger.info(f"🏠 Initialized Local AI Provider, connected to: {self.base_url}")
    
    async def generate_image_from_prompt(self, prompt: str, aspect_ratio: str) -> Optional[bytes]:
        """
        Calls the local AI service to generate an image from a prompt.
        """
        logger.info(f"[Local AI] Generating image with prompt: '{prompt[:80]}...'")
        
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio
        }
        
        try:
            response = await self.client.post("/api/v1/generate", json=payload)
            response.raise_for_status()            
            result = response.json()
            if result.get("success") and result.get("image_base64"):
                image_bytes = base64.b64decode(result["image_base64"])
                logger.info("[Local AI] Image generated successfully.")
                return image_bytes
            else:
                logger.error(f"[Local AI] Generation failed: {result.get('message', 'No image data')}")
                return None
        except httpx.RequestError as e:
            logger.error(f"[Local AI] Error connecting to generation service: {e}")
            return None
        except Exception as e:
            logger.error(f"[Local AI] An unexpected error occurred during image generation: {e}")
            return None

    async def edit_image_from_prompt(self, prompt: str, original_image_bytes: bytes) -> Optional[bytes]:
        """
        Calls the local AI service to edit an image based on a prompt.
        """
        logger.info(f"[Local AI] Editing image with prompt: '{prompt[:80]}...'")
        
        image_base64 = base64.b64encode(original_image_bytes).decode('utf-8')
        
        payload = {
            "image_base64": image_base64,
            "prompt": prompt
        }
        
        try:
            response = await self.client.post("/api/v1/edit", json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get("success") and result.get("image_base64"):
                edited_image_bytes = base64.b64decode(result["image_base64"])
                logger.info("[Local AI] Image edited successfully.")
                return edited_image_bytes
            else:
                logger.error(f"[Local AI] Editing failed: {result.get('message', 'No image data')}")
                return None
        except httpx.RequestError as e:
            logger.error(f"[Local AI] Error connecting to editing service: {e}")
            return None
        except Exception as e:
            logger.error(f"[Local AI] An unexpected error occurred during image editing: {e}")
            return None


# Mock implementations
    def generate_story_from_project_context(self, project_context: Dict[str, Any]) -> str:
        """
        Mock implementation that generates a simple story template.
        """
        logger.info("[LOCAL MOCK] Generating story from project context.")
        
        project_name = project_context.get("project", {}).projectName or "Untitled Project"
        characters = project_context.get("characters", [])
        worlds = project_context.get("worlds", [])
        threads = project_context.get("threads", [])
        
        # Generate a simple mock story
        mock_story = f"""# {project_name}

## Chapter 1: The Beginning

Once upon a time, in a world filled with wonder and mystery, our story begins.

### Characters
"""
        
        for char in characters[:3]:  # Limit to first 3 characters
            mock_story += f"- **{char.name}**: {char.description[:100]}...\n"
        
        mock_story += "\n### Setting\n"
        
        for world in worlds[:2]:  # Limit to first 2 worlds
            mock_story += f"In the realm of **{world.name}**, {world.description[:100]}...\n\n"
        
        mock_story += "### The Adventure\n"
        
        for i, thread in enumerate(threads[:3], 1):  # Limit to first 3 threads
            mock_story += f"{i}. {thread.content[:200]}...\n\n"
        
        mock_story += """
And so our heroes embarked on their greatest adventure yet, facing challenges that would test their courage, wisdom, and friendship.

*[This is a mock story generated by the Local AI Provider for development purposes.]*
"""
        
        return mock_story

    def generate_scenes_from_story(self, story_content: str) -> List[Dict[str, Any]]:
        """
        Mock implementation that breaks a story into simple scenes.
        """
        logger.info("[LOCAL MOCK] Generating scenes from story.")
        
        # Simple mock scene breakdown
        mock_scenes = [
            {
                "sceneNumber": 1,
                "duration": 45,
                "content": "### INT. CASTLE HALL - DAY\n\nOur heroes gather in the great hall, preparing for their quest.\n\n**HERO**\n> Are we ready for this adventure?"
            },
            {
                "sceneNumber": 2,
                "duration": 60,
                "content": "### EXT. FOREST PATH - DAY\n\nThe group ventures into the mysterious forest.\n\n**COMPANION**\n> I sense magic in the air."
            },
            {
                "sceneNumber": 3,
                "duration": 90,
                "content": "### INT. CAVE - NIGHT\n\nA dark cave reveals ancient secrets.\n\n**HERO**\n> What lies ahead in the darkness?"
            }
        ]
        
        # Add more scenes based on story length
        story_length = len(story_content)
        if story_length > 1000:
            mock_scenes.append({
                "sceneNumber": 4,
                "duration": 75,
                "content": "### EXT. MOUNTAIN PEAK - DAWN\n\nThe final confrontation approaches.\n\n**HERO**\n> This is our moment of truth."
            })
        
        return mock_scenes

    def extract_entities_from_scene(self, scene_content: str) -> Dict[str, List[str]]:
        """
        Mock implementation that extracts basic entities from scene content.
        """
        logger.info("[LOCAL MOCK] Extracting entities from scene.")
        
        # Simple pattern matching for common character names and locations
        import re
        
        # Extract potential character names (words in bold or after character indicators)
        character_patterns = [
            r'\*\*([A-Z][A-Z\s]+)\*\*',  # Bold uppercase names
            r'([A-Z][a-z]+):',  # Names followed by colon
        ]
        
        characters = []
        for pattern in character_patterns:
            matches = re.findall(pattern, scene_content)
            characters.extend(matches)
        
        # Extract potential locations (after common location indicators)
        location_patterns = [
            r'### (?:INT\.|EXT\.)\s+([A-Z\s]+)\s+-',  # Scene headers
            r'(?:in|at|to)\s+(?:the\s+)?([A-Z][a-z\s]+)',  # Location references
        ]
        
        worlds = []
        for pattern in location_patterns:
            matches = re.findall(pattern, scene_content, re.IGNORECASE)
            worlds.extend([match.strip().title() for match in matches])
        
        # Remove duplicates and clean up
        characters = list(set([char.strip() for char in characters if char.strip()]))
        worlds = list(set([world.strip() for world in worlds if world.strip()]))
        
        return {
            "characters": characters[:5],  # Limit to 5 characters
            "worlds": worlds[:3]  # Limit to 3 worlds
        }

    async def generate_storyboard_image_from_references(
        self, 
        prompt: str, 
        character_image_paths: List[str], 
        world_image_paths: List[str]
    ) -> bytes:
        """
        Mock implementation that returns a placeholder storyboard image.
        """
        logger.info(f"[LOCAL] Generating storyboard image for: '{prompt[:80]}...'")
        logger.info(f"[LOCAL] Using {len(character_image_paths)} character refs and {len(world_image_paths)} world refs")
        
        # Simulate some processing time
        await asyncio.sleep(0.5)
        
        # Return the same mock PNG as generate_image_from_prompt
        return await self.generate_image_from_prompt(prompt, "16:9")

    async def generate_animatics_video_from_references(
        self,
        prompt: str,
        storyboard_image_path: str,
        character_image_paths: List[str],
        world_image_paths: List[str],
        duration_in_seconds: int
    ) -> bytes:
        """
        Mock implementation that returns a placeholder video.
        """
        logger.info(f"[LOCAL MOCK] Generating animatic video for: '{prompt[:80]}...'")
        logger.info(f"[LOCAL MOCK] Duration: {duration_in_seconds}s")
        
        # Simulate longer processing time for video
        await asyncio.sleep(2.0)
        
        # Return a minimal MP4 file header (not a valid video, just for testing)
        # In a real implementation, you would generate actual video content
        mock_mp4_bytes = bytes([
            0x00, 0x00, 0x00, 0x20, 0x66, 0x74, 0x79, 0x70,  # ftyp box
            0x69, 0x73, 0x6F, 0x6D, 0x00, 0x00, 0x02, 0x00,  # isom brand
            0x69, 0x73, 0x6F, 0x6D, 0x69, 0x73, 0x6F, 0x32,  # compatible brands
            0x61, 0x76, 0x63, 0x31, 0x6D, 0x70, 0x34, 0x31,  # avc1, mp41
        ])
        
        logger.info("[LOCAL MOCK] Generated placeholder video successfully.")
        return mock_mp4_bytes