"""
Apply chat_sessions migration using psycopg2.

This script connects directly to Supabase PostgreSQL and applies the migration.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")

if not SUPABASE_URL:
    print("ERROR: SUPABASE_URL must be set")
    sys.exit(1)

# Parse Supabase URL to get connection details
# Format: https://<project_id>.supabase.co
# We need to construct the PostgreSQL connection string

print("=" * 60)
print("APPLYING CHAT_SESSIONS MIGRATION")
print("=" * 60)
print()

# Supabase uses postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
# We need the database password from SUPABASE_SERVICE_ROLE_KEY or DB_PASSWORD

db_password = os.environ.get("SUPABASE_DB_PASSWORD")
project_id = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "").split("/")[0]

print(f"Project ID: {project_id}")
print()

# The connection string format for Supabase
conn_string_template = "postgresql://postgres.{project_id}:{password}@db.{project_id}.supabase.co:5432/postgres"

print("To apply this migration, you need the database password.")
print()
print("Options to get the password:")
print("1. Go to Supabase Dashboard > Project Settings > Database")
print("2. Scroll to 'Connection string' and copy the password")
print("3. Set SUPABASE_DB_PASSWORD environment variable")
print()
print("Or use the SQL Editor in Supabase Dashboard:")
print("1. Go to https://app.supabase.com")
print("2. Select your project")
print("3. Click SQL Editor")
print("4. Run the migration SQL from migrations/003_chat_sessions_table.sql")
print()

if not db_password:
    print("SUPABASE_DB_PASSWORD not set - using SQL Editor approach")
    print()
    print("Please run this SQL in your Supabase SQL Editor:")
    print("=" * 60)

    with open("migrations/003_chat_sessions_table.sql", "r") as f:
        print(f.read())

    print("=" * 60)
    sys.exit(0)

# If password is set, try to apply directly
try:
    conn_string = conn_string_template.format(project_id=project_id, password=db_password)

    print(f"Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Connected!")

    with open("migrations/003_chat_sessions_table.sql", "r") as f:
        migration_sql = f.read()

    print("Applying migration...")
    cursor.execute(migration_sql)

    print("Migration applied successfully!")

    # Verify
    cursor.execute("SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname='public' AND tablename='chat_sessions')")
    exists = cursor.fetchone()[0]

    if exists:
        print("Verified: chat_sessions table exists")
    else:
        print("Warning: table not found after migration")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    print()
    print("Falling back to SQL Editor approach...")
    print()
    print("Please run this SQL in your Supabase SQL Editor:")

    with open("migrations/003_chat_sessions_table.sql", "r") as f:
        print(f.read())

print("=" * 60)
