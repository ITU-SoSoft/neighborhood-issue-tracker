"""Load test configuration."""

import os

# Base URL for the API - defaults to staging
# Override with LOAD_TEST_BASE_URL environment variable
BASE_URL = os.getenv("LOAD_TEST_BASE_URL", "https://staging-api.mahallem.biz.tr")

# API Version prefix
API_PREFIX = "/api/v1"

# Timeouts
REQUEST_TIMEOUT = 30  # seconds

# Test user credentials - these should exist in the database
TEST_USERS = {
    "citizen": {
        "email": "loadtest_citizen@example.com",
        "password": "LoadTest123!",
        "phone_number": "+905551234567",
    },
    "support": {
        "email": "loadtest_support@example.com",
        "password": "LoadTest123!",
    },
    "manager": {
        "email": "loadtest_manager@example.com",
        "password": "LoadTest123!",
    },
}

# Spawn rates for different test scenarios
SPAWN_RATES = {
    "light": {"users": 10, "spawn_rate": 2},
    "medium": {"users": 50, "spawn_rate": 5},
    "heavy": {"users": 100, "spawn_rate": 10},
    "stress": {"users": 200, "spawn_rate": 20},
}

# Wait times between requests (in seconds)
MIN_WAIT = 1
MAX_WAIT = 3
