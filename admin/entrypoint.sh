#!/bin/sh

# Admin service entrypoint script

# Run migrations
echo "Running migrations..."
/workspace/.venv/bin/python manage.py migrate

# Create superuser if it doesn't exist
echo "Creating superuser..."
/workspace/.venv/bin/python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully.')
else:
    print('Superuser already exists.')
"

# Collect static files
echo "Collecting static files..."
/workspace/.venv/bin/python manage.py collectstatic --noinput

# Start the server
echo "Starting admin server..."
/workspace/.venv/bin/python manage.py runserver 0.0.0.0:8003
