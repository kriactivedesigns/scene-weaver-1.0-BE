import json
import os
import logging
from pathlib import Path
import re
from typing import List, Dict, Any
from vertexai.preview.vision_models import ImageGenerationModel
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
from google import genai
from google.genai import types
from google.genai.errors import APIError
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_ai_client():
    return genai.Client(vertexai=True, project=os.getenv("GOOGLE_CLOUD_PROJECT"), location=os.getenv("GOOGLE_CLOUD_LOCATION"))

client = get_ai_client()

def generate_image_from_prompt(prompt: str, aspect_ratio: str) -> bytes:
    """
    Generates an image from a text prompt using Vertex AI's Imagen 3 model.
    """
    if not client:
        logger.error("AI Service client is not initialized. Cannot generate image.")
        return None

    try:
        logger.info(f"Generating image with prompt: '{prompt[:80]}...'")
        model = ImageGenerationModel.from_pretrained(os.getenv("IMAGE_GENERATION_MODEL", "imagen-4.0-generate-001"))
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio=aspect_ratio
        )

        if response.images[0]:
            logger.info("Image generated successfully.")
            return response.images[0]._image_bytes
        else:
            logger.warning("AI service returned no images for the prompt.")
            return None
            
    except Exception as e:
        logger.error(f"An error occurred during image generation: {e}")
        return None

def edit_image_from_prompt(prompt: str, original_image_bytes: bytes) -> bytes | None:
    """
    Placeholder for modifying an existing image.
    For now, regenerates the image with a new combined prompt.
    """
    
    model = ImageGenerationModel.from_pretrained("imagegeneration@002")
    base_image = load_image(original_image_bytes)
    logger.info(f"Re-generating image for editing with new prompt.")

    try:
        response = model.edit_image(
            base_image=base_image,
            prompt=prompt,
            seed=1,
            guidance_scale=21,
            number_of_images=1
        )

        if response.images[0]:
            logger.info("Image generated successfully.")
            return response.images[0]._image_bytes
        else:
            logger.warning("AI service returned no images for the prompt.")
            return None
            
    except Exception as e:
        logger.error(f"An error occurred during image generation: {e}")
        return None
    
def generate_story_from_project_context(project_context: Dict[str, Any]) -> str:
    """
    Constructs a prompt from the provided context, calls Vertex AI,
    and returns the generated story as formatted text.
    
    This function does NOT interact with the database.
    """
    # 1. Build the prompt from the context dictionary
    threads_text = "\\n".join(f"- {thread.content}" for thread in project_context["threads"])
    characters_text = "\\n".join(f"- **{char.name}:** {char.description}" for char in project_context["characters"])
    worlds_text = "\\n".join(f"- **{world.name}:** {world.description}" for world in project_context["worlds"])

    prompt = f"""
                You are an expert storyteller. Your task is to write a cohesive and compelling story
                in Markdown format based on the provided project elements.

                **Project Title:** {project_context["project"].projectName}

                **World & Setting:**
                {worlds_text}

                **Main Characters:**
                {characters_text}

                **Core Plot Points & Ideas (in order):**
                {threads_text}

                Please generate a rich narrative that creatively weaves all these elements together.
                The story must be returned as a single block of well-formatted Markdown text,
                starting with a title (e.g., # My Story Title).
            """
    model = GenerativeModel(os.getenv("LLM_MODEL", "gemini-2.5-flash"))
    response = model.generate_content(prompt)
    logger.info(response.text.strip()[:80])
    return response.text.strip()

