# Chronos - Observability for Docker Hosts

A service for collecting and monitoring metrics from Docker containers.

## 🚀 Features

- **Real-Time Event Tracking:** Monitor Docker events as they happen.
- **Customizable Cadence Policies:** Adjust data collection frequency to optimize performance and storage.
- **Controllable Collection Tasks:** Control specific collections task to fit your needs.


## 🐳 Running Chronos

### Environment Variables

To set up the necessary environment variables for DynamoDB, you need to provide the following keys:

```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=your_aws_region
```

See more at [Setting up DynamoDB (web service)](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SettingUp.DynamoWebService.html)

### From source

Step 1: Clone the repo

```bash
git clone "https://github.com/swecc-uw/swecc-chronos.git"
```

Step 2 (Optional): Create your Docker network. For other service to make request to this it must be within a network. Use `swecc_default` for SWECC related development. More [below](#-customizing-docker-network)

```bash
docker network create <your network name>
```

Step 3 (Optional): Add any service that communicate with this service to the network
```bash
docker network connect <your network name> <your container name>
```

*Note: If you use your custom network rather than `swecc_default`, make sure to update `docker-compose.yaml` before continue*

Step 4: Set up python env. Active then add the previous DynamoDB key to your enviroment.

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=your_aws_region
```

*Note: Ensure that your Docker daemon is running before executing the following commands.*  

## Quick start

### Docker
```bash
docker compose up
```

### Locally
```bash
python uvicorn app.main:app --host 0.0.0.0 --port 8002
```

Check your server running at port 8002
```bash
curl "http://localhost:8002/health"
```

### Test

```
python -m app.test.<test>
```

### 🔧 Customizing Docker Network

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

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Credit
README revamp credit - GPT-4-turbo Contributions are welcome! Feel free to submit issues or pull requests to help improve Chronos.