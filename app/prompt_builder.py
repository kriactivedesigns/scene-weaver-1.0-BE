from typing import Optional
from . import ai_srevices

#Character Prompt Definitions
CHARACTER_PROMPT_STYLES = {
    "Dynamic Line Art (Gesture Drawing)": (
        "A dynamic gesture drawing of {description}, masterpiece, best quality, "
        "expressive black and white concept art sketch, detailed character illustration, "
        "clean comic book style line art, high contrast, dramatic shadows. "
        "Full body portrait, standing pose, feet visible, isolated on a plain white background. "
        "The entire figure is visible from head to toe in the frame."
    )
}

# World Prompt Definitions
WORLD_PROMPT_STYLES = {
    "Dynamic Line Art (Gesture Drawing)": (
        "A sweeping panoramic concept sketch of {description}, masterpiece, best quality, "
        "expressive black and white architectural line art, detailed environment illustration, "
        "clean comic book style, high contrast. Wide-angle perspective, emphasizing immense scale."
    )
}

DEFAULT_CHARACTER_PROMPT = "A detailed digital illustration of {description}, high quality."
DEFAULT_WORLD_PROMPT = "A detailed digital fantasy landscape of {description}, high quality."

def build_character_prompt(description: str, visual_style: Optional[str]) -> str:
    """
    Constructs a detailed character prompt based on the chosen visual style.
    """

    prompt_template = CHARACTER_PROMPT_STYLES.get(visual_style, DEFAULT_CHARACTER_PROMPT)
    return prompt_template.format(description=description)

def build_world_prompt(description: str, visual_style: str) -> str:
    """
    Constructs a detailed world prompt based on the chosen visual style.
    """
    prompt_template = WORLD_PROMPT_STYLES.get(visual_style, DEFAULT_WORLD_PROMPT)
    return prompt_template.format(description=description)

def build_modify_character_prompt(original_prompt: str, prompt: str, visual_style: Optional[str]) -> str:
    """
    Constructs a detailed character prompt based on the chosen visual style.
    """
    prompt = """
        A modified sketch of the same image, with {prompt}, 
        maintaining the original artistic style and features.
        Focus on seamlessly {prompt} without altering the rest of the drawing.
    """
    return prompt

def build_modify_world_prompt(original_prompt: str, prompt: str, visual_style: Optional[str]) -> str:
    """
    Constructs a detailed character prompt based on the chosen visual style.
    """
    prompt = """
        A modified sketch of the same image, with {prompt}, 
        maintaining the original artistic style and features.
        Focus on seamlessly {prompt} without altering the rest of the drawing.
    """
    return prompt