def generate_scenes_from_story(story_content: str) -> list[Dict[str, Any]]:
    """
    Takes story content, calls Vertex AI to break it into screenplay scenes,
    and returns a list of scene data dictionaries.
    """

    prompt = f"""
        You are a professional screenwriter. Your task is to read the following story and break it down into a series of screenplay scenes.
        Return your response as a valid JSON array where each object represents a single scene.

        Each scene object must have the following keys:
        - "sceneNumber": An integer.
        - "duration": An estimated integer duration in seconds.
        - "content": A string containing the screenplay-formatted text for the scene, written in Markdown.

        **Markdown Formatting Rules for Scene Content:**
        - **Scene Headings**: Use a Level 3 Markdown Header (e.g., ### INT. COCKPIT - DAY).
        - **Action Lines**: Use standard paragraph text.
        - **Character Names**: Make the character name **bold** (e.g., **COMMANDER EVA**).
        - **Dialogue**: Place dialogue in a blockquote (e.g., > This is the dialogue.).

        **STORY:**
        {story_content}

        **EXAMPLE RESPONSE FORMAT:**
        [
            {{
                "sceneNumber": 1,
                "duration": 45,
                "content": "### INT. COCKPIT - DAY\\n\\nCommander Eva, 40s, studies a fluctuating signal on her console.\\n\\n**COMMANDER EVA**\\n> What are you?"
            }},
            {{
                "sceneNumber": 2,
                "duration": 90,
                "content": "### EXT. ALIEN PLANET - NIGHT\\n\\nThe ship has crashed. Strange flora glows faintly in the darkness.\\n\\n**COMMANDER EVA**\\n> I'm definitely not in Kansas anymore."
            }}
        ]
        """
    
    generation_config = GenerationConfig(
        response_mime_type="application/json"
    )
    model = GenerativeModel(os.getenv("LLM_MODEL", "gemini-2.5-flash"))

    try:

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        print(response.text[:100])
        raw_text = response.text
        if not raw_text.strip():
            print("AI response was empty.")
            return []
        
        # Clean the response just in case it's wrapped in markdown
        # This regex looks for `````` and extracts what's inside
        match = re.search(r"``````", raw_text)
        if match:
            cleaned_text = match.group(1)
        else:
            cleaned_text = raw_text
        
        # Parse the cleaned JSON
        print(cleaned_text[:100])
        scenes_data = json.loads(cleaned_text)

        if not isinstance(scenes_data, list):
            raise ValueError("AI did not return a valid JSON array.")
        return scenes_data
    
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error parsing AI response: {e}")
        return []
    
def extract_entities_from_scene(scene_content: str) -> Dict[str, List[str]]:
    """
    Uses a text model to extract character and world names from scene content.
    """
    prompt = f"""
        You are a script analyst. Read the following screenplay scene and identify all characters and locations mentioned.
        Return your answer as a single, valid JSON object with two keys: "characters" and "worlds".

        Scene Text: {scene_content}

        Your JSON output:
    """
    model = GenerativeModel(os.getenv("LLM_MODEL", "gemini-2.5-flash"))
    config = GenerationConfig(response_mime_type="application/json")
    
    try:
        response = model.generate_content(prompt, generation_config=config)
        # Simple cleaning in case the model wraps the response
        cleaned_text = re.sub(r"^``````$", "", response.text, flags=re.MULTILINE)
        return json.loads(cleaned_text)
    except Exception as e:
        # Log the full error details for debugging
        logger.error(f"Error extracting entities from scene content: {str(e)}")
        logger.error(f"Scene content length: {len(scene_content)} characters")
        logger.error(f"Scene content preview: {scene_content[:200]}...")
        
        # Re-raise the exception so the task manager can handle it properly
        raise Exception(f"Entity extraction failed: {str(e)}")
    
async def generate_storyboard_image_from_references(prompt: str, character_image_paths: List[str], world_image_paths: List[str]) -> bytes:
    """
    Generates an image using reference images and a text prompt.
    Returns the image data as bytes.
    """
    llm_model = GenerativeModel(os.getenv("LLM_MODEL"))
    system_instruction = "Analyze the provided images and the scene description. Generate a single, highly detailed, cinematic text prompt that incorporates the style and character likenesses from the images to render the scene."
    full_text_prompt_for_llm = f"{system_instruction}\n\nScene Description: {prompt}"
    text_part = Part.from_text(full_text_prompt_for_llm)

    image_parts = []
    all_original_image_paths  = character_image_paths + world_image_paths
    for original_image_path in all_original_image_paths:
        image = load_image(original_image_path)
        image_part = Part.from_data(data=image._image_bytes, mime_type="image/png")
        image_parts.append(image_part)
            
    gemini_prompt_parts = [text_part] + image_parts

    llm_response = llm_model.generate_content(gemini_prompt_parts)
    final_text_prompt = llm_response.text.strip()

    image_gen_model = ImageGenerationModel.from_pretrained(os.getenv("IMAGE_GENERATION_MODEL"))

    try:
        response = await asyncio.to_thread(
            image_gen_model.generate_images,
            prompt=final_text_prompt,
            number_of_images=1,
            aspect_ratio='16:9'
        )

        if response.images:
            print("image generated", response.images[0]._image_bytes[:20])
            return response.images[0]._image_bytes
        else:
            raise ValueError("AI model did not return any images.")
        
    except Exception as e:
        # It's crucial to log the specific error from the AI service
        print(f"Error during image generation with Vertex AI: {e}")
        raise

