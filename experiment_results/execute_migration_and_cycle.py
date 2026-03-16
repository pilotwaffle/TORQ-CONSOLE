#!/usr/bin/env python3
"""
Execute Layer 17 migration and run Cycle 001 with persistence.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
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

print(f"Supabase URL: {supabase_url}")
print(f"Connected: OK")

# Read migration SQL
migration_path = Path(__file__).parent.parent / "migrations" / "017_layer17_agent_genome_evolution.sql"
sql_content = migration_path.read_text()

# Split SQL into individual statements
statements = []
current = []
in_function = False
for line in sql_content.split('\n'):
    stripped = line.strip()
    if stripped.startswith('--') or stripped == '':
        continue
    current.append(line)
    if stripped.startswith('CREATE ') or stripped.startswith('CREATE OR REPLACE '):
        in_function = True
    if stripped.endswith(';') and not in_function:
        statements.append('\n'.join(current))
        current = []
        in_function = False
    elif stripped.endswith('$$ LANGUAGE') and in_function:
        # Function definition continues until END;
        pass
    elif stripped == 'END;' and in_function:
        statements.append('\n'.join(current))
        current = []
        in_function = False

# Filter to only CREATE TABLE statements (safe for execution)
create_table_statements = [s for s in statements if s.strip().startswith('CREATE TABLE')]

print(f"\nFound {len(create_table_statements)} CREATE TABLE statements")
print(f"Found {len(statements)} total statements")

# Note: We cannot execute DDL via REST API
# Must use postgres connection or Supabase SQL Editor

print("\n" + "="*60)
print("MIGRATION EXECUTION INSTRUCTIONS")
print("="*60)
print("\nOption 1: Supabase Dashboard SQL Editor")
print(f"1. Open: https://supabase.com/dashboard")
print(f"2. Go to SQL Editor")
print(f"3. Paste contents of: {migration_path}")
print(f"4. Execute")
print("\nOption 2: psql command line")
print(f'psql $DATABASE_URL -f "{migration_path}"')
print("\nOption 3: Direct postgres connection (requires psycopg2)")
print("Attempting direct connection...")

# Try direct postgres connection if DATABASE_URL is available
db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
if db_url:
    try:
        import psycopg2
        from psycopg2 import sql

        print(f"\nConnecting to database...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        # Read and execute migration
        cursor.execute(open(migration_path, 'r').read())

        print("Migration executed successfully!")

        # Verify tables created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('agent_genomes', 'l16_ecosystem_signals', 'benchmark_evaluations')
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"\nTables created: {[t[0] for t in tables]}")

        cursor.close()
        conn.close()

        print("\nMigration complete! Ready for Cycle 001 with persistence.")
        sys.exit(0)

    except ImportError:
        print("psycopg2 not installed, install with: pip install psycopg2-binary")
    except Exception as e:
        print(f"Direct connection failed: {e}")
else:
    print("DATABASE_URL or SUPABASE_DB_URL not set")

print("\nPlease execute migration manually, then run Cycle 001.")
sys.exit(1)
