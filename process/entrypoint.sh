#!/bin/sh
set -e

echo "Starting Process service..."
exec /workspace/.venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001