# ID Service

Authentication and identity management service for the Neighborhood Issue Tracker. This is a serverless microservice that handles user authentication, session management, and identity verification, deployed on Cloudflare's global edge network.

## Overview

The service is built with [Better Auth](https://www.better-auth.com/) and runs on [Cloudflare Workers](https://workers.cloudflare.com/). It provides a complete authentication system with:

- **User Management**: Registration, login, and profile management
- **Session Handling**: Secure session tokens with IP and user agent tracking
- **OAuth Integration**: Support for third-party authentication providers
- **Email Verification**: Token-based email verification and password reset flows

## Architecture

### Tech Stack

- **Runtime**: Cloudflare Workers (serverless edge compute)
- **Web Framework**: [Hono](https://hono.dev/) - Ultra-fast web framework
- **Authentication**: [Better Auth](https://www.better-auth.com/) - Modern auth library
- **Database**: [Neon](https://neon.tech/) PostgreSQL (serverless)
- **ORM**: [Drizzle ORM](https://orm.drizzle.team/) with `@neondatabase/serverless` driver
- **Package Manager**: pnpm
- **Language**: TypeScript with strict mode

### Project Structure

```
id/
├── src/
│   ├── index.ts                 # Main Hono app with /api/auth/* routes
│   ├── lib/
│   │   └── better-auth/
│   │       ├── index.ts         # Auth instance factory (receives env bindings)
│   │       └── options.ts       # Better Auth configuration (appName: 'sosoft-id')
│   └── db/
│       └── schema.ts            # Database schema (user, session, account, verification)
├── better-auth.config.ts        # CLI configuration for local development
├── drizzle.config.ts            # Drizzle Kit configuration
├── drizzle/                     # Generated migrations
├── package.json
├── tsconfig.json
└── .env                         # Environment variables (not committed)
```

### How It Works

1. **Request Flow**: All auth requests hit `/api/auth/*` endpoints on the Cloudflare Worker
2. **Environment Injection**: Cloudflare bindings (`DATABASE_URL`, `BETTER_AUTH_URL`, `BETTER_AUTH_SECRET`) are injected at runtime
3. **Dynamic Auth Instance**: Better Auth is instantiated per-request with environment-specific configuration
4. **Database Connection**: Uses Neon's HTTP-based serverless driver (no persistent connections)
5. **Edge Response**: Auth responses are served from Cloudflare's edge network (low latency globally)

## Setup

### 1. Install dependencies

```bash
pnpm install
```

### 2. Configure environment variables

Create a `.env` file in the root directory with the following variables:

```bash
# The URL where your auth service is accessible
# For local dev: http://localhost:8787 (default Wrangler port)
# For production: https://your-worker.workers.dev
BETTER_AUTH_URL=http://localhost:8787

# Secret key for signing tokens and sessions
# Generate a secure random string: openssl rand -base64 32
BETTER_AUTH_SECRET=<your-generated-secret>

# PostgreSQL connection string from Neon
# Format: postgresql://user:password@host/database?sslmode=require
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
```

**Note**: The `.env` file is used by:
- Drizzle CLI for migrations (`drizzle-kit generate`, `drizzle-kit push`)
- Better Auth CLI for local testing

For production deployment, these environment variables must be configured as Cloudflare Worker secrets/bindings.

### 3. Set up the database

Generate and push the database schema:

```bash
pnpm drizzle-kit generate
pnpm drizzle-kit push
```

## Development

Start the local development server:

```bash
pnpm dev
```

The service will be available at `http://localhost:8787`.

### API Endpoints

- `GET/POST /api/auth/*` - Better Auth endpoints for authentication

## Database Schema

The service uses a PostgreSQL database with four core tables managed by Drizzle ORM:

### Tables

#### `user`
Stores user account information:
- `id` (text, PK) - Unique user identifier
- `name` (text) - User's display name
- `email` (text, unique) - Email address
- `emailVerified` (boolean) - Email verification status
- `image` (text, nullable) - Profile image URL
- `createdAt` (timestamp) - Account creation time
- `updatedAt` (timestamp) - Last update time

#### `session`
Manages active authentication sessions:
- `id` (text, PK) - Session identifier
- `token` (text, unique) - Session token
- `expiresAt` (timestamp) - Expiration time
- `userId` (text, FK → user) - Associated user (cascade delete)
- `ipAddress` (text, nullable) - Client IP
- `userAgent` (text, nullable) - Client user agent
- `createdAt` / `updatedAt` (timestamp)

#### `account`
Stores OAuth provider connections and credentials:
- `id` (text, PK) - Account identifier
- `accountId` (text) - Provider-specific account ID
- `providerId` (text) - OAuth provider name
- `userId` (text, FK → user) - Associated user (cascade delete)
- `accessToken` / `refreshToken` / `idToken` (text, nullable)
- `accessTokenExpiresAt` / `refreshTokenExpiresAt` (timestamp, nullable)
- `scope` (text, nullable) - OAuth scopes
- `password` (text, nullable) - Hashed password for credentials provider
- `createdAt` / `updatedAt` (timestamp)

#### `verification`
Handles email verification and password reset tokens:
- `id` (text, PK) - Verification identifier
- `identifier` (text) - Email or phone number
- `value` (text) - Verification token/code
- `expiresAt` (timestamp) - Token expiration
- `createdAt` / `updatedAt` (timestamp)

### Migrations

Database migrations are managed by Drizzle Kit and stored in `drizzle/` directory. The schema uses PostgreSQL-specific features and maintains referential integrity with foreign key constraints.

## Deployment

Deploy to Cloudflare Workers:

```bash
pnpm deploy
```

## Type Generation

[Generate/synchronize types based on your Worker configuration](https://developers.cloudflare.com/workers/wrangler/commands/#types):

```bash
pnpm cf-typegen
```

Pass the `CloudflareBindings` as generics when instantiating `Hono`:

```ts path=null start=null
// src/index.ts
const app = new Hono<{ Bindings: CloudflareBindings }>()
```

## Development Workflow

### Making Schema Changes

1. Modify `src/db/schema.ts`
2. Generate migration: `pnpm drizzle-kit generate`
3. Review migration in `drizzle/` directory
4. Push to database: `pnpm drizzle-kit push`
5. Restart dev server to pick up changes

### Testing Locally

The dev server runs at `http://localhost:8787`. Test authentication endpoints:

```bash
# Health check (if implemented)
curl http://localhost:8787/api/auth

# Example: Check available auth methods
curl http://localhost:8787/api/auth/session
```

## Deployment

### Prerequisites

1. Cloudflare account with Workers enabled
2. Wrangler CLI authenticated (`pnpm wrangler login`)
3. Environment variables configured in Cloudflare dashboard or via `wrangler secret`

### Deploy Steps

```bash
# Deploy to production
pnpm deploy

# The worker will be available at:
# https://<worker-name>.<account>.workers.dev
```

### Setting Production Secrets

```bash
pnpm wrangler secret put BETTER_AUTH_SECRET
pnpm wrangler secret put DATABASE_URL
pnpm wrangler secret put BETTER_AUTH_URL
```

## Troubleshooting

### "Failed to connect to database"
- Verify `DATABASE_URL` is correct and accessible
- Check Neon database is active (may sleep on free tier)
- Ensure `sslmode=require` is in connection string

### "Invalid token" errors
- Regenerate `BETTER_AUTH_SECRET`
- Clear existing sessions in database
- Verify `BETTER_AUTH_URL` matches your deployed URL

### Type errors after schema changes
- Run `pnpm cf-typegen` to regenerate Worker types
- Restart TypeScript server in your editor

## Notes

- **Serverless Architecture**: No persistent connections; each request creates a new database connection via HTTP
- **Cold Starts**: First request may be slower; Cloudflare Workers have minimal cold start times
- **Global Edge**: Deployed to Cloudflare's global network; requests are served from nearest datacenter
- **Environment Isolation**: `.env` for local development; Cloudflare secrets/bindings for production
- **Security**: Secrets are never bundled; accessed via Cloudflare's secure runtime bindings
