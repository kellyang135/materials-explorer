# Materials Explorer - Deployment Guide

This guide provides comprehensive instructions for deploying the Materials Explorer application in production environments.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Production Configuration](#production-configuration)
- [Deployment Options](#deployment-options)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Git** (for cloning the repository)
- Minimum **4GB RAM** and **20GB disk space**

### Optional Software
- **nginx** (for custom reverse proxy setup)
- **SSL certificate** (for HTTPS in production)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/materials-explorer.git
cd materials-explorer
```

### 2. Configure Environment
```bash
# Copy the production environment template
cp .env.prod.template .env.prod

# Edit the configuration file
nano .env.prod
```

### 3. Deploy with One Command
```bash
# Run the deployment script
./deploy.sh
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Production Configuration

### Environment Variables (.env.prod)

#### Essential Settings
```env
# Application
PROJECT_NAME="Materials Explorer"
DEBUG=false

# Database (PostgreSQL)
POSTGRES_USER=materials
POSTGRES_PASSWORD=your_secure_database_password
POSTGRES_DB=materials_explorer

# Redis Cache
REDIS_PASSWORD=your_secure_redis_password

# Materials Project API
MP_API_KEY=your_materials_project_api_key

# Domain Configuration
REACT_APP_API_URL=https://your-domain.com/api/v1
CORS_ORIGINS=["https://your-domain.com","https://www.your-domain.com"]
```

#### Security Settings
```env
# Strong passwords (use password generators)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# SSL Configuration
SSL_CERT_PATH=/etc/ssl/certs/your_cert.crt
SSL_KEY_PATH=/etc/ssl/private/your_key.key
```

### Database Setup

#### Initial Data Loading
```bash
# Load diverse materials dataset (run once)
python load_diverse_materials.py
python import_mp_data.py
```

#### Backup Configuration
```bash
# Set up automated backups
echo "0 2 * * * docker-compose exec -T db pg_dump -U materials materials_explorer | gzip > /backups/materials_$(date +%Y%m%d).sql.gz" | crontab -
```

## Deployment Options

### Option 1: Docker Compose (Recommended)
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# With custom environment
docker-compose --env-file .env.prod -f docker-compose.prod.yml up -d
```

### Option 2: Using Deployment Script
```bash
# Full deployment
./deploy.sh

# Custom configuration
./deploy.sh --env-file .env.custom --compose-file docker-compose.custom.yml
```

### Option 3: Cloud Deployment

#### AWS ECS
```bash
# 1. Build and push images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker build -t materials-explorer-backend .
docker tag materials-explorer-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/materials-explorer-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/materials-explorer-backend:latest

# 2. Deploy ECS task definition
aws ecs update-service --cluster materials-cluster --service materials-service --force-new-deployment
```

#### Docker Swarm
```bash
# Initialize swarm (on manager node)
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml materials-explorer
```

#### Kubernetes
```bash
# Generate Kubernetes manifests
docker-compose -f docker-compose.prod.yml config | kompose convert -f -

# Deploy to cluster
kubectl apply -f materials-explorer-*.yaml
```

### Option 4: Manual Installation

#### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db"
export REDIS_URL="redis://localhost:6379/0"
export MP_API_KEY="your_api_key"

# Run database migrations
python -c "import asyncio; from app.db.session import AsyncSessionLocal, engine; from app.db.base import Base; asyncio.run(engine.begin().run_sync(Base.metadata.create_all))"

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Build for production
REACT_APP_API_URL=https://your-domain.com/api/v1 npm run build

# Serve with nginx
sudo nginx -c /path/to/your/nginx.conf
```

## Monitoring & Maintenance

### Health Checks
```bash
# Check service status
./deploy.sh status

# View logs
./deploy.sh logs

# Check API health
curl http://localhost:8000/health
```

### Performance Monitoring
```bash
# Container resource usage
docker stats

# Database connections
docker-compose exec db psql -U materials -d materials_explorer -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory usage
docker-compose exec redis redis-cli info memory
```

### Log Management
```bash
# Rotate logs (add to crontab)
0 0 * * 0 docker-compose exec nginx sh -c "nginx -s reload"

# Archive old logs
find /var/lib/docker/containers -name "*.log" -mtime +30 -delete
```

### Updates & Maintenance
```bash
# Pull latest images
docker-compose pull

# Rolling update
./deploy.sh restart

# Database backup before updates
docker-compose exec db pg_dump -U materials materials_explorer > backup_$(date +%Y%m%d).sql

# Clean up old images
docker image prune -f
```

## Security

### SSL/TLS Configuration
```bash
# Generate self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/private.key \
  -out nginx/ssl/certificate.crt

# Let's Encrypt (production)
certbot certonly --webroot -w /var/www/html -d your-domain.com
```

### Firewall Configuration
```bash
# UFW (Ubuntu)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# iptables
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -j DROP
```

### Container Security
```bash
# Scan images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image materials-explorer-backend

# Run containers as non-root
docker-compose exec api whoami  # Should output 'appuser'
```

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database is running
docker-compose ps db

# Verify connection
docker-compose exec api python -c "
import asyncio
import sys
sys.path.append('/app/backend')
from app.db.session import AsyncSessionLocal
async def test(): 
    async with AsyncSessionLocal() as session: 
        await session.execute('SELECT 1')
        print('Database connection OK')
asyncio.run(test())
"
```

#### Frontend Build Errors
```bash
# Clear npm cache
docker-compose exec frontend npm cache clean --force

# Rebuild frontend
docker-compose build --no-cache frontend
```

#### API Rate Limiting
```bash
# Check Materials Project API limits
curl -H "X-API-KEY: your_api_key" "https://api.materialsproject.org/materials/mp-149/core"

# Monitor rate limit headers
curl -I http://localhost:8000/api/v1/materials
```

#### Memory Issues
```bash
# Increase Docker memory limits
# Edit ~/.docker/daemon.json:
{
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    }
  }
}