async def generate_animatics_video_from_references(prompt: str, storyboard_image_path: str, character_image_paths: List[str], world_image_paths: List[str], duration_in_seconds: int) -> bytes:
    """
    Generates an animatic video using a two-step AI process:
    1. Gemini analyzes text, reference images, and the final storyboard to create an optimized video prompt.
    2. A video model generates the final animatic from that optimized prompt.
    """

    print("storyboard_image_path:", storyboard_image_path)
    print("character_image_paths:", character_image_paths)
    print("world_image_paths:", world_image_paths)
    print("duration_in_seconds:", duration_in_seconds)
    
    llm_model = GenerativeModel("gemini-2.5-flash")
    system_instruction = (
        "You are an expert director's assistant. Analyze the provided character images, "
        "world style images, the final storyboard frame, and the scene description. "
        "Generate a single, highly detailed, cinematic text prompt for a text-to-video "
        "AI model. The prompt should describe a short, animated clip that brings the "
        "static storyboard image to life, incorporating the character likenesses, "
        "art style, and the actions described in the scene."
    )
    full_text_prompt_for_llm = f"{system_instruction}\n\nScene Description: {prompt}"
    text_part = Part.from_text(full_text_prompt_for_llm)
    image_parts = []
    all_original_image_paths  = character_image_paths + world_image_paths + [storyboard_image_path]
    for relative_path in all_original_image_paths:
        if not relative_path: continue
        image = load_image(relative_path)
        image_part = Part.from_data(data=image._image_bytes, mime_type="image/png")
        image_parts.append(image_part)

    gemini_prompt_parts = [text_part] + image_parts

    llm_response = await asyncio.to_thread(llm_model.generate_content, gemini_prompt_parts)
    
    final_video_prompt = llm_response.text.strip()
    print("Final video prompt:", final_video_prompt)

    video_model_name = os.getenv("VIDEO_GENERATION_MODEL", "veo-3.0-generate-001")

    try:
        operation = await asyncio.to_thread(
            client.models.generate_videos,
            model=video_model_name,
            prompt=final_video_prompt,
            config=types.GenerateVideosConfig(
                duration_seconds=4, #duration_in_seconds,
                aspect_ratio="16:9",
                resolution="720p",
                number_of_videos=1
            )
        )
        
        video_bytes = await asyncio.to_thread(_poll_for_video_completion, operation, timeout=600, poll_interval=20)
        return video_bytes

    except APIError as e:
        print(f"Gemini API Error during video generation: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise

def _poll_for_video_completion(operation, timeout=300, poll_interval=10):
    """
    Polls the given operation until it is done or a timeout occurs.
    """
    print("Waiting for video generation operation to complete...")
    start_time = time.time()
    while not operation.done:
        if time.time() - start_time > timeout:
            raise TimeoutError("Video generation operation timed out.")
        print("Video generation in progress...")
        time.sleep(poll_interval)
    
    if operation.response and operation.response.generated_videos:
        generated_video = operation.response.generated_videos[0]
        video_bytes = generated_video.video.video_bytes
        print(f"Video generated successfully! Duration: {operation.response.duration_seconds}s")
        return video_bytes
    else:
        error = operation.error or "Unknown error"
        raise ValueError(f"Video generation failed. Operation status: {operation.error}")







