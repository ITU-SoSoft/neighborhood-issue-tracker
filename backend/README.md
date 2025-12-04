# SoSoft Backend API

FastAPI backend for the **SoSoft** - Neighborhood Issue Reporting & Tracking Platform.

## Features

- **Phone-based Authentication**: Turkish phone number validation (+90) with OTP verification via Twilio
- **Role-based Access Control**: Citizen, Support, and Manager roles with different permissions
- **Ticket Management**: Full CRUD operations with status workflow
- **Geospatial Support**: PostGIS for location-based queries and heatmaps
- **File Storage**: MinIO (S3-compatible) for photo uploads
- **Analytics Dashboard**: KPIs, heatmaps, team performance metrics
- **Real-time Notifications**: SMS notifications for ticket status updates

## Tech Stack

- **Framework**: FastAPI (Python 3.13)
- **Database**: PostgreSQL 16 with PostGIS
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic
- **Storage**: MinIO
- **SMS**: Twilio
- **Package Manager**: uv

## Project Structure

```
backend/
├── alembic/                  # Database migrations
│   ├── versions/             # Migration files
│   ├── env.py                # Alembic environment
│   └── script.py.mako        # Migration template
├── app/
│   ├── api/
│   │   ├── v1/               # API v1 endpoints
│   │   │   ├── analytics.py  # Analytics & reporting
│   │   │   ├── auth.py       # Authentication
│   │   │   ├── categories.py # Category management
│   │   │   ├── comments.py   # Ticket comments
│   │   │   ├── escalations.py# Escalation requests
│   │   │   ├── feedback.py   # Citizen feedback
│   │   │   ├── tickets.py    # Ticket CRUD
│   │   │   ├── users.py      # User management
│   │   │   └── router.py     # Router aggregation
│   │   └── deps.py           # Shared dependencies
│   ├── core/
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── permissions.py    # Permission utilities
│   │   └── security.py       # JWT & OTP utilities
│   ├── models/               # SQLAlchemy models
│   │   ├── category.py
│   │   ├── comment.py
│   │   ├── escalation.py
│   │   ├── feedback.py
│   │   ├── photo.py
│   │   ├── team.py
│   │   ├── ticket.py
│   │   └── user.py
│   ├── schemas/              # Pydantic schemas
│   │   ├── analytics.py
│   │   ├── auth.py
│   │   ├── category.py
│   │   ├── comment.py
│   │   ├── escalation.py
│   │   ├── feedback.py
│   │   ├── photo.py
│   │   ├── ticket.py
│   │   └── user.py
│   ├── services/             # External services
│   │   ├── sms.py            # Twilio SMS
│   │   └── storage.py        # MinIO storage
│   ├── config.py             # Settings
│   └── database.py           # Database setup
├── main.py                   # Application entry point
├── alembic.ini               # Alembic configuration
├── pyproject.toml            # Project dependencies
├── Dockerfile                # Container image
└── .env.example              # Environment template
```

## Getting Started

### Prerequisites

- Python 3.13+
- PostgreSQL 16+ with PostGIS
- MinIO (or S3-compatible storage)
- uv package manager

### Local Development

1. **Clone and navigate to backend**:
   ```bash
   cd backend
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start PostgreSQL and MinIO** (using Docker):
   ```bash
   docker compose up postgres minio minio-setup -d
   ```

5. **Run database migrations**:
   ```bash
   uv run alembic upgrade head
   ```

6. **Seed default categories** (optional):
   ```bash
   uv run python -m app.scripts.seed
   ```

7. **Start the development server**:
   ```bash
   uv run uvicorn main:app --reload
   ```

8. **Access the API**:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Using Docker Compose

Start all services (PostgreSQL, MinIO, API):

```bash
# From project root
docker compose up -d

# View logs
docker compose logs -f backend

# Stop all services
docker compose down
```

## API Documentation

### Authentication Flow

1. **Request OTP**: `POST /api/v1/auth/request-otp`
   ```json
   {"phone_number": "+905551234567"}
   ```

2. **Verify OTP**: `POST /api/v1/auth/verify-otp`
   ```json
   {"phone_number": "+905551234567", "code": "123456"}
   ```

3. **Register** (new users): `POST /api/v1/auth/register`
   ```json
   {
     "phone_number": "+905551234567",
     "otp_code": "123456",
     "full_name": "John Doe"
   }
   ```

### Ticket Status Workflow

```
new → in_progress → resolved → closed
         ↓
     escalated → (manager approves/rejects) → in_progress
```

### User Roles

| Role | Permissions |
|------|-------------|
| **Citizen** | Create tickets, view own tickets, add comments, provide feedback |
| **Support** | All citizen permissions + manage tickets, update status, assign |
| **Manager** | All support permissions + analytics, escalation approval, user management |

## Database Migrations

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Show migration history
uv run alembic history
```

## Default Categories

The system comes with 6 default categories:

1. Infrastructure
2. Traffic
3. Lighting
4. Waste Management
5. Parks
6. Other

## Environment Variables

See `.env.example` for all available configuration options.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/sosoft` |
| `JWT_SECRET_KEY` | Secret key for JWT signing | (required) |
| `TWILIO_ENABLED` | Enable SMS notifications | `false` |
| `MINIO_ENDPOINT` | MinIO server address | `localhost:9000` |
| `DEBUG` | Enable debug mode | `false` |

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_auth.py
```

## License

MIT
