# Deployment Guide - DataSentinel

This document provides comprehensive deployment instructions for DataSentinel and the generated validation services.

---

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Using DataSentinel CLI](#using-datasentinel-cli)
3. [Deploying Generated Services](#deploying-generated-services)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment](#cloud-deployment)
6. [Production Considerations](#production-considerations)

---

## Local Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git
- Docker (optional, for containerized deployment)

### Installation

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/DataSentinel.git
cd DataSentinel
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing and development)
pip install -r requirements-dev.txt
```

#### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Example `.env` file:**

```env
# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# API Configuration
DEFAULT_TIMEOUT=30
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=2.0

# Generation Configuration
OUTPUT_DIR=./output
TEMPLATE_DIR=./templates

# Optional: Authentication for parsing remote APIs
# API_KEY=your_api_key_here
# BEARER_TOKEN=your_bearer_token_here
```

#### 5. Verify Installation

```bash
# Run tests to verify installation
pytest tests/ -v

# Check CLI is working
python auto_sentinel.py --help
```

---

## Using DataSentinel CLI

### Basic Usage

#### Generate from OpenAPI Specification

```bash
python auto_sentinel.py \
  --input-type openapi \
  --source examples/openapi/petstore.yaml \
  --output ./output/petstore \
  --project-name petstore
```

#### Generate from GraphQL Endpoint

```bash
python auto_sentinel.py \
  --input-type graphql \
  --source https://api.spacex.land/graphql \
  --output ./output/spacex \
  --project-name spacex
```

#### Generate from JSON Sample

```bash
python auto_sentinel.py \
  --input-type json \
  --source examples/json/user_sample.json \
  --output ./output/user_api \
  --project-name user_api
```

### Advanced Options

#### With Authentication

```bash
# API Key authentication
python auto_sentinel.py \
  --input-type openapi \
  --source https://api.example.com/openapi.json \
  --output ./output/example_api \
  --project-name example_api \
  --auth-type api_key \
  --auth-value "your_api_key_here"

# Bearer token authentication
python auto_sentinel.py \
  --input-type openapi \
  --source https://api.example.com/openapi.json \
  --output ./output/example_api \
  --project-name example_api \
  --auth-type bearer \
  --auth-value "your_bearer_token"
```

#### Selective Generation

```bash
# Skip test generation
python auto_sentinel.py \
  --input-type openapi \
  --source examples/openapi/petstore.yaml \
  --output ./output/petstore \
  --project-name petstore \
  --no-tests

# Skip Docker generation
python auto_sentinel.py \
  --input-type openapi \
  --source examples/openapi/petstore.yaml \
  --output ./output/petstore \
  --project-name petstore \
  --no-docker
```

#### Verbose Mode

```bash
python auto_sentinel.py \
  --input-type openapi \
  --source examples/openapi/petstore.yaml \
  --output ./output/petstore \
  --project-name petstore \
  --verbose
```

### Output Structure

After successful generation, you'll have:

```
output/petstore/
├── models.py           # Pydantic v2 models
├── validators.py       # Validation logic with retry
├── test_api.py        # Pytest test suite
├── app.py             # FastAPI application
├── data_dict.md       # Data dictionary documentation
├── Dockerfile         # Container definition
├── requirements.txt   # Python dependencies
└── README.md          # Generated project README
```

---

## Deploying Generated Services

### Running Generated Service Locally

#### 1. Navigate to Generated Project

```bash
cd output/petstore
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Run Tests

```bash
pytest test_api.py -v
```

#### 4. Start FastAPI Application

```bash
# Development mode with auto-reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 5. Access API Documentation

Open your browser to:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Using the Validation Service

#### Health Check

```bash
curl http://localhost:8000/health
```

#### Validate Endpoint

```bash
# Example: Validate user data
curl -X POST http://localhost:8000/validate/user/123 \
  -H "Content-Type: application/json"
```

---

## Docker Deployment

### Building Docker Image

#### 1. Build Image

```bash
cd output/petstore

# Build image
docker build -t petstore-validator:latest .
```

#### 2. Run Container

```bash
# Run container
docker run -d \
  --name petstore-validator \
  -p 8000:8000 \
  petstore-validator:latest

# View logs
docker logs -f petstore-validator

# Stop container
docker stop petstore-validator

# Remove container
docker rm petstore-validator
```

#### 3. Run with Environment Variables

```bash
docker run -d \
  --name petstore-validator \
  -p 8000:8000 \
  -e LOG_LEVEL=DEBUG \
  -e API_KEY=your_api_key \
  petstore-validator:latest
```

### Docker Compose

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  validator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
      - API_KEY=${API_KEY}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Usage:**

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Multi-Stage Build Optimization

The generated Dockerfile uses multi-stage builds for optimization:

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Cloud Deployment

### AWS Deployment

#### Option 1: AWS ECS (Elastic Container Service)

**1. Push Image to ECR**

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag image
docker tag petstore-validator:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/petstore-validator:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/petstore-validator:latest
```

**2. Create ECS Task Definition**

```json
{
  "family": "petstore-validator",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "validator",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/petstore-validator:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/petstore-validator",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**3. Create ECS Service**

```bash
aws ecs create-service \
  --cluster my-cluster \
  --service-name petstore-validator \
  --task-definition petstore-validator \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

#### Option 2: AWS Lambda (with Mangum adapter)

**1. Install Mangum**

```bash
pip install mangum
```

**2. Modify app.py**

```python
from mangum import Mangum

# Existing FastAPI app
app = FastAPI()

# Add Lambda handler
handler = Mangum(app)
```

**3. Deploy with AWS SAM**

```yaml
# template.yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  ValidatorFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: app.handler
      Runtime: python3.11
      MemorySize: 512
      Timeout: 30
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /{proxy+}
            Method: ANY
```

```bash
sam build
sam deploy --guided
```

### Google Cloud Platform (GCP)

#### Cloud Run Deployment

**1. Build and Push to GCR**

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Build image
docker build -t gcr.io/<project-id>/petstore-validator:latest .

# Push image
docker push gcr.io/<project-id>/petstore-validator:latest
```

**2. Deploy to Cloud Run**

```bash
gcloud run deploy petstore-validator \
  --image gcr.io/<project-id>/petstore-validator:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000 \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10
```

### Azure Deployment

#### Azure Container Instances

**1. Push to Azure Container Registry**

```bash
# Login to ACR
az acr login --name <registry-name>

# Tag image
docker tag petstore-validator:latest \
  <registry-name>.azurecr.io/petstore-validator:latest

# Push image
docker push <registry-name>.azurecr.io/petstore-validator:latest
```

**2. Deploy to ACI**

```bash
az container create \
  --resource-group myResourceGroup \
  --name petstore-validator \
  --image <registry-name>.azurecr.io/petstore-validator:latest \
  --cpu 1 \
  --memory 1 \
  --registry-login-server <registry-name>.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label petstore-validator \
  --ports 8000
```

---

## Production Considerations

### Security

#### 1. Environment Variables

Never hardcode secrets in code. Use environment variables:

```python
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_key: str = os.getenv("API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    
    class Config:
        env_file = ".env"
```

#### 2. HTTPS/TLS

Always use HTTPS in production:

```bash
# With Let's Encrypt and Certbot
certbot --nginx -d api.example.com
```

#### 3. Rate Limiting

Add rate limiting to prevent abuse:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/validate")
@limiter.limit("100/minute")
async def validate_endpoint():
    pass
```

### Monitoring

#### 1. Logging

Use structured logging:

```python
from loguru import logger

logger.add(
    "logs/app.log",
    rotation="500 MB",
    retention="10 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    serialize=True  # JSON format
)
```

#### 2. Metrics

Add Prometheus metrics:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

#### 3. Health Checks

Implement comprehensive health checks:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    # Check dependencies (database, external APIs, etc.)
    return {"status": "ready"}
```

### Performance

#### 1. Caching

Implement caching for validation results:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def validate_cached(data_hash: str):
    # Validation logic
    pass
```

#### 2. Connection Pooling

Use connection pooling for external APIs:

```python
import httpx

client = httpx.AsyncClient(
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    timeout=30.0
)
```

#### 3. Async Operations

Leverage async for I/O-bound operations:

```python
@app.post("/validate/batch")
async def validate_batch(items: List[Item]):
    tasks = [validate_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

### Scaling

#### Horizontal Scaling

Use load balancer with multiple instances:

```bash
# Docker Swarm
docker service create \
  --name petstore-validator \
  --replicas 3 \
  --publish 8000:8000 \
  petstore-validator:latest

# Kubernetes
kubectl scale deployment petstore-validator --replicas=5
```

#### Auto-scaling

Configure auto-scaling based on metrics:

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: petstore-validator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: petstore-validator
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 2. Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### 3. Docker Build Fails

```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t petstore-validator:latest .
```

#### 4. Memory Issues

```bash
# Increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory

# Or use memory limits in docker run
docker run -m 2g petstore-validator:latest
```

---

## Summary

This deployment guide provides:
- ✅ Local development setup instructions
- ✅ CLI usage examples for all input types
- ✅ Docker deployment with optimization
- ✅ Cloud deployment for AWS, GCP, Azure
- ✅ Production considerations (security, monitoring, performance)
- ✅ Scaling strategies
- ✅ Troubleshooting guide

**Next Steps:**
1. Set up local development environment
2. Generate your first validation service
3. Test locally with Docker
4. Deploy to your preferred cloud platform
5. Configure monitoring and alerts
6. Set up CI/CD pipeline for automated deployments