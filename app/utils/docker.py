from app.models.container import DockerEventType, convert_raw_event_to_docker_event
from app.services.dynamodb_service import db
import logging

from app.utils.task import update_to_db_task
logger = logging.getLogger(__name__)

def callback_from_docker_events(event):
    """Callback function to handle Docker events."""
    logger.info(f"Received Docker event: {event.get('Action')} {event.get('Type')}")

    docker_events = convert_raw_event_to_docker_event(event)
    # print(docker_events)

    if(docker_events.type == DockerEventType.CONTAINER):
        logger.info(f"Polling again for container stats")
        update_to_db_task()

    # Update event to db
    try:
        dynam_docker_events = docker_events.to_dynamo_item()
        db.add_item_to_table("docker_events", dynam_docker_events)
    except Exception as e:
        logger.error(f"Error adding item to table: {e}")