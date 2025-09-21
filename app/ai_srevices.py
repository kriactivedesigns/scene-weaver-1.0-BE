import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def generate_image_from_prompt(prompt: str) -> bytes:
    """
    Generates as image using Gemini model and returns the image data as bytes.
    """
    try:
        response = requests.post(API_URL, headers=headers, json={
            "inputs": prompt
        })

        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"An error occurred during image generation: {e}")
        return None
