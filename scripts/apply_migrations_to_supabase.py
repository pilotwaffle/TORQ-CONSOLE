#!/usr/bin/env python3
"""
Apply Phase 5.1 migrations (018-020) to Supabase.

Uses direct PostgreSQL connection to Supabase for migration execution.
This bypasses the Supabase REST API to execute SQL directly.

Prerequisites:
- SUPABASE_URL and SUPABASE_DB_PASSWORD must be set in .env
- Or Supabase connection string in DATABASE_URL
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

# Load from .env
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

def get_supabase_db_url():
    """
    Convert Supabase REST URL to PostgreSQL connection string.

    Supabase URL format: https://<project_ref>.supabase.co
    DB connection: postgresql://postgres:[password]@db.<project_ref>.supabase.co:5432/postgres
    """
    supabase_url = os.getenv("SUPABASE_URL")
    password = os.getenv("SUPABASE_DB_PASSWORD")

    if not supabase_url:
        raise ValueError("SUPABASE_URL not found in environment")

    # Extract project ref from URL
    if ".supabase.co" in supabase_url:
        project_ref = supabase_url.split("//")[1].split(".")[0]
    else:
        raise ValueError(f"Invalid Supabase URL format: {supabase_url}")

    # If no password provided, try common defaults or DATABASE_URL
    if not password:
        database_url = os.getenv("DATABASE_URL", "")
        if database_url and "postgresql" in database_url:
            # Try to extract password from existing DATABASE_URL
            parsed = urlparse(database_url)
            password = parsed.password
            if password:
                print(f"[INFO] Using password from DATABASE_URL")
            else:
                raise ValueError(
                    "No database password found. Set either:\n"
                    "  - SUPABASE_DB_PASSWORD environment variable\n"
                    "  - DATABASE_URL with password included"
                )
        else:
            raise ValueError(
                "SUPABASE_DB_PASSWORD not set. You need to set:\n"
                "SUPABASE_DB_PASSWORD=your_db_password\n\n"
                "Find this in Supabase Dashboard: Project Settings > Database > Connection String"
            )

    # Build PostgreSQL connection string
    db_url = f"postgresql://postgres:{password}@db.{project_ref}.supabase.co:5432/postgres"
    return db_url


def apply_migration(conn, migration_file, migration_id):
    """Apply a single migration file to Supabase."""
    migration_path = os.path.join(
        os.path.dirname(__file__), '..', 'migrations', migration_file
    )

    if not os.path.exists(migration_path):
        print(f"[SKIP] {migration_file} not found")
        return False

    print(f"\n[APPYING] {migration_file}...")

    with open(migration_path, 'r') as f:
        sql = f.read()

    cur = conn.cursor()

    try:
        # Execute migration
        cur.execute(sql)
        conn.commit()
        print(f"[OK] {migration_file} applied successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] {migration_file} failed: {e}")
        return False
    finally:
        cur.close()


def verify_tables(conn):
    """Verify that Phase 5.1 tables exist."""
    cur = conn.cursor()

    tables_to_check = [
        'missions', 'mission_graphs', 'mission_nodes', 'mission_edges',
        'mission_events', 'mission_handoffs', 'workstream_states',
        'validation_telemetry', 'validation_results'
    ]

    print("\n[VERIFY] Checking Phase 5.1 tables...")

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = ANY(%s)
    """, (tables_to_check,))

    existing_tables = {row[0] for row in cur.fetchall()}
    cur.close()

    print(f"\n[STATUS] Tables found: {len(existing_tables)}/{len(tables_to_check)}")

    missing = set(tables_to_check) - existing_tables
    if missing:
        print(f"[WARN] Missing tables: {', '.join(missing)}")
        return False

    print("[OK] All Phase 5.1 tables present")
    return True


def main():
    """Apply migrations 018-020 to Supabase."""
    print("=" * 60)
    print("Phase 5.1 Migration to Supabase")
    print("=" * 60)

    try:
        # Get database URL
        db_url = get_supabase_db_url()
        print(f"\n[INFO] Connecting to Supabase PostgreSQL...")

        # Connect to Supabase
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        print("[OK] Connected to Supabase")

        # Verify current state
        print("\n[INFO] Checking current schema...")
        already_applied = verify_tables(conn)

        if already_applied:
            print("\n[INFO] Phase 5.1 tables already exist. Skipping migrations.")
            print("[INFO] Use --force to re-apply if needed.")
        else:
            # Apply migrations
            migrations = [
                "018_mission_graphs.sql",
                "019_execution_fabric.sql",
                "020_validation_telemetry.sql"
            ]

            print("\n[INFO] Applying migrations...")
            applied = 0
            for migration_file in migrations:
                if apply_migration(conn, migration_file, migration_file.split('_')[0]):
                    applied += 1

            print(f"\n[RESULT] Applied {applied}/{len(migrations)} migrations")

            # Verify after applying
            if applied > 0:
                verify_tables(conn)

        conn.close()
        print("\n" + "=" * 60)
        print("Migration complete")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Start TORQ backend: python -m torq_console.cli serve")
        print("2. Create validation mission via API")
        print("3. Run validation checks")

    except Exception as e:
        print(f"\n[FATAL] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