# Restart Docker
sudo systemctl restart docker
```

### Log Analysis
```bash
# API errors
docker-compose logs api | grep ERROR

# Database slow queries
docker-compose exec db tail -f /var/log/postgresql/postgresql.log

# Nginx access patterns
docker-compose exec nginx tail -f /var/log/nginx/access.log | grep -v "GET /health"
```

### Performance Optimization
```bash
# Optimize PostgreSQL
docker-compose exec db psql -U materials -d materials_explorer -c "
ANALYZE;
REINDEX DATABASE materials_explorer;
"

# Redis memory optimization
docker-compose exec redis redis-cli config set maxmemory 1gb
docker-compose exec redis redis-cli config set maxmemory-policy allkeys-lru

# Frontend caching
# Add to nginx.conf:
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### Backup & Recovery
```bash
# Create full backup
./deploy.sh stop
docker run --rm -v materials-explorer_postgres_data:/volume -v $(pwd):/backup alpine tar czf /backup/materials_backup_$(date +%Y%m%d).tar.gz -C /volume .

# Restore from backup
docker-compose down -v
docker volume create materials-explorer_postgres_data
docker run --rm -v materials-explorer_postgres_data:/volume -v $(pwd):/backup alpine tar xzf /backup/materials_backup_YYYYMMDD.tar.gz -C /volume
./deploy.sh start
```

## Cloud Deployment Strategies

### AWS
- **ECS with Fargate**: Serverless container deployment
- **EKS**: Kubernetes-managed containers
- **RDS**: Managed PostgreSQL database
- **ElastiCache**: Managed Redis cache
- **CloudFront**: CDN for frontend assets

### Google Cloud Platform
- **Cloud Run**: Serverless containers
- **GKE**: Kubernetes clusters
- **Cloud SQL**: Managed databases
- **Memorystore**: Managed Redis

### Azure
- **Container Instances**: Simple container deployment
- **AKS**: Kubernetes service
- **Database for PostgreSQL**: Managed database
- **Cache for Redis**: Managed cache

### DigitalOcean
- **App Platform**: Simple app deployment
- **Kubernetes**: Managed Kubernetes
- **Managed Databases**: PostgreSQL and Redis

For questions or issues, please check the [troubleshooting section](#troubleshooting) or open an issue in the GitHub repository.