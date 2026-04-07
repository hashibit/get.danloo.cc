#!/bin/sh
set -e

echo "Waiting for database to be ready..."
while ! /workspace/.venv/bin/python python_wrapper.py -c "
import pymysql
try:
    conn = pymysql.connect(host='db', user='danloo', password='password', database='danloo')
    conn.close()
    print('Database is ready!')
except Exception as e:
    print(f'Database not ready: {e}')
    exit(1)
"; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "Running database migrations..."
cd /workspace/backend && /workspace/.venv/bin/python python_wrapper.py -c "
import sys
sys.path.insert(0, '/home/appuser/.local/lib/python3.11/site-packages')
import alembic.config
alembic.config.main(argv=['upgrade', 'head'])
"

echo "Starting application..."
cd /workspace/backend && exec /workspace/.venv/bin/python python_wrapper.py -c "
import sys
sys.path.insert(0, '/home/appuser/.local/lib/python3.11/site-packages')
import uvicorn
uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True, reload_dirs=['/workspace/backend', '/workspace/common'])
"
