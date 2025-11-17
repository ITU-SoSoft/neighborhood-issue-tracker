# Web Application

Frontend web application for the Neighborhood Issue Tracker built with Next.js 16.

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **Forms**: React Hook Form + Zod validation
- **Authentication**: Better Auth (via ID service)
- **Maps**: Leaflet + React Leaflet
- **Package Manager**: pnpm

## Setup

### 1. Install dependencies

```bash
pnpm install
```

### 2. Configure environment variables

Create a `.env.local` file in the root directory:

```bash
# Auth Service URL
# Points to the ID service authentication endpoints
NEXT_PUBLIC_AUTH_BASE_URL=http://localhost:8787/api/auth
```

**Note**: For production, update this URL to your deployed ID service endpoint.

### 3. Start the development server

Make sure the ID service is running first (see `../id/README.md`), then:

```bash
pnpm dev
```

The application will be available at `http://localhost:3000`.

## Authentication Flow

The web app communicates with the ID service for authentication:

1. User submits sign-up/sign-in form
2. Web app sends POST request to `${NEXT_PUBLIC_AUTH_BASE_URL}/sign-up/email` or `/sign-in/email`
3. ID service validates credentials and returns session token
4. Session cookie is set automatically by Better Auth
5. User is redirected to the dashboard

### Available Auth Pages

- `/sign-in` - User login
- `/sign-up` - User registration
- `/forgot-password` - Password reset (if implemented)

## Development

### Running Both Services

For local development, you need both services running:

```bash
# Terminal 1 - Start ID service
cd ../id
pnpm dev

# Terminal 2 - Start Web app
cd web
pnpm dev
```

### Building for Production

```bash
pnpm build
pnpm start
```
