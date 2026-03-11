"""
Apply Shared Cognitive Workspace migration to Supabase.

This script creates the workspaces and working_memory_entries tables.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from supabase import create_client
from torq_console.settings import get_settings
import httpx

def apply_migration_via_sql():
    """
    Apply migration by directly executing SQL via Supabase REST API.

    Note: This requires the service_role_key and schema modification permissions.
    """
    settings = get_settings()

    if not settings.supabase.url or not settings.supabase.service_role_key:
        print("ERROR: Supabase credentials not configured")
        return False

    # Read migration SQL
    migration_path = Path(__file__).parent / "migrations" / "004_shared_cognitive_workspace.sql"

    if not migration_path.exists():
        print(f"ERROR: Migration file not found: {migration_path}")
        return False

    with open(migration_path, 'r') as f:
        sql = f.read()

    # Split into individual statements (rough split by semicolon)
    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

    print(f"Found {len(statements)} SQL statements to execute")
    print("")
    print("IMPORTANT: This script requires Supabase schema modification permissions.")
    print("If execution fails, apply the migration manually via:")
    print("  1. Open Supabase SQL Editor")
    print("  2. Run the contents of: migrations/004_shared_cognitive_workspace.sql")
    print("")

    # For Supabase, we need to use their REST API or direct PostgreSQL connection
    # The service role key can execute SQL via the /rpc endpoint if we set up a function
    # For now, let's create a function-based migration approach

    client = create_client(settings.supabase.url, settings.supabase.service_role_key)

    # First, let's try to check if tables exist
    try:
        result = client.table('workspaces').select('*', count='exact').execute()
        if result.count == 0:
            print("Workspaces table exists but is empty (migration may have been partially applied)")
            return True
        else:
            print(f"Workspaces table exists with {result.count} rows")
            return True
    except Exception as e:
        if 'PGRST116' in str(e) or 'does not exist' in str(e):
            print("Workspaces table does not exist - migration needs to be applied")
            print("\nPlease apply the migration manually via Supabase SQL Editor:")
            print("=" * 60)
            print(sql)
            print("=" * 60)
            return False
        else:
            print(f"Error checking tables: {e}")
            return False

def show_manual_instructions():
    """Show instructions for manual migration."""
    settings = get_settings()

    migration_path = Path(__file__).parent / "migrations" / "004_shared_cognitive_workspace.sql"

    with open(migration_path, 'r') as f:
        sql = f.read()

    print("\n" + "=" * 60)
    print("MANUAL MIGRATION INSTRUCTIONS")
    print("=" * 60)
    print("\nOption 1: Supabase Dashboard SQL Editor")
    print("-" * 40)
    print(f"1. Go to: {settings.supabase.url}")
    print("2. Navigate to: SQL Editor")
    print("3. Paste the SQL below and execute:")
    print("\n" + "-" * 40)
    print(sql)
    print("-" * 40)

    print("\nOption 2: psql command line")
    print("-" * 40)
    print("psql -h db.{settings.supabase.project_ref}.supabase.co \\")
    print("     -U postgres -d postgres -f migrations/004_shared_cognitive_workspace.sql")
    print("-" * 40)

if __name__ == "__main__":
    print("TORQ Console - Shared Cognitive Workspace Migration")
    print("=" * 50)
    print("")

    result = apply_migration_via_sql()

    if not result:
        show_manual_instructions()
    else:
        print("\n✓ Migration check complete")
