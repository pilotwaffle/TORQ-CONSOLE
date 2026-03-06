/**
 * Execute Supabase migration via REST API using individual CREATE TABLE statements
 * This bypasses the direct PostgreSQL connection issues
 */

const https = require('https');
const fs = require('fs');

const SUPABASE_URL = 'https://npukynbaglmcdvzyklqa.supabase.co';
const SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wdWt5bmJhZ2xtY2R2enlrbHFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTU2MDUzNCwiZXhwIjoyMDg3MTM2NTM0fQ.-O3TTF2rr9_kUfOk9oD5Q_Fe494wtPxHOJsga5oT7Pk';

// Read migration SQL
const migrationSQL = fs.readFileSync('migrations/001_task_graph_engine_production_safe.sql', 'utf8');

console.log('Migration SQL file loaded');
console.log('Size:', migrationSQL.length, 'characters\n');

// The Supabase Management API can execute SQL
// We need to use the v1 SQL endpoint with proper authentication

// First, let's list existing tables to verify our connection
async function listTables() {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: 'npukynbaglmcdvzyklqa.supabase.co',
            port: 443,
            path: '/rest/v1/',
            method: 'GET',
            headers: {
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                if (res.statusCode === 200) {
                    const openapi = JSON.parse(body);
                    const tables = Object.keys(openapi.paths || {}).filter(p => p.startsWith('/') && p !== '/');
                    resolve(tables);
                } else {
                    reject(new Error(`HTTP ${res.statusCode}`));
                }
            });
        });

        req.on('error', reject);
        req.end();
    });
}

// Execute SQL via the SQL Editor API
async function executeSQLViaAPI(sql) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({ query: sql });

        const options = {
            hostname: 'npukynbaglmcdvzyklqa.supabase.co',
            port: 443,
            path: '/rest/v1/rpc/exec_sql',  // This may not exist - need to find the correct endpoint
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'apikey': SUPABASE_SERVICE_KEY,
                'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
                'Content-Length': data.length
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    try {
                        resolve(JSON.parse(body));
                    } catch {
                        resolve(body);
                    }
                } else {
                    reject(new Error(`HTTP ${res.statusCode}: ${body}`));
                }
            });
        });

        req.on('error', reject);
        req.write(data);
        req.end();
    });
}

// Main execution
async function main() {
    console.log('Attempting to execute migration...\n');
    console.log('NOTE: Due to limitations in the Supabase REST API,');
    console.log('this script provides instructions for manual execution.\n');

    try {
        const tables = await listTables();
        console.log('Existing tables:', tables.slice(0, 10).join(', '), `(${tables.length} total)`);
    } catch (err) {
        console.error('Failed to list tables:', err.message);
    }

    console.log('\n========================================');
    console.log('MIGRATION EXECUTION OPTIONS');
    console.log('========================================\n');

    console.log('Option 1: Use Supabase Dashboard (RECOMMENDED)');
    console.log('  1. Go to: https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql');
    console.log('  2. Paste the contents of: migrations/001_task_graph_engine_production_safe.sql');
    console.log('  3. Click "Run"\n');

    console.log('Option 2: Use Supabase CLI with access token');
    console.log('  1. Generate access token at: https://supabase.com/dashboard/account/tokens');
    console.log('  2. Run: export SUPABASE_ACCESS_TOKEN=your_token');
    console.log('  3. Run: npx supabase db execute --project-ref npukynbaglmcdvzyklqa --file migrations/001_task_graph_engine_production_safe.sql\n');

    console.log('Option 3: Use psql with database password');
    console.log('  1. Find database password in Dashboard > Settings > Database');
    console.log('  2. Run: psql "postgresql://postgres:[password]@db.npukynbaglmcdvzyklqa.supabase.co:5432/postgres" -f migrations/001_task_graph_engine_production_safe.sql\n');

    console.log('========================================');
    console.log('EXPECTED OBJECTS TO BE CREATED');
    console.log('========================================\n');

    console.log('Tables (6):');
    console.log('  - task_graphs');
    console.log('  - task_nodes');
    console.log('  - task_edges');
    console.log('  - task_executions');
    console.log('  - task_node_results');
    console.log('  - task_webhooks\n');

    console.log('Functions (4):');
    console.log('  - update_updated_at_column');
    console.log('  - enforce_execution_state_transition');
    console.log('  - enforce_node_result_state_transition');
    console.log('  - generate_idempotency_key\n');

    console.log('Triggers (6):');
    console.log('  - update_task_graphs_updated_at');
    console.log('  - update_task_nodes_updated_at');
    console.log('  - update_task_webhooks_updated_at');
    console.log('  - enforce_execution_state_transition_trigger');
    console.log('  - enforce_node_result_state_transition_trigger\n');

    console.log('View (1):');
    console.log('  - execution_summary_view\n');

    // Write the migration to a temp file for easy access
    fs.writeFileSync('E:/TORQ-CONSOLE/migration_to_execute.sql', migrationSQL);
    console.log('Migration SQL written to: E:/TORQ-CONSOLE/migration_to_execute.sql');
}

main().catch(console.error);
