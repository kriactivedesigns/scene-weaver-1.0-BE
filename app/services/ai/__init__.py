import os
from dotenv import load_dotenv
from .base import AIProvider
from .vertex_ai import VertexAIProvider
from .local import LocalAIProvider

# Load environment variables
load_dotenv()

def get_ai_provider() -> AIProvider:
    """
    Factory function to get the configured AI provider instance
    based on the AI_PROVIDER environment variable.
    """
    provider = os.getenv("AI_PROVIDER", "vertex-ai").lower()
    
    # Add beautiful icons for different AI providers
    provider_icons = {
        "vertex-ai": "🤖",
        "local": "🏠"
    }
    
    icon = provider_icons.get(provider, "🧠")
    print(f"{icon} Using AI provider: {provider}")
    
    if provider == "vertex-ai":
        # Validate required environment variables for Vertex AI
        required_vars = ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables for Vertex AI: {', '.join(missing_vars)}")
        return VertexAIProvider()
    
    elif provider == "local":
        return LocalAIProvider()
        
    else:
        raise ValueError(f"Unsupported AI provider: {provider}. Supported: 'vertex-ai', 'local'")

# Create a single, shared instance to be imported by the rest of the application
ai_provider = get_ai_provider()

# Get the current provider type for status message
current_provider = os.getenv("AI_PROVIDER", "vertex-ai").lower()

# Display AI provider initialization status with beautiful icons
provider_status = {
    "vertex-ai": "🤖 Vertex AI Provider initialized",
    "local": "🏠 Local AI Provider initialized (Mock)"
}

status_message = provider_status.get(current_provider, f"🧠 {current_provider.title()} AI Provider initialized")
print(f"✅ {status_message}")