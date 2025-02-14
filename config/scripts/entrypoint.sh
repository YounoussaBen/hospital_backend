#!/bin/sh
set -o errexit  # Exit immediately if a command exits with a non-zero status

# Upgrade pip to the latest version
pip install --upgrade pip

# Wait for the database to be available.
if [ -n "$POSTGRES_HOST" ] && [ -n "$POSTGRES_PORT" ]; then
  echo "Waiting for PostgreSQL at $POSTGRES_HOST:$POSTGRES_PORT..."
  while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    sleep 0.5
  done
  echo "PostgreSQL is up!"
fi

# Set production settings for Django
export DJANGO_SETTINGS_MODULE=config.settings.prod

# Run migrations and collect static files
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Create superuser in an idempotent manner (assumes your custom 'createsu' command handles existing users gracefully)
python manage.py createsu || echo "Superuser already exists or creation skipped"

# Execute the container's main command
exec "$@"
