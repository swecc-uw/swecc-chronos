# Chronos - Lightweight Observability for Docker Hosts

Chronos is a lightweight service designed to collect and monitor metrics from Docker containers, providing real-time insights with flexible data management.

## 🚀 Features

- **Real-Time Event Tracking:** Monitor Docker events as they happen.
- **Customizable Cadence Policies:** Adjust data collection frequency to optimize performance and storage.
- **Controllable Collection Tasks:** Control specific collections task to fit your needs.

## 🌍 Environment Variables

Ensure the following environment variables are set:

```bash
AWS_ACCESS_KEY_ID=<your-access-key>
AWS_SECRET_ACCESS_KEY=<your-secret-key>
AWS_DEFAULT_REGION=<your-region>
```

## 🐳 Running Chronos

1. **Create the `swecc_default` Docker network:**
   ```bash
   docker network create swecc_default
   ```

2. **Start the service with Docker Compose:**
   ```bash
   docker compose up
   ```

## 🔧 Customizing Docker Network

For deployments outside the SWECC club, you can modify the Docker Compose file to use a different network:

1. **Open `docker-compose.yml`.**  
2. Replace `swecc-default` with your preferred network name:

```yaml
version: '3.8'

services:
  chronos:
    tty: true
    build: .
    networks:
      - your-custom-network  # Replace with your network name
    volumes:
      - .:/app
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "8002:8002"
    environment:
      AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
      AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
      AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION}

networks:
  your-custom-network:  # Replace with your network name
    external: true
    name: your-custom-network
```

**Note:** Keep `swecc_default` for SWECC club deployments.

## 🧪 Running Tests

Execute the test suite with:

```bash
python -m app.test.<test>
```

---

README revamp credit - GPT-4-turbo
Contributions are welcome! Feel free to submit issues or pull requests to help improve Chronos.

