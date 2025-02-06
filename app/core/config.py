from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DOCKER_SOCKET: str = "/var/run/docker.sock"
    HEALTH_METRICS_TABLE: str = "health_metrics"
    POLL_DATA_JOB_ID: str = "collect_metrics_and_sent_to_db"
    COMPACT_DATA_JOB_ID: str = "compact_data_and_update_db"
    CLEAN_UP_EVENTS_JOB_ID: str = "delete_docker_data"

settings = Settings()