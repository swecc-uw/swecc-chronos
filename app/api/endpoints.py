from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.docker_service import DockerService
from app.models.container import ContainerStats
from typing import List

router = APIRouter()
docker_service = DockerService()

@router.get("/usage", response_model=List[ContainerStats], tags=["containers"])
async def get_container_usage():
    try:
        return docker_service.poll_all_container_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/poll", tags=["containers"])
async def poll_container_stats(background_tasks: BackgroundTasks):
    background_tasks.add_task(docker_service.poll_all_container_stats)
    return {"message": "Polling started in the background"}