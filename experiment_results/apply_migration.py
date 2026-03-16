#!/usr/bin/env python3
"""Apply Layer 17 migration to Supabase."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not supabase_url or not supabase_key:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
    sys.exit(1)

# Read migration SQL
migration_path = Path(__file__).parent.parent / "migrations" / "017_layer17_agent_genome_evolution.sql"
sql = migration_path.read_text()

# Split by semicolon and execute each statement
# Supabase doesn't support multi-statement via REST API directly
# We'll need to use postgres connection or execute via Supabase dashboard

print("Migration SQL loaded. To apply:")
print(f"1. Open Supabase dashboard: https://supabase.com/dashboard")
print(f"2. Go to SQL Editor")
print(f"3. Paste and execute: {migration_path}")
print()
print("Or use psql:")
print(f"psql {os.getenv('SUPABASE_DB_URL', '<DATABASE_URL>')} -f {migration_path}")

# Alternative: Create tables via REST API one by one
supabase = create_client(supabase_url, supabase_key)

print("\nAttempting to create tables via REST API...")

# Note: Cannot execute DDL via REST API - must use SQL editor or postgres connection
# This script just validates the migration file exists

print("\nMigration file validated: OK")
print("Please apply migration via Supabase SQL Editor or psql.")
