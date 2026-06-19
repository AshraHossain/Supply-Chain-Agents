#!/bin/bash
# Deployment script for supply-chain-agents

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Supply Chain Agents - Deployment Script${NC}"

# Check environment
if [ -z "$DEPLOYMENT_ENV" ]; then
    echo -e "${RED}Error: DEPLOYMENT_ENV not set (dev/staging/prod)${NC}"
    exit 1
fi

# Check required environment variables
required_vars=("LLM_PROVIDER" "LLM_MODEL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}Error: $var not set${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓ Environment: $DEPLOYMENT_ENV${NC}"
echo -e "${GREEN}✓ LLM Provider: $LLM_PROVIDER${NC}"
echo -e "${GREEN}✓ LLM Model: $LLM_MODEL${NC}"

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
LLM_PROVIDER=mock pytest tests/ -v --tb=short

# Run linting
echo -e "${YELLOW}Running linting...${NC}"
black --check app tests
isort --check-only app tests
flake8 app tests

echo -e "${GREEN}✓ All checks passed${NC}"

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t supply-chain-agents:latest .

if [ "$DEPLOYMENT_ENV" = "prod" ]; then
    echo -e "${YELLOW}Building production image...${NC}"
    docker build -t supply-chain-agents:prod .

    echo -e "${YELLOW}Running health check...${NC}"
    docker run --rm \
        -e LLM_PROVIDER=mock \
        --name supply-chain-test \
        supply-chain-agents:prod \
        bash -c "sleep 2 && python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\"" || \
        echo -e "${RED}Health check failed${NC}"
fi

echo -e "${GREEN}✓ Deployment preparation complete${NC}"
echo -e "${YELLOW}Ready to push to registry or deploy to cloud${NC}"
