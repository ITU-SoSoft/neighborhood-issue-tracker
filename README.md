# Neighborhood Issue Tracker 

A citizen issue reporting platform for BLG411E Software Engineering at Istanbul Technical University.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, TanStack Query, Leaflet Maps |
| **Backend** | FastAPI (Python 3.13), SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 16 + PostGIS (geospatial) |
| **Storage** | MinIO (S3-compatible) |
| **Infrastructure** | Docker Compose |

## Project Structure

```
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   └── tests/        # pytest tests
├── web/              # Next.js frontend
│   └── src/
│       ├── app/      # Pages (App Router)
│       ├── components/
│       └── lib/      # API clients, queries
└── docker-compose.yml
```

## Quick Start

### Prerequisites
- Docker and Docker Compose

### Setup

```bash
# 1. Copy environment file and configure
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Run database migrations
docker compose exec backend alembic upgrade head

# 4. Seed default data
docker compose exec backend python -m app.scripts.seed
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |

## Default Accounts

| Role | Email | Password |
|------|-------|----------|
| Manager | manager@sosoft.com | manager123! |
| Support | support@sosoft.com | support123! |

Citizens register via the `/sign-up` page.

## Useful Commands

```bash
# View logs
docker compose logs -f backend

# Run backend tests
docker compose exec backend python -m pytest -v

# Stop services
docker compose down

# Reset everything (including data)
docker compose down -v
```
