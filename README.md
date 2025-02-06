# Chronos - Observability for Docker Hosts

A service for collecting and monitoring metrics from Docker containers.

**Features:**

Tracks Docker events in real-time

Customizable cadence policies for decreasing data cadence stored

Controllable collection tasks for flexibility

## env

Need

AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION

## Run

Create the `swecc_default` network.

```bash
docker compose up
```

```test
python -m app.test.<test>
```