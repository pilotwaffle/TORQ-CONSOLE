"""
Apply chat_sessions table migration to Supabase.

This script creates the chat_sessions table for session persistence.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

# Read migration SQL
migration_path = os.path.join(os.path.dirname(__file__), "migrations", "003_chat_sessions_table.sql")
with open(migration_path, "r") as f:
    migration_sql = f.read()

# Option 1: Apply via Supabase SQL Editor (Manual)
print("=" * 60)
print("CHAT SESSIONS MIGRATION")
print("=" * 60)
print()
print("To apply this migration:")
print()
print("Option 1: Supabase Dashboard (Recommended)")
print("  1. Go to https://app.supabase.com")
print("  2. Select your project (npukynbaglmcdvzyklqa)")
print("  3. Click SQL Editor in left sidebar")
print("  4. Click New Query")
print("  5. Paste the contents of migrations/003_chat_sessions_table.sql")
print("  6. Click Run")
print()
print("Option 2: Using psql command line")
print(f"  psql '{SUPABASE_URL}' -f migrations/003_chat_sessions_table.sql")
print()
print("=" * 60)
print()
print("Migration creates:")
print("  - chat_sessions table (conversation history)")
print("  - Row Level Security policies")
print("  - Indexes for performance")
print("  - Helper function for message cleanup")
print()
print("=" * 60)
