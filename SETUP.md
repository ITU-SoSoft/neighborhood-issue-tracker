# Neighborhood Issue Tracker - Setup Guide

A comprehensive guide to run the Neighborhood Issue Tracker on a fresh VDS (Virtual Dedicated Server) or local computer.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Local Development)](#quick-start-local-development)
3. [Production Deployment (VDS)](#production-deployment-vds)
4. [Environment Configuration](#environment-configuration)
5. [Default Users](#default-users)
6. [Useful Commands](#useful-commands)
7. [Architecture Overview](#architecture-overview)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 20.10+ | Container runtime |
| Docker Compose | 2.0+ | Container orchestration |
| Git | 2.30+ | Version control |

### System Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 20 GB | 50 GB |
| OS | Ubuntu 20.04+ / Windows 10+ / macOS 12+ | Ubuntu 22.04 LTS |

---

## Quick Start (Local Development)

### Step 1: Install Docker

#### Ubuntu/Debian
```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install -y docker.io docker-compose-v2

# Start and enable Docker
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

#### Windows
1. Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Enable WSL 2 integration in Docker Desktop settings
3. Restart your computer

#### macOS
1. Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Start Docker Desktop from Applications

### Step 2: Clone the Repository

```bash
git clone https://github.com/ITU-SoSoft/neighborhood-issue-tracker.git
cd neighborhood-issue-tracker
```

### Step 3: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env
```

Edit the `.env` file with minimal settings for local development:

```env
# Database
POSTGRES_USER=sosoft
POSTGRES_PASSWORD=localdev123
POSTGRES_DB=sosoft

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# MinIO (Object Storage)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_PUBLIC_ENDPOINT=localhost:9000

# URLs (for local development)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
CORS_ORIGINS=http://localhost:3000

# Email (disabled for local development)
RESEND_ENABLED=false

# SMS (disabled for local development)
TWILIO_ENABLED=false
```

### Step 4: Build and Start

```bash
# Build all containers
docker compose build

# Start all services
docker compose up -d
```

### Step 5: Verify Installation

```bash
# Check if all services are healthy
docker compose ps
```

All services should show `(healthy)` status:

```
NAME                      STATUS
sosoft-staging-backend    Up (healthy)
sosoft-staging-frontend   Up (healthy)
sosoft-staging-minio      Up (healthy)
sosoft-staging-postgres   Up (healthy)
```

### Step 6: Access the Application

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main web application |
| Backend API | http://localhost:8000 | REST API |
| API Documentation | http://localhost:8000/docs | Swagger/OpenAPI |
| MinIO Console | http://localhost:9001 | Object storage admin |

---

## Production Deployment (VDS)

### Step 1: Server Setup

```bash
# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again, then verify
docker --version
docker compose version
```

### Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/ITU-SoSoft/neighborhood-issue-tracker.git
cd neighborhood-issue-tracker

# Create environment file
cp .env.example .env
```

### Step 3: Configure Production Environment

Edit `.env` with secure production values:

```env
# =============================================================================
# Database (PostgreSQL with PostGIS)
# =============================================================================
POSTGRES_USER=mahallem_prod
POSTGRES_PASSWORD=<GENERATE_STRONG_PASSWORD>
POSTGRES_DB=mahallem_prod

# =============================================================================
# JWT Authentication
# =============================================================================
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=<GENERATE_WITH_OPENSSL>

# =============================================================================
# MinIO (S3-compatible object storage)
# =============================================================================
MINIO_ACCESS_KEY=minio_prod_admin
MINIO_SECRET_KEY=<GENERATE_STRONG_PASSWORD>
MINIO_PUBLIC_ENDPOINT=storage.yourdomain.com

# =============================================================================
# URLs and CORS
# =============================================================================
NEXT_PUBLIC_APP_BASE_URL=https://yourdomain.com
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com/api/v1
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# =============================================================================
# Email Service (Resend)
# =============================================================================
RESEND_ENABLED=true
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxx
RESEND_FROM_EMAIL=noreply@yourdomain.com
RESEND_FROM_NAME=Your App Name

# =============================================================================
# SMS Service (Twilio) - Optional
# =============================================================================
TWILIO_ENABLED=false
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```

Generate secure passwords:
```bash
# Generate JWT secret
openssl rand -hex 32

# Generate database password
openssl rand -base64 24

# Generate MinIO secret
openssl rand -base64 24
```

### Step 4: Setup Reverse Proxy (Nginx)

Install and configure Nginx for SSL termination:

```bash
# Install Nginx and Certbot
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/mahallem
```

Add the following configuration:

```nginx
# Frontend
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For file uploads
        client_max_body_size 50M;
    }
}

# MinIO Storage
server {
    listen 80;
    server_name storage.yourdomain.com;

    location / {
        proxy_pass http://localhost:9000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For file uploads
        client_max_body_size 50M;
    }
}
```

Enable the configuration and setup SSL:

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/mahallem /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Get SSL certificates (for all domains)
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com -d storage.yourdomain.com
```

### Step 5: Build and Deploy

```bash
# Build containers
docker compose build

# Start services
docker compose up -d

# Check status
docker compose ps
```

### Step 6: Setup Automatic Updates (Optional)

Create a deployment script:

```bash
nano ~/deploy.sh
```

```bash
#!/bin/bash
cd /path/to/neighborhood-issue-tracker

# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose build
docker compose up -d

# Cleanup old images
docker image prune -f

echo "Deployment complete!"
```

```bash
chmod +x ~/deploy.sh
```

---

## Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_USER` | Database username | `sosoft` |
| `POSTGRES_PASSWORD` | Database password | `secure_password` |
| `POSTGRES_DB` | Database name | `sosoft` |
| `JWT_SECRET_KEY` | JWT signing key (32+ chars) | `openssl rand -hex 32` |
| `MINIO_ACCESS_KEY` | MinIO access key | `minioadmin` |
| `MINIO_SECRET_KEY` | MinIO secret key | `minioadmin123` |
| `MINIO_PUBLIC_ENDPOINT` | Public MinIO URL | `localhost:9000` |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API URL | `http://localhost:8000/api/v1` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RESEND_ENABLED` | Enable email service | `false` |
| `RESEND_API_KEY` | Resend API key | - |
| `RESEND_FROM_EMAIL` | Sender email | - |
| `TWILIO_ENABLED` | Enable SMS service | `false` |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | - |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | - |
| `TWILIO_PHONE_NUMBER` | Twilio phone number | - |

---

## Default Users

After starting the application, the following users are automatically created:

| Role | Email | Password | Permissions |
|------|-------|----------|-------------|
| Manager | manager@sosoft.com | manager123! | Full access, manage escalations |
| Support | support@sosoft.com | support123! | Handle tickets, update status |

**Note:** Citizen users must register through the signup page at `/signup`.

---

## Useful Commands

### Container Management

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Stop and remove all data (volumes)
docker compose down -v

# Restart a specific service
docker compose restart backend

# View logs
docker compose logs -f              # All services
docker compose logs -f backend      # Specific service

# Check service status
docker compose ps
```

### Database Operations

```bash
# Access PostgreSQL shell
docker compose exec postgres psql -U sosoft -d sosoft

# Run database migrations manually
docker compose exec backend alembic upgrade head

# Check migration status
docker compose exec backend alembic current

# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "description"
```

### Backend Operations

```bash
# Access backend shell
docker compose exec backend bash

# Run tests
docker compose exec backend python -m pytest -v

# Run specific test file
docker compose exec backend python -m pytest tests/integration/tickets/ -v
```

### Cleanup

```bash
# Remove unused images
docker image prune -f

# Remove all unused resources
docker system prune -af

# Remove everything including volumes (CAUTION: deletes all data)
docker system prune -af --volumes
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Docker Network                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Frontend  │  │   Backend   │  │    MinIO    │             │
│  │  (Next.js)  │  │  (FastAPI)  │  │  (Storage)  │             │
│  │   :3000     │  │   :8000     │  │ :9000/:9001 │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                     │
│         │                ▼                │                     │
│         │         ┌─────────────┐         │                     │
│         │         │  PostgreSQL │◄────────┘                     │
│         │         │  + PostGIS  │                               │
│         │         │   :5432     │                               │
│         │         └─────────────┘                               │
│         │                                                       │
└─────────┼───────────────────────────────────────────────────────┘
          │
          ▼
    ┌───────────┐
    │  Browser  │
    └───────────┘
```

### Services

| Service | Technology | Port | Description |
|---------|------------|------|-------------|
| Frontend | Next.js 14 | 3000 | React-based web interface |
| Backend | FastAPI | 8000 | REST API with async support |
| Database | PostgreSQL + PostGIS | 5432 | Relational database with GIS |
| Storage | MinIO | 9000/9001 | S3-compatible object storage |

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
lsof -i :3000
lsof -i :8000

# Kill the process or change ports in docker-compose.yml
```

#### 2. Database Connection Failed

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

#### 3. Backend Health Check Failing

```bash
# Check backend logs
docker compose logs backend

# Common issues:
# - Database not ready yet (wait a few seconds)
# - Missing environment variables
# - Migration errors
```

#### 4. Permission Denied (Linux)

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Logout and login again
# Or run: newgrp docker
```

#### 5. WSL 2 + Docker Issues (Windows)

1. Ensure WSL 2 is installed and enabled
2. Enable WSL 2 integration in Docker Desktop settings
3. Restart Docker Desktop
4. If issues persist, restart your computer

#### 6. Clean Reset

If something goes wrong, perform a complete reset:

```bash
# Stop everything and remove all data
docker compose down -v

# Remove all Docker resources
docker system prune -af --volumes

# Rebuild and start fresh
docker compose build --no-cache
docker compose up -d
```

### Getting Help

- Check logs: `docker compose logs -f`
- API documentation: http://localhost:8000/docs
- GitHub Issues: https://github.com/ITU-SoSoft/neighborhood-issue-tracker/issues

---

## License

This project is developed for BLG411E Software Engineering course at Istanbul Technical University.
