#!/bin/bash

# Materials Explorer Deployment Script
# This script helps deploy the Materials Explorer application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists docker; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command_exists docker-compose; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to setup environment
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env.prod ]; then
        if [ -f .env.prod.template ]; then
            print_warning ".env.prod not found, copying from template"
            cp .env.prod.template .env.prod
            print_warning "Please edit .env.prod with your configuration before continuing"
            exit 1
        else
            print_error ".env.prod.template not found"
            exit 1
        fi
    fi
    
    print_success "Environment configuration ready"
}

# Function to build and start services
deploy_services() {
    local env_file=${1:-.env.prod}
    local compose_file=${2:-docker-compose.prod.yml}
    
    print_status "Building and starting services..."
    
    # Load environment variables
    if [ -f "$env_file" ]; then
        export $(cat "$env_file" | grep -v '^#' | xargs)
    fi
    
    # Build images
    print_status "Building Docker images..."
    docker-compose -f "$compose_file" build --no-cache
    
    # Start services
    print_status "Starting services..."
    docker-compose -f "$compose_file" up -d
    
    print_success "Services started successfully"
}

# Function to check service health
check_health() {
    local compose_file=${1:-docker-compose.prod.yml}
    
    print_status "Checking service health..."
    
    # Wait for services to be healthy
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$compose_file" ps | grep -q "Up (healthy)"; then
            print_success "Services are healthy"
            return 0
        fi
        
        print_status "Waiting for services to be healthy... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    print_error "Services failed to become healthy within expected time"
    docker-compose -f "$compose_file" logs --tail=20
    exit 1
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Wait for database to be ready
    docker-compose -f docker-compose.prod.yml exec -T api python -c "
import asyncio
import sys
sys.path.append('/app/backend')
from app.db.session import AsyncSessionLocal

async def check_db():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute('SELECT 1')
        print('Database is ready')
    except Exception as e:
        print(f'Database not ready: {e}')
        sys.exit(1)

asyncio.run(check_db())
"
    
    print_success "Database is ready"
}

# Function to display service URLs
show_urls() {
    local api_port=${API_PORT:-8000}
    local frontend_port=${FRONTEND_PORT:-3000}
    
    print_success "Deployment completed successfully!"
    echo
    print_status "Service URLs:"
    echo "  Frontend: http://localhost:${frontend_port}"
    echo "  Backend API: http://localhost:${api_port}"
    echo "  API Documentation: http://localhost:${api_port}/docs"
    echo "  Database Admin: http://localhost:5050 (if enabled)"
    echo
    print_status "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
    print_status "To stop services: docker-compose -f docker-compose.prod.yml down"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  deploy          Full deployment (default)"
    echo "  build           Build images only"
    echo "  start           Start services"
    echo "  stop            Stop services"
    echo "  restart         Restart services"
    echo "  logs            Show logs"
    echo "  status          Show service status"
    echo "  clean           Clean up (remove containers and volumes)"
    echo "  help            Show this help message"
    echo
    echo "Options:"
    echo "  --env-file      Environment file (default: .env.prod)"
    echo "  --compose-file  Docker compose file (default: docker-compose.prod.yml)"
}

# Main deployment function
main_deploy() {
    local env_file=${1:-.env.prod}
    local compose_file=${2:-docker-compose.prod.yml}
    
    print_status "Starting Materials Explorer deployment..."
    
    check_prerequisites
    setup_environment
    deploy_services "$env_file" "$compose_file"
    check_health "$compose_file"
    run_migrations
    show_urls
}

# Parse command line arguments
ENV_FILE=".env.prod"
COMPOSE_FILE="docker-compose.prod.yml"

while [[ $# -gt 0 ]]; do
    case $1 in
        --env-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --compose-file)
            COMPOSE_FILE="$2"
            shift 2
            ;;
        deploy)
            COMMAND="deploy"
            shift
            ;;
        build)
            COMMAND="build"
            shift
            ;;
        start)
            COMMAND="start"
            shift
            ;;
        stop)
            COMMAND="stop"
            shift
            ;;
        restart)
            COMMAND="restart"
            shift
            ;;
        logs)
            COMMAND="logs"
            shift
            ;;
        status)
            COMMAND="status"
            shift
            ;;
        clean)
            COMMAND="clean"
            shift
            ;;
        help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Execute command
case ${COMMAND:-deploy} in
    deploy)
        main_deploy "$ENV_FILE" "$COMPOSE_FILE"
        ;;
    build)
        check_prerequisites
        docker-compose -f "$COMPOSE_FILE" build
        ;;
    start)
        docker-compose -f "$COMPOSE_FILE" up -d
        show_urls
        ;;
    stop)
        docker-compose -f "$COMPOSE_FILE" down
        ;;
    restart)
        docker-compose -f "$COMPOSE_FILE" restart
        ;;
    logs)
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    status)
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    clean)
        print_warning "This will remove all containers, networks, and volumes"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
            docker system prune -f
            print_success "Cleanup completed"
        fi
        ;;
esac