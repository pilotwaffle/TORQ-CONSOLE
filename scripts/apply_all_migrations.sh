#!/bin/bash
# ============================================================================
# Phase 5.1 Validation — Migration Setup Script
# ============================================================================
#
# This script applies all TORQ Console migrations to prepare the database
# for Phase 5.1 validation.
#
# Prerequisites:
# 1. Supabase project URL and ANON_KEY in .env file
# 2. psql command-line tool installed
# 3. Database connection string in DATABASE_URL environment variable
#
# Usage:
#   bash scripts/apply_all_migrations.sh
#
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "TORQ Console — Migration Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}Error: DATABASE_URL environment variable not set${NC}"
    echo ""
    echo "Please set DATABASE_URL:"
    echo "  export DATABASE_URL='postgresql://user:password@host:port/database'"
    echo ""
    echo "Or load from .env:"
    echo "  export \$(grep DATABASE_URL .env | xargs)"
    exit 1
fi

echo "Database connection:"
echo "$DATABASE_URL"
echo ""

# Parse DATABASE_URL to get connection params
# Expected format: postgresql://user:password@host:port/database
DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
if [ -z "$DB_HOST" ]; then
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^\/]*\)\/.*/\1/p')
fi
DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')

echo "Target database: $DB_NAME@$DB_HOST"
echo ""

# Test connection
echo "Testing database connection..."
if psql "$DATABASE_URL" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo ""
    echo "Please verify:"
    echo "1. DATABASE_URL is correct"
    echo "2. Database server is running"
    echo "3. Network/firewall allows connection"
    exit 1
fi
echo ""

# Check if schema_migrations table exists
echo "Checking migration state..."
MIGRATION_TABLE_EXISTS=$(psql "$DATABASE_URL" -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'schema_migrations');")

if [ "$MIGRATION_TABLE_EXISTS" = "t" ]; then
    echo -e "${GREEN}✓ schema_migrations table exists${NC}"

    # Get current migration version
    CURRENT_VERSION=$(psql "$DATABASE_URL" -tAc "SELECT MAX(version)::text FROM schema_migrations;")
    echo "Current migration version: ${CURRENT_VERSION:-none}"
else
    echo "schema_migrations table does not exist — creating..."
    psql "$DATABASE_URL" -f - << 'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
SQL
    echo -e "${GREEN}✓ schema_migrations table created${NC}"
fi
echo ""

# Find all migration files
MIGRATIONS_DIR="$(dirname "$0")/../migrations"
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo -e "${RED}Error: Migrations directory not found: $MIGRATIONS_DIR${NC}"
    exit 1
fi

echo "Scanning migrations directory: $MIGRATIONS_DIR"
echo ""

# Get list of migration files sorted
MIGRATION_FILES=$(ls -1 "$MIGRATIONS_DIR"/*.sql 2>/dev/null | sort)

if [ -z "$MIGRATION_FILES" ]; then
    echo -e "${YELLOW}No migration files found${NC}"
    exit 0
fi

# Count total migrations
TOTAL_MIGRATIONS=$(echo "$MIGRATION_FILES" | wc -l)
echo "Found $TOTAL_MIGRATIONS migration files"
echo ""

# Track applied migrations
APPLIED_COUNT=0
SKIPPED_COUNT=0
FAILED_COUNT=0

echo "=========================================="
echo "Applying Migrations"
echo "=========================================="
echo ""

for migration_file in $MIGRATION_FILES; do
    # Extract version from filename (e.g., 001_init.sql -> 001)
    filename=$(basename "$migration_file")
    version=$(echo "$filename" | cut -d'_' -f1)

    # Check if already applied
    APPLIED=$(psql "$DATABASE_URL" -tAc "SELECT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '$version');")

    if [ "$APPLIED" = "t" ]; then
        echo -e "${YELLOW}⊘ $filename${NC} — already applied"
        SKIPPED_COUNT=$((SKIPPED_COUNT + 1))
        continue
    fi

    echo -n "Applying $filename ... "

    # Apply migration
    if psql "$DATABASE_URL" -f "$migration_file" > /dev/null 2>&1; then
        # Record migration
        psql "$DATABASE_URL" -c "INSERT INTO schema_migrations (version) VALUES ('$version');" > /dev/null 2>&1
        echo -e "${GREEN}✓${NC}"
        APPLIED_COUNT=$((APPLIED_COUNT + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo "  Check migration file: $migration_file"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        # Continue with remaining migrations
    fi
done

echo ""
echo "=========================================="
echo "Migration Summary"
echo "=========================================="
echo ""
echo "Total migrations:   $TOTAL_MIGRATIONS"
echo -e "Applied:            ${GREEN}$APPLIED_COUNT${NC}"
echo -e "Skipped:            ${YELLOW}$SKIPPED_COUNT${NC}"
if [ $FAILED_COUNT -gt 0 ]; then
    echo -e "Failed:             ${RED}$FAILED_COUNT${NC}"
    echo ""
    echo -e "${RED}WARNING: Some migrations failed${NC}"
    echo "Review the output above for details."
else
    echo -e "Failed:             $FAILED_COUNT"
fi
echo ""

# Show current state
CURRENT_VERSION=$(psql "$DATABASE_URL" -tAc "SELECT MAX(version)::text FROM schema_migrations;")
echo "Current migration version: ${CURRENT_VERSION:-none}"
echo ""

# Verify key tables exist
echo "Verifying key tables..."
KEY_TABLES=(
    "missions"
    "mission_nodes"
    "mission_edges"
    "mission_events"
    "mission_handoffs"
    "workstream_states"
    "validation_telemetry"
    "validation_results"
)

for table in "${KEY_TABLES[@]}"; do
    EXISTS=$(psql "$DATABASE_URL" -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$table');")
    if [ "$EXISTS" = "t" ]; then
        echo -e "  ${GREEN}✓${NC} $table"
    else
        echo -e "  ${RED}✗${NC} $table (missing)"
    fi
done

echo ""
echo "=========================================="
if [ $FAILED_COUNT -eq 0 ]; then
    echo -e "${GREEN}Migration setup complete!${NC}"
    echo ""
    echo "You can now proceed with validation:"
    echo "  1. Start the backend server"
    echo "  2. Run: bash scripts/prepare_validation_env.sql"
    echo "  3. Create validation missions"
else
    echo -e "${RED}Migration setup incomplete${NC}"
    echo ""
    echo "Please resolve failed migrations before proceeding."
fi
echo "=========================================="
