"""
Apply chat_sessions migration to Supabase via REST API.

This script applies the 003_chat_sessions_table.sql migration.
"""

import os
import sys
from dotenv import load_dotenv
import httpx

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Read migration SQL
migration_path = os.path.join(os.path.dirname(__file__), "migrations", "003_chat_sessions_table.sql")

with open(migration_path, "r") as f:
    migration_sql = f.read()

async def apply_migration():
    """Apply migration via Supabase REST API."""

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        print()
        print("Please set these in your .env file or environment.")
        sys.exit(1)

    print("=" * 60)
    print("APPLYING CHAT_SESSIONS MIGRATION")
    print("=" * 60)
    print()
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Migration: {migration_path}")
    print()

    # Method 1: Try Supabase RPC/REST endpoint
    print("Attempting to apply migration via Supabase REST API...")
    print()

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Supabase doesn't have a direct SQL execution REST endpoint for DDL
            # We need to use the Supabase CLI or SQL Editor

            print("NOTE: Supabase REST API cannot execute DDL statements directly.")
            print()
            print("Please apply the migration using one of these methods:")
            print()
            print("Option 1: Supabase Dashboard (Easiest)")
            print("  1. Go to https://app.supabase.com")
            print("  2. Select your project")
            print("  3. Click SQL Editor in the left sidebar")
            print("  4. Click New Query")
            print("  5. Paste the contents below and click Run")
            print()
            print("=" * 60)
            print("COPY FROM HERE:")
            print("=" * 60)
            print(migration_sql)
            print("=" * 60)
            print("END OF SQL")
            print("=" * 60)
            print()
            print("Option 2: Use psql with connection string")
            print(f"  psql \"{SUPABASE_URL}\" < {migration_path}")
            print()
            print("Option 3: Install Supabase CLI and run:")
            print("  supabase db push")
            print()

            # Verify if table already exists
            print("Checking if chat_sessions table already exists...")

            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/chat_sessions",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}"
                },
                params={"limit": 1}
            )

            if response.status_code == 200:
                print()
                print("✅ chat_sessions table already exists!")
                print("   Migration may have been applied already.")
            elif response.status_code == 404:
                print()
                print("❌ chat_sessions table not found.")
                print("   Please apply the migration using Option 1 above.")
            else:
                print()
                print(f"Response: {response.status_code}")
                print(f"Message: {response.text}")

    except Exception as e:
        print(f"Error: {e}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(apply_migration())
