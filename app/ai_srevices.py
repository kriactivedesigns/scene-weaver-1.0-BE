import json
import os
import logging
import re
from typing import Dict, Any
from vertexai.preview.vision_models import Image, ImageGenerationModel
from vertexai.generative_models import GenerativeModel, GenerationConfig
from google import genai
from google.genai.types import GenerateImagesConfig
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_ai_client():
    """
    Initializes and returns the Google GenAI Client for Vertex AI,
    checking for necessary environment variables and authentication.
    """
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION")

    # Check if essential environment variables are set
    if not project_id or not location:
        logger.error("Error: Environment variables GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set.")
        return None

    try:
        # Explicitly initialize the client for Vertex AI
        # This uses your application-default credentials from the gcloud login
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        logger.info("Successfully initialized Google GenAI Client for Vertex AI.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Google GenAI Client: {e}")
        logger.error("Please ensure you have authenticated via 'gcloud auth application-default login'.")
        return None
    
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
        # Use the generate_images method specifically for Imagen models
        response = client.models.generate_images(
            model="imagen-4.0-generate-001",  # A powerful and recent model
            prompt=prompt,
            config=GenerateImagesConfig(
                number_of_images=1,
                image_size="1k",
                aspect_ratio=aspect_ratio
            ),
        )

        if response.generated_images:
            logger.info("Image generated successfully.")
            return response.generated_images[0].image.image_bytes
        else:
            logger.warning("AI service returned no images for the prompt.")
            return None
            
    except Exception as e:
        logger.error(f"An error occurred during image generation: {e}")
        return None

def edit_image_from_prompt(prompt: str, original_image_path: str) -> bytes | None:
    """
    Placeholder for modifying an existing image.
    For now, regenerates the image with a new combined prompt.
    """
    
    model = ImageGenerationModel.from_pretrained("imagegeneration@002")
    base_image = Image.load_from_file(location=original_image_path)
    logger.info(f"Re-generating image for editing with new prompt.")

    response = model.edit_image(
        base_image=base_image,
        prompt=prompt,
        seed=1,
        guidance_scale=21,
        number_of_images=1
    )

    try:
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
    model = GenerativeModel("gemini-2.5-flash")
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
    model = GenerativeModel("gemini-2.5-flash")

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