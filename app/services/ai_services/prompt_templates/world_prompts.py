
# This file will contain prompt templates for generating worlds based on visual style.

# Note: The keys in this dictionary should correspond to the 'visualStyle' 
# attribute of the Project model. This allows for dynamic selection of the 
# correct prompt template based on the project's settings.

WORLD_PROMPT_TEMPLATES = {
    "Monochromatic B&W Dynamic Sketch": """
        "Strict Grayscale Monochromatic B&W Detailed Environment Sketch." A highly detailed, monochromatic black and white (grayscale only) pen and ink illustration of a scene or location, emphasizing the grand scale and intricate details of the environment. The image must be rendered in strict grayscale, with absolutely no color tint or hue. It should feature meticulous, intricate cross-hatching to define all architectural forms, natural elements, shadows, and textures, creating deep contrast and a strong sense of three-dimensionality.
        Scene Rendering (Grayscale Details): Render the entire scene with realistic proportions and perspective, focusing on conveying the characteristic features of the location. Architectural details (e.g., rusted metal, cracked stone), geological formations, or unique botanical elements should be precisely defined with crisp lines and varied hatching, all expressed through a range of grayscale tones. The composition should clearly establish the atmosphere and scale of the environment.
        Elements within the Scene (Grayscale Consistency): Any objects or incidental figures within the environment should be rendered consistently with the detailed cross-hatching style, integrated naturally into the overall scene. Their textures and forms should be meticulously defined by the hatching, using only grayscale tones.
        Tonal Qualities (Strict Grayscale Palette): The overall tone must be a strict black and white or deep graphite monochromatic palette, with absolutely no color tint or hue. It should mimic classic hand-drawn architectural renderings, etchings, or master's sketches. Maintain a high level of contrast between light and shadow, using dense cross-hatching for deep shadows and open spaces or lighter hatching for illuminated areas. The aesthetic should evoke a classic, detailed illustration from a historical text or architectural blueprint, imbued with intricate depth and realism.
        Subject: {world_description}
    """
}


