import uuid
import asyncio
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from .connection_manager import manager
from .. import crud, schemas

# In-memory job store - replace with Redis for production
job_manager: Dict[str, Dict] = {}

async def run_storyboard_generation_task(job_id: str, project_id: uuid.UUID, scene_ids: List[uuid.UUID], db: Session):
    """
    The ASYNCHRONOUS background task that generates storyboard images.
    """

    total_scenes = len(scene_ids)
    
    for i, scene_id in enumerate(scene_ids, 1):
        if job_manager.get(job_id, {}).get("cancelled", False):
            await manager.send_json(job_id, {"event": "JOB_CANCELLED"})
            break
        
        try:
            storyboard = crud.create_storyboard_for_scene(db, project_id, scene_id)
            # Directly await the async send_json method
            await manager.send_json(job_id, {
                "event": "IMAGE_GENERATED",
                "progress": f"{i}/{total_scenes}",
                "storyboard": schemas.StoryboardImage.from_orm(storyboard).model_dump(mode='json')
            })
        except Exception as e:
            await manager.send_json(job_id, {"event": "ERROR", "scene_id": str(scene_id), "detail": str(e)})

    await manager.send_json(job_id, {"event": "JOB_COMPLETED"})
    job_manager.pop(job_id, None)

async def run_animatic_generation_task(job_id: str, project_id: uuid.UUID, scene_ids: List[uuid.UUID], db: Session):
    """
    The ASYNCHRONOUS background task that generates animatic videos.
    """
    print("run_animatic_generation_task called")
    total_scenes = len(scene_ids)
    
    for i, scene_id in enumerate(scene_ids, 1):
        if job_manager.get(job_id, {}).get("cancelled", False):
            await manager.send_json(job_id, {"event": "JOB_CANCELLED"})
            break
        
        try:
            print(f"[{i}/{total_scenes}] Generating animatic for scene: {scene_id}")
            # Call the corresponding CRUD function for animatics
            animatic = await crud.create_animatics_for_scene(
                db,
                project_id,
                scene_id
            )
            await manager.send_json(job_id, {
                "event": "VIDEO_GENERATED", # Use a distinct event name
                "progress": f"{i}/{total_scenes}",
                "animatic": schemas.AnimaticsScene.from_orm(animatic).model_dump(mode='json')
            })
        except Exception as e:
            await manager.send_json(job_id, {"event": "ERROR", "scene_id": str(scene_id), "detail": str(e)})

    await manager.send_json(job_id, {"event": "JOB_COMPLETED"})
    job_manager.pop(job_id, None)





