# Web Application

Frontend web application for the Neighborhood Issue Tracker built with Next.js 14+.

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod validation
- **Authentication**: JWT-based (via FastAPI backend)
- **Maps**: Leaflet + React Leaflet
- **UI Components**: shadcn/ui
- **Animations**: Framer Motion
- **Package Manager**: npm

## Setup

### 1. Install dependencies

```bash
npm install
```

### 2. Configure environment variables

The API URL is automatically configured in `docker-compose.yml` and `docker-compose.prod.yml`.

For **local development** (if running outside Docker):
Create a `.env.local` file in the `web/` directory:

```bash
# API Backend URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

For **production**, the URL is set via Docker build arguments in `docker-compose.prod.yml`.

### 3. Start the development server

**Option A: Using Docker Compose (Recommended)**
```bash
# From project root
docker-compose up -d
```
The application will be available at `http://localhost:3000`.

**Option B: Local Development (without Docker)**
```bash
# Make sure the backend is running first
npm run dev
```

## Authentication Flow

The web app communicates with the FastAPI backend for authentication:

1. User submits sign-up/sign-in form (phone number + password or OTP)
2. Web app sends request to backend API endpoints
3. Backend validates credentials and returns JWT tokens
4. Tokens are stored in localStorage
5. User is redirected to the dashboard

### Available Auth Pages

- `/sign-in` - Citizen login (phone + password or OTP)
- `/sign-up` - Citizen registration
- `/staff` - Staff login (support/manager)

## Development

### Running with Docker Compose

For local development, use Docker Compose to run all services:

```bash
# From project root
docker-compose up -d

# View logs
docker-compose logs -f frontend
```

### Building for Production

```bash
npm run build
npm start
```

Or using Docker:
```bash
# From project root
docker-compose -f docker-compose.prod.yml up -d
```
