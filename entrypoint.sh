#!/bin/sh

# wait_for_db.sh script content
DB_HOST="postgres"
DB_PORT="5432"
shift 2
cmd="$@"

# Check if PostgreSQL is up and running
echo "Waiting for PostgreSQL to be available at $DB_HOST:$DB_PORT..."
until nc -z $DB_HOST $DB_PORT; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - executing command"

# Run migrations and then start the server
python3 manage.py makemigrations && python3 manage.py migrate

# Execute the command passed as arguments
exec $cmd
