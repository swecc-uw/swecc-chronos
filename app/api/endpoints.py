from fastapi import APIRouter, HTTPException
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