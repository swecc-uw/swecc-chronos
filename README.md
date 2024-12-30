# Chronos - Observability for docker

## Run

```bash
docker run -v /var/run/docker.sock:/var/run/docker.sock -p 8002:8002 $(docker build -q .)
```