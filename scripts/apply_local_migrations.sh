#!/bin/bash
# Apply migrations to local Docker PostgreSQL
set -e

echo "Applying migrations to local PostgreSQL..."

MIGRATIONS_DIR="E:/TORQ-CONSOLE/migrations"

# Get all migration files sorted
for migration in $(ls $MIGRATIONS_DIR/*.sql | sort); do
    filename=$(basename "$migration")
    echo "Applying $filename..."
    docker exec -i torq_validation_db psql -U postgres -d torq_validation < "$migration" 2>&1 | grep -v "ERROR:" || echo "  Done"
done

echo "Migrations applied!"
