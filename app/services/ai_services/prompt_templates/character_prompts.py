
# This file will contain prompt templates for generating characters based on visual style.

# Note: The keys in this dictionary should correspond to the 'visualStyle' 
# attribute of the Project model. This allows for dynamic selection of the 
# correct prompt template based on the project's settings.

CHARACTER_PROMPT_TEMPLATES = {
    "Monochromatic B&W Dynamic Sketch": """
        "Full-Figure Strict Grayscale Monochromatic B&W Dynamic Sketch." A full-figure, highly detailed, monochromatic black and white (grayscale only) pen and ink sketch of a single character. Emphasize energetic, loose lines and dynamic action lines characteristic of animation or gesture drawing. The background must be pure white. The image should feature meticulous, intricate cross-hatching to define forms, shadows, and textures on the character, creating deep contrast and a strong sense of three-dimensionality, applied with a gestural quality.
        Character Rendering (Full Figure): Render the entire character from head to toe with realistic proportions, emphasizing expressive features, particularly in the eyes and hands, which should convey emotion and focus. Incorporate action lines around the character to suggest movement and vitality. Clothing fabric must show distinct texture and folds, defined by precise hatching, but with a more spontaneous, flowing quality to the lines. Deep, rich shadows are crucial, achieved through dense, yet expressively applied cross-hatching.
        Environment Rendering (White Background): The background is to be pure white, with no environmental elements or suggestions whatsoever.
        Tonal Qualities (Strict Grayscale): The overall tone must be a strict black and white or deep graphite monochromatic palette, with absolutely no color tint or hue. It should mimic classic hand-drawn illustrations and etchings, but with the raw energy of a preliminary sketch. Maintain a high level of contrast between light and shadow. The aesthetic should evoke a classic illustration or master's sketch book, imbued with the immediacy and dynamism of a drawing for animation.
        Subject: {character_description}
    """
}

CHARACTER_PROMPT_NEGATIVE_TEMPLATES = {
    "Monochromatic B&W Dynamic Sketch": ["color", "colorful", "tint", "hue", "saturation", "green", "brown", "red", "blue", "yellow", "sepia", "monochrome but with color"]
}
