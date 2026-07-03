#!/bin/bash

# Backend database migration script
# Similar to Django's migrate command

set -e

# Change to backend directory
cd /opt/danloo/get.danloo.cc/backend

# Load environment variables if file exists
if [ -f "/opt/danloo/get.danloo.cc/.env" ]; then
    echo "Loading environment variables from /opt/danloo/get.danloo.cc/.env"
    # Use a safer method to load env vars
    set -a
    source /opt/danloo/get.danloo.cc/.env
    set +a
else
    echo "Warning: /opt/danloo/get.danloo.cc/.env not found"
fi

# Debug: show what DATABASE_URL is being used
echo "DATABASE_URL: $DATABASE_URL"

# Run alembic migrations
echo "Running backend database migrations..."
/usr/local/bin/uv run alembic upgrade head

echo "Backend migrations completed successfully."
