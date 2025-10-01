from typing import Optional
import logging
from .prompt_templates.character_prompts import CHARACTER_PROMPT_TEMPLATES
from .prompt_templates.world_prompts import WORLD_PROMPT_TEMPLATES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_CHARACTER_PROMPT = "A detailed digital illustration of {character_description}, high quality."
DEFAULT_WORLD_PROMPT = "A detailed digital fantasy landscape of {world_description}, high quality."

def build_character_prompt(description: str, visual_style: Optional[str]) -> str:
    """
    Constructs a detailed character prompt based on the chosen visual style.
    """
    prompt_template = CHARACTER_PROMPT_TEMPLATES.get(visual_style, DEFAULT_CHARACTER_PROMPT)
    prompt_template = prompt_template.format(character_description=description)
    return prompt_template

def build_world_prompt(description: str, visual_style: str) -> str:
    """
    Constructs a detailed world prompt based on the chosen visual style.
    """
    prompt_template = WORLD_PROMPT_TEMPLATES.get(visual_style, DEFAULT_WORLD_PROMPT)
    return prompt_template.format(world_description=description)

def build_modify_character_prompt(original_prompt: str, prompt: str, visual_style: Optional[str]) -> str:
    """
    Constructs a detailed character prompt based on the chosen visual style.
    """
    prompt = f"""
        A modified sketch of the same character, 
        maintaining the original artistic style and features and
        without altering the rest of the drawing make the following change: {prompt}.
    """
    return prompt

def build_modify_world_prompt(original_prompt: str, prompt: str, visual_style: Optional[str]) -> str:
    """
    Constructs a detailed character prompt based on the chosen visual style.
    """
    prompt = f"""
        A modified sketch of the same image, with {prompt}, 
        maintaining the original artistic style and features.
        Focus on seamlessly {prompt} without altering the rest of the drawing.
    """
    return prompt
