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
if alembic upgrade head; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations FAILED!"
    echo "Attempting to show migration error details..."
    alembic upgrade head --sql 2>&1 || true
    echo "❌ Cannot proceed without successful migrations. Exiting."
    exit 1
fi

# Seed initial data in production (categories, default manager, teams)
echo "🌱 Seeding initial data..."
python -c "
import asyncio
import traceback
from app.scripts.seed import seed_categories, seed_users
from app.scripts.seed_teams import seed_teams

async def seed_all():
    try:
        await seed_categories()
        print('✅ Categories seeded')
    except Exception as e:
        print(f'⚠️  Category seeding skipped (may already exist): {e}')
        traceback.print_exc()
    
    try:
        await seed_users()
        print('✅ Default users seeded')
    except Exception as e:
        print(f'⚠️  User seeding skipped (may already exist): {e}')
        traceback.print_exc()
    
    try:
        await seed_teams()
        print('✅ Teams seeded')
    except Exception as e:
        print(f'⚠️  Team seeding skipped (may already exist): {e}')
        traceback.print_exc()

asyncio.run(seed_all())
"

# Seed test data for staging environment (controlled by SEED_TEST_DATA env var)
if [ "$SEED_TEST_DATA" = "true" ]; then
    echo "🌱 Seeding staging test data..."
    python -c "
import asyncio
from app.scripts.seed_fallback_team import main as seed_fallback
from app.scripts.seed_test_data import main as seed_test

async def seed_staging():
    try:
        await seed_fallback()
        print('✅ Fallback team seeded')
    except Exception as e:
        print(f'⚠️  Fallback team seeding error: {e}')
    
    try:
        await seed_test()
        print('✅ Test data seeded')
    except Exception as e:
        print(f'⚠️  Test data seeding error: {e}')

asyncio.run(seed_staging())
"
    echo "✅ Staging test data complete!"
fi

echo "✅ Initialization complete!"
echo "🚀 Starting uvicorn server..."

# Execute the main command (passed as arguments to this script)
exec "$@"
