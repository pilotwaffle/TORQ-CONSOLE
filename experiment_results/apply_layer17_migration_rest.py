#!/usr/bin/env python3
"""
Apply Layer 17 migration using Supabase REST API with raw PostgreSQL connection.

This script tries multiple methods to apply the migration:
1. Direct psycopg2 connection (if DB password available)
2. Falls back to manual instructions
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

def try_psycopg2_migration():
    """Try to apply migration using psycopg2 direct connection."""
    try:
        import psycopg2
    except ImportError:
        print("[SKIP] psycopg2 not available")
        return False

    supabase_url = os.getenv("SUPABASE_URL")
    password = os.getenv("SUPABASE_DB_PASSWORD")

    if not password:
        # Try to extract from DATABASE_URL
        database_url = os.getenv("DATABASE_URL", "")
        if database_url and "postgresql" in database_url:
            parsed = urlparse(database_url)
            password = parsed.password

    if not password:
        print("[SKIP] No database password found")
        print("[INFO] Set SUPABASE_DB_PASSWORD in .env or provide DATABASE_URL with password")
        return False

    # Extract project ref
    if ".supabase.co" in supabase_url:
        project_ref = supabase_url.split("//")[1].split(".")[0]
    else:
        print(f"[ERROR] Invalid Supabase URL: {supabase_url}")
        return False

    db_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"

    migration_path = Path(__file__).parent.parent / "migrations" / "017_layer17_agent_genome_evolution.sql"
    if not migration_path.exists():
        print(f"[ERROR] Migration file not found: {migration_path}")
        return False

    sql = migration_path.read_text()

    try:
        print(f"[INFO] Connecting to PostgreSQL...")
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()

        print(f"[INFO] Applying Layer 17 migration...")
        cur.execute(sql)
        conn.commit()

        print("[OK] Migration applied successfully!")

        # Verify tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('agent_genomes', 'l16_ecosystem_signals', 'benchmark_evaluations')
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"[OK] Created tables: {', '.join(tables)}")

        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def print_manual_instructions():
    """Print manual application instructions."""
    supabase_url = os.getenv("SUPABASE_URL")
    if ".supabase.co" in supabase_url:
        project_ref = supabase_url.split("//")[1].split(".")[0]
    else:
        project_ref = "<your_project_ref>"

    migration_path = Path(__file__).parent.parent / "migrations" / "017_layer17_agent_genome_evolution.sql"

    print("\n" + "=" * 70)
    print("MANUAL MIGRATION REQUIRED")
    print("=" * 70)
    print("\nThe Layer 17 tables need to be created in Supabase.")
    print("\nOption 1: Supabase Dashboard SQL Editor (EASIEST)")
    print(f"  1. Open: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print(f"  2. Copy the SQL from: {migration_path}")
    print("  3. Paste and click 'Run'\n")

    print("Option 2: Set database password and re-run")
    print("  1. Get your database password from Supabase Dashboard:")
    print(f"     https://supabase.com/dashboard/project/{project_ref}/settings/database")
    print("  2. Add to .env: SUPABASE_DB_PASSWORD=your_password")
    print("  3. Re-run: python experiment_results/apply_layer17_migration_rest.py\n")

    print("Option 3: Use psql directly")
    print(f"  psql -h db.{project_ref}.supabase.co -U postgres -d postgres \\")
    print(f"       -f {migration_path}\n")

    print("=" * 70)


def main():
    print("=" * 70)
    print("Layer 17 Migration Application")
    print("=" * 70)

    # Try psycopg2 first
    if try_psycopg2_migration():
        print("\n[SUCCESS] Migration applied via psycopg2!")
        print("\nNext step: Run Cycle 001 with database persistence")
        print("  python experiment_results/run_layer17_cycle_with_db.py")
        return 0
    else:
        print_manual_instructions()
        return 1


if __name__ == "__main__":
    sys.exit(main())
