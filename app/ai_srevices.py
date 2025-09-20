import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))

def generate_image_from_prompt(prompt: str) -> bytes:
    """
    Generates as image using Gemini model and returns the image data as bytes.
    """
    try:
        model = genai.GenerativeModel('imagen-4.0-generate-001')
        response = model.generate_content(prompt)

        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data
        print("No image data found in the API response.")
        return None
    except Exception as e:
        print(f"An error occurred during image generation: {e}")
        return None
