# Deployment Guide

Guide for running the supply chain agent in various environments.

## Local Development

### Prerequisites
- Python 3.11+
- pip or uv

### Setup

```bash
git clone https://github.com/AshraHossain/Supply-Chain-Agents
cd Supply-Chain-Agents
pip install -r requirements.txt
cp .env.example .env
```

### Run Demo

Test the full workflow with mock LLM (no API key):

```bash
LLM_PROVIDER=mock python run_demo.py
```

Or with a specific SKU:

```bash
LLM_PROVIDER=mock python run_demo.py SKU-MILK-1L
```

### Run Tests

```bash
LLM_PROVIDER=mock pytest tests/ -v
```

### Start API Server

```bash
LLM_PROVIDER=mock uvicorn app.main:app --reload --port 8000
```

Then test:

```bash
curl http://localhost:8000/health
```

---

## Docker (Recommended)

### Prerequisites
- Docker
- Docker Compose

### Quick Start (mock LLM)

```bash
docker compose up --build
```

API will be at `http://localhost:8000`

### With Real LLM

```bash
LLM_PROVIDER=openrouter \
OPENROUTER_API_KEY=sk-or-v1-... \
LLM_MODEL=anthropic/claude-sonnet-4.5 \
docker compose up --build
```

### Docker Compose Services

Default `docker-compose.yml` includes:
- **api** — FastAPI server (port 8000)

Optional services you can add:
- **postgres** — For persistent checkpointing (instead of in-memory)
- **redis** — For caching & rate limiting

---

## Cloud Platforms

### AWS (EC2 + ECS)

**Option 1: EC2 with Docker**

1. Launch EC2 instance (t3.medium recommended)
2. Install Docker
3. Clone repo
4. Set environment variables in `/etc/environment`
5. Run: `docker compose up -d`

**Option 2: ECS (Fargate)**

1. Build and push Docker image to ECR:
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t supply-chain-agents .
   docker tag supply-chain-agents:latest <account>.dkr.ecr.us-east-1.amazonaws.com/supply-chain-agents:latest
   docker push <account>.dkr.ecr.us-east-1.amazonaws.com/supply-chain-agents:latest
   ```

2. Create ECS task definition (see below)
3. Create ECS service
4. Attach ALB (Application Load Balancer)

**ECS Task Definition Example:**
```json
{
  "family": "supply-chain-agents",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "<account>.dkr.ecr.us-east-1.amazonaws.com/supply-chain-agents:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LLM_PROVIDER",
          "value": "openrouter"
        },
        {
          "name": "LLM_MODEL",
          "value": "anthropic/claude-sonnet-4.5"
        }
      ],
      "secrets": [
        {
          "name": "OPENROUTER_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account>:secret:openrouter-key"
        }
      ]
    }
  ]
}
```

### Google Cloud (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/supply-chain-agents

# Deploy
gcloud run deploy supply-chain-agents \
  --image gcr.io/PROJECT_ID/supply-chain-agents \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars LLM_PROVIDER=openrouter,LLM_MODEL=anthropic/claude-sonnet-4.5 \
  --set-secrets OPENROUTER_API_KEY=openrouter-key:latest
```

### Heroku

```bash
git push heroku main

# Set environment variables
heroku config:set LLM_PROVIDER=openrouter
heroku config:set LLM_MODEL=anthropic/claude-sonnet-4.5
heroku config:set OPENROUTER_API_KEY=sk-or-v1-...
```

---

## Kubernetes

### Prerequisites
- `kubectl` configured
- Container registry (Docker Hub, ECR, GCR, etc.)

### Deployment YAML

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: supply-chain-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: supply-chain-agents
  template:
    metadata:
      labels:
        app: supply-chain-agents
    spec:
      containers:
      - name: api
        image: <registry>/supply-chain-agents:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM_PROVIDER
          value: "openrouter"
        - name: LLM_MODEL
          value: "anthropic/claude-sonnet-4.5"
        - name: OPENROUTER_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openrouter-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: supply-chain-agents
spec:
  type: LoadBalancer
  selector:
    app: supply-chain-agents
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
```

### Deploy

```bash
# Create secret
kubectl create secret generic llm-secrets --from-literal=openrouter-key=sk-or-v1-...

# Apply manifests
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods
kubectl get svc
```

---

## Scaling

### Horizontal Scaling
- Increase `replicas` in deployment
- Each instance has independent memory (no shared state between replicas)
- Use load balancer for traffic distribution

### Vertical Scaling
- Increase `memory` and `cpu` in deployment
- Allows more concurrent workflows per instance

### Database Checkpoint (for state persistence)

By default, state is stored in memory. For multi-instance setups, persist to Postgres:

```bash
pip install langgraph-checkpoint-postgres
```

In `app/graph.py`, replace:
```python
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
```

With:
```python
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg

def get_checkpointer():
    conn_string = "postgresql://user:password@localhost/langgraph"
    return PostgresSaver(
        conn=psycopg.connect(conn_string),
        table_name="checkpoints"
    )

checkpointer = get_checkpointer()
```

---

## Monitoring

### Health Checks

All deployment targets should monitor the `/health` endpoint:

```bash
curl http://localhost:8000/health
```

### Logging

The API logs to stdout. Capture logs with:

```bash
# Docker
docker logs <container_id>

# Kubernetes
kubectl logs <pod_name>

# Cloud Run
gcloud run logs read supply-chain-agents
```

### Metrics (Future)

Consider adding:
- Request latency histogram
- LLM token usage (cost tracking)
- Approval rate (how many orders require human review)
- Order fulfillment SLA

---

## Security

### API Authentication (Future)

Current API is open. For production, add:
- API key authentication
- OAuth2 / JWT
- IP whitelisting
- Rate limiting

### Environment Variables

Never commit `.env` or credentials. Use:
- GitHub Secrets (for CI/CD)
- Cloud provider secret management (AWS Secrets Manager, GCP Secret Manager)
- Environment variable files (never in git)

### API Key Rotation

Regularly rotate LLM API keys:
1. Generate new key in provider console
2. Update secret
3. Revoke old key

---

## Troubleshooting

**Container fails to start:**
```
docker logs <container_id>
```

Check for missing environment variables or invalid API keys.

**High latency:**
- Increase container memory (LLM inference is memory-intensive)
- Use a faster model (gpt-4o-mini vs gpt-4)
- Increase replicas and use load balancer

**API key not working:**
- Verify key is set correctly (no extra spaces)
- Check key hasn't been revoked in provider console
- Ensure right provider is selected in LLM_PROVIDER

---

## Next Steps

- Set up monitoring & alerting
- Add database persistence for checkpoints
- Implement API authentication
- Create deployment automation (GitHub Actions → cloud)
- Set up cost tracking for LLM usage
