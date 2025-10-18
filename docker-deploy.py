import subprocess
import sys

# --- Configuration ---
# TODO: Update these two variables with your specific GCP details.
REGION = "us-central1"
PROJECT_ID = "sceneweaver-1"

# --- Static Configuration ---
# These are unlikely to change for this project.
REPOSITORY_NAME = "sceneweaver-services"
LOCAL_IMAGE_NAME = "sceneweaver-backend"
REMOTE_IMAGE_NAME = "backend"
TAG = "latest"

# --- Script Logic ---

def run_command(command):
    """Executes a shell command and exits if it fails."""
    print(f"🚀 Running command: {command}")
    try:
        subprocess.run(command, shell=True, check=True, text=True)
        print("✅ Command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing command: {command}", file=sys.stderr)
        print(e, file=sys.stderr)
        sys.exit(1)

def main():
    """Main function to build, tag, and push the Docker image."""
    
    # Construct the full, unique image name for Artifact Registry
    full_image_name = (
        f"{REGION}-docker.pkg.dev/{PROJECT_ID}/"
        f"{REPOSITORY_NAME}/{REMOTE_IMAGE_NAME}:{TAG}"
    )
    
    print("-" * 60)
    print(f"🐳 Starting deployment for image: {full_image_name}")
    print("-" * 60)
    
    # 1. Build the Docker image from the Dockerfile in the current directory
    run_command(f"docker build --no-cache -t {LOCAL_IMAGE_NAME} .")
    
    # 2. Tag the local image with the full Artifact Registry name
    run_command(f"docker tag {LOCAL_IMAGE_NAME} {full_image_name}")
    
    # 3. Push the tagged image to your private Artifact Registry
    run_command(f"docker push {full_image_name}")
    
    print("\n🎉 --- Deployment script finished successfully! --- 🎉")
    print(f"Image '{full_image_name}' is now in Artifact Registry.")
    print("You can now deploy a new revision in Cloud Run.")
    print("-" * 60)

if __name__ == "__main__":
    main()
