#!/bin/bash
set -e

# Function to wait for database
wait_for_db() {
    echo "Waiting for database..."
    until python -c "import sqlite3; sqlite3.connect('${DATABASE_URL#sqlite:///}')" &> /dev/null; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is up and running"
}

# Collect static files
# python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

# Load businesses data
python manage.py load_businesses --clear

# Run the Django development server
exec python manage.py runserver 0.0.0.0:8000
