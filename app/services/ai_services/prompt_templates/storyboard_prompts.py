# This file contains prompt templates for generating storyboard images based on visual style.

# Note: The keys in this dictionary should correspond to the 'visualStyle' 
# attribute of the Project model. This allows for dynamic selection of the 
# correct prompt template based on the project's settings.

STORYBOARD_PROMPT_TEMPLATES = {
    "Monochromatic B&W Dynamic Sketch": """
        "Strict Grayscale Monochromatic B&W Detailed Storyboard Frame." A highly detailed, monochromatic black and white (grayscale only) pen and ink storyboard illustration of a cinematic scene. The image must be rendered in strict grayscale, with absolutely no color tint or hue. It should feature meticulous, intricate cross-hatching to define all figures, objects, environments, shadows, and textures, creating deep contrast and a strong sense of three-dimensionality.
        
        Cinematic Composition (Storyboard Format): Frame the scene with cinematic camera angles and composition techniques typical of professional storyboards. Consider close-ups, medium shots, wide shots, or dynamic angles that best serve the narrative moment. The composition should clearly convey the action, emotion, and spatial relationships described in the scene.
        
        Character Rendering (Grayscale Details): Render all characters with realistic proportions and expressive poses that capture the dramatic moment. Facial expressions, body language, and character interactions should be precisely defined with crisp lines and varied hatching, all expressed through a range of grayscale tones. Characters should be clearly recognizable and emotionally engaging.
        
        Environment and Props (Grayscale Consistency): Any environments, objects, or props within the scene should be rendered consistently with the detailed cross-hatching style, integrated naturally into the overall composition. Their textures and forms should be meticulously defined by the hatching, using only grayscale tones. Focus on elements that support the narrative and mood of the scene.
        
        Lighting and Atmosphere (Strict Grayscale Palette): The overall tone must be a strict black and white or deep graphite monochromatic palette, with absolutely no color tint or hue. Use dramatic lighting to enhance the cinematic quality, with strong directional light sources creating compelling shadows and highlights. Maintain a high level of contrast between light and shadow, using dense cross-hatching for deep shadows and open spaces or lighter hatching for illuminated areas. The aesthetic should evoke classic film storyboards or graphic novel illustrations, imbued with dramatic depth and cinematic storytelling.
        
        Scene Description: {storyboard_description}
    """
}