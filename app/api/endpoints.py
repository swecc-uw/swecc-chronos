from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.docker_service import DockerService
from app.services.dynamodb_service import db
from app.models.container import ContainerStats, JobItem
from app.utils.scheduler import Scheduler
from app.core.config import settings
from typing import List

router = APIRouter()
docker_service = DockerService()


@router.get("/raw-usage", response_model=List[ContainerStats], tags=["containers"])
async def get_container_usage():
    try:
        return docker_service.poll_all_container_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/status", tags=["containers"])
async def get_container_status():
    return docker_service.get_all_containers_live_status()

@router.get("/container/{container_name}", tags=["containers"])
async def get_container_metadata_by_name(container_name: str):
    try:
        return docker_service.get_container_metadata(container_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/usage", tags=["containers"])
async def get_recent_usage():
    try:
        return db.get_recent_items_from_table(settings.HEALTH_METRICS_TABLE)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage/{container_name}", tags=["containers"])
async def get_recent_usage_by_container_name(container_name: str):
    try:
        return db.get_recent_items_by_container_name(settings.HEALTH_METRICS_TABLE, container_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/usage/{container_name}/all", tags=["containers"])
async def get_all_usage_by_container_name(container_name: str):
    try:
        return db.get_all_items_by_container_name(settings.HEALTH_METRICS_TABLE, container_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/poll/pause", tags=["scheduler"])
async def pause_polling(job_item: JobItem):
    scheduler = Scheduler()
    jobs = scheduler.list_jobs()
    if(job_item.id in jobs):
        scheduler.pause_job(job_item.id)
        return {"message": f"Job {job_item.id} paused"}
    else:
        raise HTTPException(status_code=404, detail="Job not found")

@router.post("/poll/resume", tags=["scheduler"])
async def resume_polling(job_item: JobItem):
    scheduler = Scheduler()
    jobs = scheduler.list_jobs()
    if(job_item.id in jobs):
        scheduler.resume_job(job_item.id)
        return {"message": f"Job {job_item.id} resumed"}
    else:
        raise HTTPException(status_code=404, detail="Job not found")
    
@router.get("/job/{job_id}/status", tags=["scheduler"])
async def get_job_status(job_id: str):
    scheduler = Scheduler()
    return {"status": scheduler.get_job_status(job_id)}

@router.post("/poll", tags=["containers"])
async def poll_container_stats(background_tasks: BackgroundTasks):
    background_tasks.add_task(docker_service.poll_all_container_stats)
    return {"message": "Polling started in the background"}