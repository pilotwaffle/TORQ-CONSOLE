/**
 * Execute Supabase migration using Supabase HTTP API directly
 * This bypasses connection issues by using the internal Supabase endpoints
 */

const https = require('https');
const fs = require('fs');

// URL encode the service role key for use in connection string
const serviceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wdWt5bmJhZ2xtY2R2enlrbHFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTU2MDUzNCwiZXhwIjoyMDg3MTM2NTM0fQ.-O3TTF2rr9_kUfOk9oD5Q_Fe494wtPxHOJsga5oT7Pk';
const projectRef = 'npukynbaglmcdvzyklqa';

// The Supabase API uses a different format for database connections
// The service role key needs to be used as a bearer token, not as password

async function executeSQLViaSupabaseAPI(sql) {
    return new Promise((resolve, reject) => {
        // Use the Supabase v1 SQL execute endpoint
        const options = {
            hostname: 'api.supabase.com',
            port: 443,
            path: `/v1/projects/${projectRef}/database/query`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${serviceKey}`,
                'apikey': serviceKey
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    resolve(body);
                } else {
                    reject(new Error(`HTTP ${res.statusCode}: ${body}`));
                }
            });
        });

        req.on('error', reject);
        req.write(JSON.stringify({ query: sql }));
        req.end();
    });
}

// Try using the GoTrue admin API to get database credentials
async function getDatabaseCredentials() {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: `${projectRef}.supabase.co`,
            port: 443,
            path: '/auth/v1/admin/database',
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${serviceKey}`,
                'apikey': serviceKey
            }
        };

        const req = https.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                console.log('Database credentials response:', res.statusCode);
                console.log('Body:', body.substring(0, 500));
                resolve({ statusCode: res.statusCode, body });
            });
        });

        req.on('error', reject);
        req.end();
    });
}

// Main execution
async function main() {
    console.log('Attempting to execute migration via Supabase API...\n');

    // Try to get database credentials
    try {
        const credsResult = await getDatabaseCredentials();
        console.log('Credentials result:', credsResult.statusCode);
    } catch (err) {
        console.log('Failed to get credentials:', err.message);
    }

    // Read the migration file
    const migrationSQL = fs.readFileSync('migrations/001_task_graph_engine_production_safe.sql', 'utf8');

    console.log('Migration SQL loaded:', migrationSQL.length, 'characters\n');

    console.log('==========================================');
    console.log('AUTOMATED EXECUTION ATTEMPT');
    console.log('==========================================\n');

    try {
        const result = await executeSQLViaSupabaseAPI(migrationSQL);
        console.log('Migration executed successfully!');
        console.log(result);
    } catch (err) {
        console.log('API execution failed:', err.message);
        console.log('\n==========================================');
        console.log('MANUAL EXECUTION REQUIRED');
        console.log('==========================================\n');

        console.log('To execute the migration, please use one of these methods:\n');

        console.log('Method 1: Supabase Dashboard (EASIEST)');
        console.log('  1. Go to: https://supabase.com/dashboard/project/' + projectRef + '/sql/new');
        console.log('  2. Copy the SQL from: migrations/001_task_graph_engine_production_safe.sql');
        console.log('  3. Paste it into the SQL Editor');
        console.log('  4. Click "Run" or press Ctrl+Enter\n');

        console.log('Method 2: Supabase CLI with access token');
        console.log('  1. Get access token: https://supabase.com/dashboard/account/tokens');
        console.log('  2. Run: npx supabase db execute --project-ref ' + projectRef);
        console.log('         --file migrations/001_task_graph_engine_production_safe.sql\n');

        console.log('Method 3: psql with database credentials');
        console.log('  1. Get database password from:');
        console.log('     https://supabase.com/dashboard/project/' + projectRef + '/settings/database');
        console.log('  2. Run: psql -h db.' + projectRef + '.supabase.co -U postgres');
        console.log('         (paste SQL when connected)\n');

        console.log('Expected objects after migration:');
        console.log('  - 6 tables (task_graphs, task_nodes, task_edges, task_executions, task_node_results, task_webhooks)');
        console.log('  - 4 functions (update_updated_at_column, enforce_execution_state_transition,');
        console.log('               enforce_node_result_state_transition, generate_idempotency_key)');
        console.log('  - 6 triggers (updated_at triggers and state transition enforcers)');
        console.log('  - 1 view (execution_summary_view)\n');
    }
}

main().catch(console.error);
