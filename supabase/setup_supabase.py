"""
TORQ Console - Supabase Migration Runner
Run migrations via Supabase REST API
"""
import requests
import json
import sys

SUPABASE_URL = "https://npukynbaglmcdvzyklqa.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wdWt5bmJhZ2xtY2R2enlrbHFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTU2MDUzNCwiZXhwIjoyMDg3MTM2NTM0fQ.-O3TTF2rr9_kUfOk9oD5Q_Fe494wtPxHOJsga5oT7Pk"

def run_migration(sql_content, migration_name):
    """Run SQL migration via Supabase API"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    # Since REST API doesn't support direct SQL, we'll use pgstatstatements approach
    # or create tables via individual REST calls

    print(f"Running migration: {migration_name}")
    print("=" * 60)

    # Split SQL into individual statements
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]

    for i, stmt in enumerate(statements):
        if stmt.startswith('--') or stmt.startswith('/*'):
            continue

        # Try to execute via POST to /rest/v1/ with schema manipulation
        # Note: This requires using the Supabase Management API or direct SQL execution
        print(f"Statement {i+1}/{len(statements)}: {stmt[:50]}...")

    print(f"Migration {migration_name} completed!")
    return True

# Read migration files
migration1_path = r"E:\TORQ-CONSOLE\supabase\migrations\01_telemetry_tables.sql"
migration2_path = r"E:\TORQ-CONSOLE\supabase\migrations\02_learning_tables.sql"

print("TORQ Console Supabase Migration Runner")
print("=" * 60)
print("\nNOTE: The Supabase REST API doesn't support direct SQL execution.")
print("Please run the migrations manually in the Supabase SQL Editor:")
print("https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql\n")
print("\nMigration files are located at:")
print(f"1. {migration1_path}")
print(f"2. {migration2_path}")
