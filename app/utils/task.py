from app.models.container import convert_health_metric_to_dynamo
from app.services.docker_service import DockerService
from app.services.dynamodb_service import db
import logging

docker_service = DockerService()
logger = logging.getLogger(__name__)

def update_to_db_task():
    print("Updating to db task")
    stats = docker_service.poll_all_container_stats()
    dynamodb_stats = [convert_health_metric_to_dynamo(stat) for stat in stats]

    for stat in dynamodb_stats:
        logger.info(f"Adding item to table: {stat}")
        try:
            db.add_item_to_table("health_metrics", stat.model_dump())
        except Exception as e:
            logger.info(f"Error adding item to table: {e}")

def hidden_task():
    print("This is a hidden task")

def expose_tasks():
    print("This is an exposed task")