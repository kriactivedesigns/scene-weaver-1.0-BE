import uuid
import asyncio
from typing import List, Dict
from sqlalchemy.orm import Session
from .connection_manager import manager
from .. import schemas
from ..api.v1.crud.storyboard import create_storyboard_for_scene
from ..api.v1.crud.animatics import create_animatics_for_scene

# In-memory job store - replace with Redis for production
job_manager: Dict[str, Dict] = {}

async def run_storyboard_generation_task(job_id: str, project_id: uuid.UUID, scene_ids: List[uuid.UUID], db: Session):
    """
    The ASYNCHRONOUS background task that generates storyboard images.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    total_scenes = len(scene_ids)
    logger.info(f"Starting storyboard generation job {job_id} for {total_scenes} scenes")
    
    # Add a small delay to ensure WebSocket connection is established
    await asyncio.sleep(0.5)
    
    # Send initial status to confirm job has started
    await manager.send_json(job_id, {
        "event": "GENERATION_IN_PROGRESS",
        "total_scenes": total_scenes,
        "message": f"Starting storyboard generation for {total_scenes} scenes"
    })
    
    try:
        for i, scene_id in enumerate(scene_ids, 1):
            # Check if job was cancelled
            if job_manager.get(job_id, {}).get("cancelled", False):
                await manager.send_json(job_id, {"event": "JOB_CANCELLED"})
                logger.info(f"Storyboard generation job {job_id} was cancelled")
                break
            
            try:
                logger.info(f"Processing scene {i}/{total_scenes} for job {job_id}")
                storyboard = await create_storyboard_for_scene(db, project_id, scene_id)
                
                # Send success notification
                await manager.send_json(job_id, {
                    "event": "IMAGE_GENERATED",
                    "progress": f"{i}/{total_scenes}",
                    "scene_id": str(scene_id),
                    "storyboard": schemas.StoryboardImage.from_orm(storyboard).model_dump(mode='json')
                })
                
            except Exception as scene_error:
                logger.error(f"Critical error in scene {scene_id} for job {job_id}: {str(scene_error)}")
                
                # Send ERROR event so frontend can call cancel API
                await manager.send_json(job_id, {
                    "event": "ERROR", 
                    "scene_id": str(scene_id),
                    "scene_number": i,
                    "total_scenes": total_scenes,
                    "detail": str(scene_error),
                    "message": f"Failed at scene {i} of {total_scenes}. Please cancel remaining scenes."
                })
                
                logger.error(f"Storyboard generation job {job_id} failed at scene {i}")
                # Don't clean up here - let the frontend call cancel API
                return
        
        # If we get here, all scenes completed successfully
        await manager.send_json(job_id, {"event": "JOB_COMPLETED"})
        logger.info(f"Storyboard generation job {job_id} completed successfully")
        
    except Exception as job_error:
        # Handle any unexpected errors at the job level
        logger.error(f"Unexpected error in storyboard generation job {job_id}: {str(job_error)}")
        await manager.send_json(job_id, {
            "event": "ERROR",
            "detail": str(job_error),
            "message": "Unexpected error occurred. Please cancel the job."
        })
    
    finally:
        # Always clean up the job from memory
        job_manager.pop(job_id, None)

async def run_animatic_generation_task(job_id: str, project_id: uuid.UUID, scene_ids: List[uuid.UUID], db: Session):
    """
    The ASYNCHRONOUS background task that generates animatic videos.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    total_scenes = len(scene_ids)
    logger.info(f"Starting animatic generation job {job_id} for {total_scenes} scenes")
    
    # Add a small delay to ensure WebSocket connection is established
    await asyncio.sleep(0.5)
    
    # Send initial status to confirm job has started
    await manager.send_json(job_id, {
        "event": "GENERATION_IN_PROGRESS",
        "total_scenes": total_scenes,
        "message": f"Starting animatic generation for {total_scenes} scenes"
    })
    
    try:
        for i, scene_id in enumerate(scene_ids, 1):
            # Check if job was cancelled
            if job_manager.get(job_id, {}).get("cancelled", False):
                await manager.send_json(job_id, {"event": "JOB_CANCELLED"})
                logger.info(f"Animatic generation job {job_id} was cancelled")
                break
            
            try:
                logger.info(f"Processing animatic scene {i}/{total_scenes} for job {job_id}")
                # Call the corresponding CRUD function for animatics
                animatic = await create_animatics_for_scene(
                    db,
                    project_id,
                    scene_id
                )
                
                # Send success notification
                await manager.send_json(job_id, {
                    "event": "VIDEO_GENERATED", # Use a distinct event name
                    "progress": f"{i}/{total_scenes}",
                    "scene_id": str(scene_id),
                    "animatic": schemas.AnimaticsScene.from_orm(animatic).model_dump(mode='json')
                })
                
            except Exception as scene_error:
                logger.error(f"Critical error in animatic scene {scene_id} for job {job_id}: {str(scene_error)}")
                
                # Send ERROR event so frontend can call cancel API
                await manager.send_json(job_id, {
                    "event": "ERROR", 
                    "scene_id": str(scene_id),
                    "scene_number": i,
                    "total_scenes": total_scenes,
                    "detail": str(scene_error),
                    "message": f"Failed at scene {i} of {total_scenes}. Please cancel remaining scenes."
                })
                
                logger.error(f"Animatic generation job {job_id} failed at scene {i}")
                # Don't clean up here - let the frontend call cancel API
                return

        # If we get here, all scenes completed successfully
        await manager.send_json(job_id, {"event": "JOB_COMPLETED"})
        logger.info(f"Animatic generation job {job_id} completed successfully")
        
    except Exception as job_error:
        # Handle any unexpected errors at the job level
        logger.error(f"Unexpected error in animatic generation job {job_id}: {str(job_error)}")
        await manager.send_json(job_id, {
            "event": "ERROR",
            "detail": str(job_error),
            "message": "Unexpected error occurred. Please cancel the job."
        })
    
    finally:
        # Always clean up the job from memory
        job_manager.pop(job_id, None)





