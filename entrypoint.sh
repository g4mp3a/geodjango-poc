#!/bin/bash
set -e

# Collect static files
# python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# Load businesses data
python manage.py load_businesses --clear

# Run the Django development server
exec python manage.py runserver 0.0.0.0:8000
