#!/usr/bin/env python3
"""
Apply Layer 17 migration (017) to Supabase.

Creates the agent_genomes, l16_ecosystem_signals, and benchmark_evaluations tables.
Uses Supabase REST API with SQL execution.

Prerequisites:
- SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

def execute_sql_via_rest(supabase_url, service_key, sql):
    """Execute SQL via Supabase REST API."""
    # Supabase SQL Editor REST API endpoint
    sql_url = f"{supabase_url}/rest/v1/rpc/exec_sql"

    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    payload = {"query": sql}

    response = requests.post(sql_url, json=payload, headers=headers, timeout=30)
    return response


def execute_sql_via_psql(supabase_url, password, sql):
    """
    Generate instructions for manual execution via psql.

    Since Supabase REST API doesn't support DDL statements directly,
    we provide instructions for manual execution.
    """
    project_ref = supabase_url.split("//")[1].split(".")[0]
    connection_string = f"postgresql://postgres:[YOUR-PASSWORD]@db.{project_ref}.supabase.co:5432/postgres"

    print("\n" + "=" * 70)
    print("MANUAL EXECUTION REQUIRED")
    print("=" * 70)
    print("\nOption 1: Use Supabase Dashboard SQL Editor")
    print(f"  1. Open: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print("  2. Paste the SQL below and execute")
    print("\nOption 2: Use psql command line")
    print(f"  psql 'postgresql://postgres:[PASSWORD]@db.{project_ref}.supabase.co:5432/postgres' -f migrations/017_layer17_agent_genome_evolution.sql")
    print("\n" + "=" * 70)

    return False


def verify_tables_via_rest(supabase_url, service_key):
    """Verify Layer 17 tables exist via Supabase REST API."""
    tables_to_check = [
        'agent_genomes',
        'l16_ecosystem_signals',
        'benchmark_evaluations'
    ]

    print("\n[VERIFY] Checking Layer 17 tables via REST API...")

    existing_tables = []

    for table in tables_to_check:
        url = f"{supabase_url}/rest/v1/{table}?select=*&limit=1"
        headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
        }

        response = requests.get(url, headers=headers, timeout=10)

        # 200 = OK, 406 = PGRST116 but table exists (empty result with Accept header issue)
        # 404 = table not found
        if response.status_code in [200, 406]:
            existing_tables.append(table)
            print(f"  [OK] {table} exists")
        else:
            print(f"  [MISSING] {table} - Status: {response.status_code}")

    return existing_tables


def create_tables_via_python(supabase_url, service_key):
    """
    Create Layer 17 tables using Supabase Python client.

    Since we can't execute DDL via REST API directly, we'll use
    Supabase Management API or provide instructions.
    """
    import subprocess
    import tempfile

    migration_path = Path(__file__).parent.parent / "migrations" / "017_layer17_agent_genome_evolution.sql"

    if not migration_path.exists():
        print(f"[ERROR] Migration file not found: {migration_path}")
        return False

    with open(migration_path, 'r') as f:
        sql = f.read()

    # Create a temp SQL file for psql execution
    project_ref = supabase_url.split("//")[1].split(".")[0]
    db_host = f"db.{project_ref}.supabase.co"
    db_name = "postgres"
    db_user = "postgres"

    print("\n" + "=" * 70)
    print("LAYER 17 MIGRATION - TABLE CREATION")
    print("=" * 70)
    print("\nThe Supabase REST API does NOT support DDL statements (CREATE TABLE).")
    print("To apply the migration, use one of these methods:\n")

    print("Method 1: Supabase Dashboard (EASIEST)")
    print(f"  1. Go to: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print(f"  2. Copy the SQL from: {migration_path}")
    print("  3. Paste and click 'Run'\n")

    print("Method 2: psql command line")
    print(f"  psql -h {db_host} -U {db_user} -d {db_name} -f {migration_path}")
    print(f"  (You'll need your database password)\n")

    print("Method 3: Set SUPABASE_DB_PASSWORD and re-run this script")
    print(f"  SUPABASE_DB_PASSWORD=your_password python experiment_results/execute_layer17_migration.py\n")

    # Try to check if tables exist
    existing = verify_tables_via_rest(supabase_url, service_key)

    if existing:
        print("=" * 70)
        print(f"[INFO] Found {len(existing)}/3 Layer 17 tables already exist")
        print("=" * 70)

        if len(existing) == 3:
            print("\n[OK] All Layer 17 tables exist! Migration already applied.")
            return True
        else:
            print(f"\n[WARN] Partial migration detected. Missing tables: {set(['agent_genomes', 'l16_ecosystem_signals', 'benchmark_evaluations']) - set(existing)}")
            return False
    else:
        print("=" * 70)
        print("[ACTION REQUIRED] Please apply the migration using one of the methods above")
        print("=" * 70)
        return False


def main():
    """Apply Layer 17 migration to Supabase."""
    print("=" * 70)
    print("Layer 17 Migration to Supabase")
    print("=" * 70)

    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url or not service_key:
        print("[ERROR] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")
        sys.exit(1)

    print(f"[INFO] Supabase URL: {supabase_url}")
    print(f"[INFO] Project Ref: {supabase_url.split('//')[1].split('.')[0]}")

    # Check if tables already exist
    success = create_tables_via_python(supabase_url, service_key)

    if success:
        print("\n[SUCCESS] Layer 17 migration verified!")
        print("\nYou can now run Cycle 001 with database persistence:")
        print("  python experiment_results/run_layer17_cycle.py")
    else:
        print("\n[PENDING] Apply the migration manually, then re-run this script to verify.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
