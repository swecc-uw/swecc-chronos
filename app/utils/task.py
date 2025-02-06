from app.core.config import settings
from app.models.container import convert_health_metric_to_dynamo
from app.services.docker_service import DockerService
from app.services.dynamodb_service import db
from app.services.data.data_compact import DataCompactManager
from app.services.data.prune_exited import PruneExitedAfterDays
from app.services.data.reduce_by_ten import ReduceByTenForEachContainer

import logging
from datetime import datetime, timedelta

docker_service = DockerService()
logger = logging.getLogger(__name__)
compact_manager = DataCompactManager([PruneExitedAfterDays(), ReduceByTenForEachContainer()])

def compact_data_task():
    logger.info("Running compacting data task")
    two_weeks_ago = datetime.now() - timedelta(weeks=2)
    old_items = db.get_items_older_than("health_metrics", two_weeks_ago)
    logger.info(f"Found {len(old_items)} items older than two weeks")
    compacted_items = compact_manager.compact(old_items)
    db.delete_bulk_items("health_metrics", old_items)
    logger.info(f"Deleted {len(old_items)} items")
    logger.info(f"Adding {len(compacted_items)} items")
    for item in compacted_items:
        db.add_item_to_table("health_metrics", item.model_dump())


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


MAPPING_TASKS_TO_ID = {
    update_to_db_task: settings.POLL_DATA_JOB_ID,
    compact_data_task: settings.COMPACT_DATA_JOB_ID,
}