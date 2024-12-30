from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DOCKER_SOCKET: str = "/var/run/docker.sock"

settings = Settings()