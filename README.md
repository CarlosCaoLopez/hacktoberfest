# Drone Dispatch Controller with Chatbot Interface

Welcome to **MedicAir**, a **REST API** service for managing a fleet of drones capable of delivering medications. This system functions as a dispatch controller, allowing clients to register drones, load them with medications, and monitor their status and battery levels.

A simple front-end chat interface is also provided to interact with the API. This interface communicates with a chatbot built using **YepCode's Gemini** API.

To send and receive messages from the API, the chatbot connects through an **MQTT client**, enabling real-time communication between the system and the front-end.

## 🚀 Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Poetry](https://img.shields.io/badge/Poetry-464646?style=for-the-badge&logo=poetry&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![YepCode](https://img.shields.io/badge/YepCode-FFD700?style=for-the-badge&logo=appveyor&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-FF6600?style=for-the-badge&logo=eclipse-mosquitto&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-6CCFF6?style=for-the-badge&logo=gemini&logoColor=white)
![OpenAPI](https://img.shields.io/badge/OpenAPI-6CA0DC?style=for-the-badge&logo=openapiinitiative&logoColor=white)


## API Overview

This application implements a drone dispatch system as specified in the Drones-v1-kata requirements:

- **Fleet Management**: Control up to 10 drones with different weight capacities
- **Medication Delivery**: Load drones with medication items for delivery
- **Battery Monitoring**: Continuous monitoring with automatic alerts when battery is low
- **State Management**: Track drone states (IDLE, LOADING, LOADED, DELIVERING, DELIVERED, RETURNING)
- **Safety Controls**: Prevent overloading and loading when battery is below 25%

### Drone Models

- **Lightweight**: Lower capacity drones
- **Middleweight**: Medium capacity drones
- **Cruiserweight**: Higher capacity drones
- **Heavyweight**: Maximum capacity drones (up to 500gr)

## Prerequisites

- **Docker** (version 20.0 or higher)
- **Docker Compose** (version 2.0 or higher)


## Quick Start

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd hacktoberfest
```

### 2. Start All Services

```bash
docker compose build
docker compose up -d
```

This command will:

- Start MongoDB database with persistent storage
- Build and start the FastAPI application
- Configure networking between services
- Expose API on port 8000
- Set up MQTT broker for communication
- Launch the front-end chat interface

### 3. Verify Services

```bash
# Check running containers
docker compose ps

# View logs
docker compose logs <service_name>
```

### 4. Access the Services

- **API Base URL**: http://localhost:8000
- **Interactive Documentation**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json 
- **Front-end Chat Interface**: http://localhost:8001
- **MQTT Broker**: mqtt://localhost:1883

## Environment Configuration

The application uses environment-specific configurations that are described in the `.env.template` file. Copy this file to `.env` and adjust the settings as needed.

The Docker compose command automatically loads the `.env.docker` file for containerized deployments. The configuration for this file can be looked up on the `.env.docker.template` file.

## API Endpoints

All endpoints return data in JSON format as required by the specifications.

### Drone Management

#### Register a Drone

```http
POST /api/v1/drones/
Content-Type: application/json

{
  "serial_number": "DRONE_001",
  "model": "Heavyweight",
  "weight_limit": 500,
  "battery_capacity": 100
}
```

**Response**: Registered drone object with state set to IDLE

#### Get Available Drones

```http
GET /api/v1/drones/available
```

**Response**: List of drones available for loading (IDLE state, battery > 25%)

#### Check Drone Battery

```http
GET /api/v1/drones/{serialNumber}/battery
```

**Response**: Current battery level for the specified drone

### Medication Management

#### Load Drone with Medications

```http
POST /api/v1/drones/{serialNumber}/load
Content-Type: application/json

[
  {
    "name": "Aspirin_500mg",
    "weight": 50.5,
    "code": "ASP_500",
    "image": "https://example.com/aspirin.jpg"
  }
]
```

**Response**: Updated drone object with loaded medications

#### Get Loaded Medications

```http
GET /api/v1/drones/{serialNumber}/medications
```

**Response**: List of medications currently loaded on the specified drone

## Data Models

### Drone

```json
{
  "serial_number": "string (max 100 chars)",
  "model": "Lightweight|Middleweight|Cruiserweight|Heavyweight",
  "weight_limit": "number (0-500gr)",
  "battery_capacity": "number (0-100%)",
  "state": "IDLE|LOADING|LOADED|DELIVERING|DELIVERED|RETURNING",
  "medications": []
}
```

### Medication

```json
{
  "name": "string (letters, numbers, -, _ only)",
  "weight": "number (>0)",
  "code": "string (uppercase letters, numbers, _ only)",
  "image": "string (valid URL)"
}
```

## Safety Features

The system implements several safety measures as required:

1. **Weight Validation**: Prevents loading drones beyond their weight limit
2. **Battery Protection**: Blocks loading when battery is below 25%
3. **State Management**: Enforces proper state transitions
4. **Automatic Monitoring**: Periodic battery checks with audit logging

## Battery Monitoring

The system includes automatic battery monitoring that:

- Checks all drone batteries every 30 seconds
- Creates audit logs for battery level changes
- Sends alerts when battery levels are critically low
- Prevents loading operations on low-battery drones

## Database

### MongoDB Setup

The application uses MongoDB for data persistence:

- **Container**: `mongodb` (mongo:latest)
- **Port**: 27017
- **Credentials**: root/hacktoberfest
- **Persistence**: Data stored in `mongo-data` volume

### Data Preloading

The system is designed to accept initial data through the API endpoints. No dummy data is preloaded by default, but you can populate the database using the registration endpoints.

## Development

### Project Structure

```
.
├── .env                       # Local environment variables
├── .env.docker                # Environment variables for Docker
├── docker-compose.yml         # Docker services: MongoDB, MQTT, API, Frontend
├── Dockerfile                 # API container definition
├── drones.json                # Initial drone data
├── init-mongo.js              # MongoDB initialization script
├── pyproject.toml             # Poetry configuration
├── poetry.lock                # Locked dependencies
├── test_end_to_end.sh         # E2E test script
├── README.md
│
├── app/
│   ├── main.py                # FastAPI application entry point
│   ├── __init__.py
│   │
│   ├── core/                  # Core utilities
│   │   ├── database.py        # MongoDB connection
│   │   ├── logger.py          # Logging configuration
│   │   └── __init__.py
│   │
│   ├── models/                # Data models (Pydantic)
│   │   ├── drone.py           # Drone schema
│   │   ├── medication.py      # Medication schema
│   │   ├── error.py           # Error models and exceptions
│   │   └── __init__.py
│   │
│   ├── routes/                # FastAPI routers (endpoints)
│   │   ├── drones.py          # Drone endpoints
│   │   ├── medications.py     # Medication endpoints
│   │   └── __init__.py
│   │
│   ├── services/              # Business logic layer
│   │   ├── drone_service.py   # Drone management and validation
│   │   ├── battery_monitor.py # Background battery monitor
│   │   └── __init__.py
│   │
│   ├── mqtt/                  # MQTT integration
│   │   ├── consumer.py        # MQTT message consumer
│   │   ├── config/mosquitto.conf  # Broker configuration
│   │   ├── data/              # MQTT data directory (mounted volume)
│   │   ├── log/               # MQTT logs directory (mounted volume)
│   │   └── __init__.py
│   │
│   └── chatbot/               # Chatbot integration
│       ├── chatbot_client.py  # Chatbot client logic
│       ├── context_1.txt      # Chat context example
│       ├── context_2.txt
│       └── __init__.py
│
├── docs/
│   ├── api.yaml               # OpenAPI specification
│   └── Drones-v1-kata.pdf     # Original project description
│
├── front/                     # Streamlit frontend
│   ├── chat.py                # Streamlit UI entry point
│   └── Dockerfile             # Frontend container
│
├── logs/
│   └── battery_monitor.log    # Battery monitor log output
│
└── mqtt/
    └── config/
        └── mosquitto.conf     # External MQTT broker config
              # FastAPI application
```

### Local Development

```bash
# Install dependencies
poetry install

# Run locally (requires local MongoDB)
poetry run uvicorn app.main:app --reload

# Run with Docker for consistency
docker-compose up
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Use different port
docker-compose up -d --build --force-recreate
```

#### Database Connection Issues

```bash
# Check MongoDB logs
docker compose logs mongodb

# Restart MongoDB
docker compose restart mongodb
```

#### Build Issues

```bash
# Clean rebuild
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Health Checks

#### Verify API Health

```bash
curl http://localhost:8000/docs
```

#### Check Database Connection

```bash
docker compose exec mongodb mongosh -u root -p hacktoberfest
```

#### Monitor Logs

```bash
# Follow API logs
docker compose logs -f api

# Follow all logs
docker compose logs -f
```

## Production Deployment

For production deployment:

1. **Environment Variables**: Update `.env` and `.env.docker` with production values
2. **Security**: Change default MongoDB credentials
3. **Persistence**: Ensure volume backup strategy
4. **Monitoring**: Implement health checks and logging
5. **Scaling**: Consider load balancing for API service

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Create a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## API Documentation

For detailed API documentation with interactive examples, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

The API follows OpenAPI 3.0 specifications and provides comprehensive documentation for all endpoints, request/response schemas, and error codes.