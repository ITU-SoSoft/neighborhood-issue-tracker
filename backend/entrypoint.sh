#!/bin/bash
set -e

echo "🚀 Starting SoSoft Backend..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL..."
python -c "
import asyncio
import asyncpg
import os
import time

async def wait_for_db():
    max_retries = 30
    retry_interval = 2
    
    db_url = os.getenv('DATABASE_URL', '')
    # Convert asyncpg URL format
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    for i in range(max_retries):
        try:
            conn = await asyncpg.connect(db_url)
            await conn.close()
            print('✅ Database is ready!')
            return
        except Exception as e:
            if i < max_retries - 1:
                print(f'⏳ Waiting for database... ({i+1}/{max_retries})')
                time.sleep(retry_interval)
            else:
                raise Exception(f'Database connection failed after {max_retries} attempts: {e}')

asyncio.run(wait_for_db())
"

# Run Alembic migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Seed initial data in production (categories, default manager, teams)
echo "🌱 Seeding initial data..."
python -c "
import asyncio
from app.scripts.seed import seed_categories, seed_users
from app.scripts.seed_teams import seed_teams

async def seed_all():
    try:
        await seed_categories()
        print('✅ Categories seeded')
    except Exception as e:
        print(f'⚠️  Category seeding skipped (may already exist): {e}')
    
    try:
        await seed_users()
        print('✅ Default users seeded')
    except Exception as e:
        print(f'⚠️  User seeding skipped (may already exist): {e}')
    
    try:
        await seed_teams()
        print('✅ Teams seeded')
    except Exception as e:
        print(f'⚠️  Team seeding skipped (may already exist): {e}')

asyncio.run(seed_all())
"

echo "✅ Initialization complete!"
echo "🚀 Starting uvicorn server..."

# Execute the main command (passed as arguments to this script)
exec "$@"
