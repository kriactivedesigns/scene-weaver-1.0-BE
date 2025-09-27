import uuid
import asyncio
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from .connection_manager import manager
from .. import crud, schemas

# In-memory job store - replace with Redis for production
job_manager: Dict[str, Dict] = {}

def run_storyboard_generation_task(
    job_id: str, 
    project_id: uuid.UUID, 
    scene_ids: List[uuid.UUID],
    db: Session
):
    """The background task that generates storyboard images."""
    total_scenes = len(scene_ids)
    
    # Helper to run async code from this sync function
    def send_ws_update(update_message):
        asyncio.run(manager.send_json(job_id, update_message))

    for i, scene_id in enumerate(scene_ids):
        if job_manager.get(job_id, {}).get("cancelled", False):
            send_ws_update({"event": "JOB_CANCELLED"})
            break
        
        try:
            storyboard = crud.create_storyboard_for_scene(db, project_id, scene_id)
            send_ws_update({
                "event": "IMAGE_GENERATED",
                "progress": f"{i+1}/{total_scenes}",
                # Convert the ORM object to a Pydantic model, then to a dict
                "storyboard": schemas.StoryboardImage.from_orm(storyboard).model_dump(mode='json')
            })
        except Exception as e:
            send_ws_update({"event": "ERROR", "scene_id": str(scene_id), "detail": str(e)})

    send_ws_update({"event": "JOB_COMPLETED"})
    job_manager.pop(job_id, None)
