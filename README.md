# Chronos - Observability for Docker Hosts

## env

Need

AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION

## Run

```bash
docker run -v /var/run/docker.sock:/var/run/docker.sock -p 8002:8002 $(docker build -q .)
```
