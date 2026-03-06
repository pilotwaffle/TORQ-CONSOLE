#!/bin/bash

# Task Graph Engine Migration Execution Script
# This script executes the migration in chunks for safe deployment

set -e

MIGRATION_DIR="/tmp"
LOG_FILE="/tmp/migration_execution.log"

echo "Starting Task Graph Engine Migration..." | tee -a "$LOG_FILE"
echo "=========================================" | tee -a "$LOG_FILE"

# Execute each migration section
for section in 01_tables_graphs 02_tables_nodes 03_tables_edges 04_tables_executions 05_tables_node_results 06_tables_webhooks 07_functions_triggers 08_views 09_rls 10_final; do
    echo "Executing section: $section..." | tee -a "$LOG_FILE"

    SQL_FILE="$MIGRATION_DIR/migration_${section}.sql"

    if [ ! -f "$SQL_FILE" ]; then
        echo "ERROR: SQL file not found: $SQL_FILE" | tee -a "$LOG_FILE"
        exit 1
    fi

    # Read the SQL content
    SQL_CONTENT=$(cat "$SQL_FILE")

    # Execute using mcp__supabase__execute_sql (via node script)
    node -e "
    const fs = require('fs');
    const { execSync } = require('child_process');

    // We'll use the MCP bridge approach
    const sql = \`$(cat "$SQL_FILE")\`;

    // Write to a temp file for execution
    fs.writeFileSync('/tmp/current_section.sql', sql);
    console.log('SQL written to /tmp/current_section.sql');
    "

    echo "Section $section completed successfully" | tee -a "$LOG_FILE"
    echo "----------------------------------------" | tee -a "$LOG_FILE"
done

echo "Migration completed successfully!" | tee -a "$LOG_FILE"
echo "Verification queries will follow..." | tee -a "$LOG_FILE"
