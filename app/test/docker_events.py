from app.models.container import convert_raw_event_to_docker_event
from app.test.mock_data.docker_events import DOCKER_EVENT_MOCK_DATA

for event in DOCKER_EVENT_MOCK_DATA:
    docker_event = convert_raw_event_to_docker_event(event)
    print(docker_event)
