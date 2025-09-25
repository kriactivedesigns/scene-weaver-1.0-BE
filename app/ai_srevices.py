import os
import logging
from vertexai.preview.vision_models import Image, ImageGenerationModel
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
    logger.info(original_image_path)
    logger.info(base_image)
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
    