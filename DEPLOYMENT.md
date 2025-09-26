# Deployment Guide

## Streamlit Cloud Deployment

### Prerequisites
- GitHub repository
- Streamlit Cloud account

### Steps
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New App"
4. Select your repository and branch
5. Set main file path: `dashboard.py`
6. Click "Deploy"

### Environment Variables (if needed)
```
POSTGRES_HOST=your_postgres_host
MINIO_ENDPOINT=your_minio_endpoint
REDIS_HOST=your_redis_host
```

## Heroku Deployment

### Setup
```bash
# Install Heroku CLI
# Create Heroku app
heroku create your-app-name

# Set Python buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main
```

### Environment Variables
```bash
heroku config:set POSTGRES_HOST=your_postgres_host
heroku config:set MINIO_ENDPOINT=your_minio_endpoint
```

## Docker Deployment

### Build Streamlit Image
```bash
docker build -f Dockerfile.streamlit -t streamlit-dashboard .
```

### Run Container
```bash
docker run -p 8501:8501 streamlit-dashboard
```

## AWS ECS Deployment

### Task Definition
```json
{
  "family": "streamlit-dashboard",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "streamlit-dashboard",
      "image": "your-registry/streamlit-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ]
    }
  ]
}
```

## Local Development

### Run with custom port
```bash
streamlit run dashboard.py --server.port 8501
```

### Run with configuration
```bash
streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
```