#!/bin/sh

# Check if PostgreSQL is up and running
DB_HOST="postgres"
DB_PORT="5432"

echo "Waiting for PostgreSQL to be available at $DB_HOST:$DB_PORT..."
until nc -z $DB_HOST $DB_PORT; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing command"

# Run migrations
python3 manage.py makemigrations
python3 manage.py migrate

# Execute the command passed as arguments
exec "$@"
