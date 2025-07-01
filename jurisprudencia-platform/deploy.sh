#!/bin/bash

# Deploy script for Jurisprudência Platform

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default values
ENVIRONMENT=${1:-development}
REGISTRY=${DOCKER_REGISTRY:-"docker.io/jurisprudencia"}
TAG=${2:-latest}

echo -e "${GREEN}=== Jurisprudência Platform Deployment ===${NC}"
echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"
echo -e "${YELLOW}Registry: $REGISTRY${NC}"
echo -e "${YELLOW}Tag: $TAG${NC}"

# Function to check dependencies
check_dependencies() {
    echo -e "\n${YELLOW}Checking dependencies...${NC}"
    
    DEPS=("docker" "kubectl")
    if [ "$ENVIRONMENT" == "development" ]; then
        DEPS+=("docker-compose")
    fi
    
    for dep in "${DEPS[@]}"; do
        if ! command -v $dep &> /dev/null; then
            echo -e "${RED}Error: $dep is not installed${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}All dependencies are installed${NC}"
}

# Development deployment
deploy_development() {
    echo -e "\n${YELLOW}Deploying to development environment...${NC}"
    
    # Copy environment file
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env from .env.example${NC}"
        cp .env.example .env
    fi
    
    # Build and start containers
    docker-compose build
    docker-compose up -d
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for services to start...${NC}"
    sleep 10
    
    # Run database migrations
    echo -e "${YELLOW}Running database migrations...${NC}"
    docker-compose exec api alembic upgrade head
    
    # Show status
    docker-compose ps
    
    echo -e "${GREEN}Development deployment complete!${NC}"
    echo -e "API: http://localhost:8000"
    echo -e "Streamlit: http://localhost:8501"
    echo -e "Flower: http://localhost:5555"
}

# Production deployment
deploy_production() {
    echo -e "\n${YELLOW}Deploying to production environment...${NC}"
    
    # Build and push Docker image
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t $REGISTRY/api:$TAG .
    
    echo -e "${YELLOW}Pushing image to registry...${NC}"
    docker push $REGISTRY/api:$TAG
    
    # Update Kubernetes manifests with new image
    echo -e "${YELLOW}Updating Kubernetes manifests...${NC}"
    find k8s/ -name "*.yaml" -exec sed -i "s|jurisprudencia/api:latest|$REGISTRY/api:$TAG|g" {} \;
    
    # Apply Kubernetes manifests
    echo -e "${YELLOW}Applying Kubernetes manifests...${NC}"
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/configmap.yaml
    
    # Check if secrets exist, create if not
    if ! kubectl get secret jurisprudencia-secrets -n jurisprudencia &> /dev/null; then
        echo -e "${RED}Warning: Secrets not found. Please create k8s/secrets.yaml with production values${NC}"
        echo -e "${YELLOW}Using example secrets (NOT FOR PRODUCTION!)${NC}"
        kubectl apply -f k8s/secrets.yaml
    fi
    
    # Deploy infrastructure
    kubectl apply -f k8s/postgres.yaml
    kubectl apply -f k8s/redis.yaml
    
    # Wait for infrastructure
    echo -e "${YELLOW}Waiting for infrastructure...${NC}"
    kubectl wait --for=condition=ready pod -l app=postgres -n jurisprudencia --timeout=300s
    kubectl wait --for=condition=ready pod -l app=redis -n jurisprudencia --timeout=300s
    
    # Run database migrations
    echo -e "${YELLOW}Running database migrations...${NC}"
    kubectl run -n jurisprudencia migration --rm -i --restart=Never \
        --image=$REGISTRY/api:$TAG \
        --env="DATABASE_URL=postgresql://\$(DB_USER):\$(DB_PASSWORD)@postgres-service:5432/\$(DB_NAME)" \
        --command -- alembic upgrade head
    
    # Deploy applications
    kubectl apply -f k8s/api.yaml
    kubectl apply -f k8s/celery.yaml
    kubectl apply -f k8s/streamlit.yaml
    
    # Apply networking and scaling
    kubectl apply -f k8s/network-policy.yaml
    kubectl apply -f k8s/hpa.yaml
    kubectl apply -f k8s/ingress.yaml
    
    # Show deployment status
    echo -e "\n${YELLOW}Deployment status:${NC}"
    kubectl get deployments -n jurisprudencia
    kubectl get pods -n jurisprudencia
    kubectl get services -n jurisprudencia
    
    echo -e "\n${GREEN}Production deployment complete!${NC}"
}

# Rollback function
rollback() {
    echo -e "\n${YELLOW}Rolling back deployment...${NC}"
    
    if [ "$ENVIRONMENT" == "development" ]; then
        docker-compose down
    else
        # Kubernetes rollback
        kubectl rollout undo deployment/api -n jurisprudencia
        kubectl rollout undo deployment/celery-worker -n jurisprudencia
        kubectl rollout undo deployment/streamlit -n jurisprudencia
    fi
    
    echo -e "${GREEN}Rollback complete${NC}"
}

# Main deployment logic
main() {
    check_dependencies
    
    case $ENVIRONMENT in
        development|dev)
            deploy_development
            ;;
        production|prod)
            deploy_production
            ;;
        rollback)
            rollback
            ;;
        *)
            echo -e "${RED}Invalid environment: $ENVIRONMENT${NC}"
            echo "Usage: $0 [development|production|rollback] [tag]"
            exit 1
            ;;
    esac
}

# Run main function
main