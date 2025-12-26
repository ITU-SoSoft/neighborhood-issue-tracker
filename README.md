# Neighborhood Issue Tracker (Mahallem)

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
│   │   ├── scripts/  # Seed scripts
│   │   └── services/ # Business logic
│   └── tests/        # pytest tests
├── web/              # Next.js frontend
│   └── src/
│       ├── app/      # Pages (App Router)
│       ├── components/
│       └── lib/      # API clients, queries
├── scripts/          # Helper scripts
│   └── seed.sh       # Demo data seeding
└── docker-compose.yml
```

---

## Quick Start (For TAs / Reviewers)

This section provides the fastest way to get the project running locally with demo data.

### Prerequisites

- **Docker Desktop** (includes Docker Compose)
  - [Windows](https://www.docker.com/products/docker-desktop/) - Enable WSL 2 integration
  - [macOS](https://www.docker.com/products/docker-desktop/)
  - [Linux](https://docs.docker.com/engine/install/)

### Step 1: Clone the Repository

```bash
git clone https://github.com/ITU-SoSoft/neighborhood-issue-tracker.git
cd neighborhood-issue-tracker
```

### Step 2: Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with these minimal settings for local development:

```env
# Database
POSTGRES_USER=sosoft
POSTGRES_PASSWORD=localdev123
POSTGRES_DB=sosoft

# JWT Secret (any random string works for local dev)
JWT_SECRET_KEY=local-development-secret-key-change-in-production

# MinIO (Object Storage)
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_PUBLIC_ENDPOINT=localhost:9000

# URLs
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
CORS_ORIGINS=http://localhost:3000

# Disable external services for local development
RESEND_ENABLED=false
TWILIO_ENABLED=false
```

### Step 3: Build and Start

```bash
# Build and start all services (first run takes 3-5 minutes)
docker compose up -d --build

# Wait for services to be healthy (check status)
docker compose ps
```

All services should show `healthy` status:
```
NAME                      STATUS
sosoft-staging-backend    Up (healthy)
sosoft-staging-frontend   Up (healthy)
sosoft-staging-minio      Up (healthy)
sosoft-staging-postgres   Up (healthy)
```

### Step 4: Seed Demo Data

```bash
# Seed 300 realistic tickets with full history
./scripts/seed.sh
```

This creates:
- 26 support teams covering all 39 Istanbul districts
- 300 tickets with status logs, comments, feedback, and escalations
- 15 citizen users, 52 support staff, 26 managers
- Realistic Turkish names, addresses, and issue descriptions

### Step 5: Access the Application

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **MinIO Console** | http://localhost:9001 |

---

## Default Login Credentials

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| **Manager** | manager@sosoft.com | manager123! | Full access, manage teams, review escalations |
| **Support** | support@sosoft.com | support123! | Handle tickets, update status, escalate |
| **Citizen** | citizen@sosoft.com | citizen123! | Report issues, track tickets, give feedback |

---

## Useful Commands

```bash
# View logs (all services)
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# Stop all services
docker compose down

# Reset everything (delete all data and start fresh)
docker compose down -v
docker compose up -d --build
./scripts/seed.sh

# Re-seed demo data (clear existing and recreate)
./scripts/seed.sh --clear

# Seed with custom ticket count
./scripts/seed.sh --tickets 500

# Run backend tests
docker compose exec backend python -m pytest -v
```

---

## Features Overview

### For Citizens
- Report neighborhood issues with photos and location
- Track ticket status in real-time
- Receive notifications on updates
- Rate resolved issues and provide feedback
- Save frequently used addresses

### For Support Staff
- View and manage assigned tickets
- Update ticket status with comments
- Escalate complex issues to managers
- Filter tickets by status, category, district

### For Managers
- Dashboard with analytics and statistics
- Review and approve/reject escalations
- Manage support teams and assignments
- View performance metrics and heatmaps
