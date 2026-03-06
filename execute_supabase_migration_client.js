/**
 * Execute Supabase migration using Supabase client library
 * Creates tables via RPC functions that need to be set up first
 */

const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');

const SUPABASE_URL = 'https://npukynbaglmcdvzyklqa.supabase.co';
const SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wdWt5bmJhZ2xtY2R2enlrbHFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTU2MDUzNCwiZXhwIjoyMDg3MTM2NTM0fQ.-O3TTF2rr9_kUfOk9oD5Q_Fe494wtPxHOJsga5oT7Pk';

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function executeViaRPC() {
    console.log('Attempting to execute SQL via RPC...\n');

    // Try to find an exec_sql function or similar
    const { data, error } = await supabase.rpc('exec_sql', {
        query: 'SELECT 1 as test'
    });

    if (error) {
        console.log('exec_sql RPC not available:', error.message);
        console.log('\nTo execute the migration, you need to:');
        console.log('1. Go to Supabase Dashboard SQL Editor:');
        console.log('   https://supabase.com/dashboard/project/npukynbaglmcdvzyklqa/sql');
        console.log('2. Paste the migration SQL and run it\n');

        // Try alternative: check if we can create a simple test table
        console.log('Testing database connection via simple query...');
        const { data: testData, error: testError } = await supabase
            .from('agents_registry')
            .select('*')
            .limit(1);

        if (testError) {
            console.error('Connection test failed:', testError.message);
        } else {
            console.log('Connection OK! Found', testData.length, 'rows in agents_registry');
        }

        return;
    }

    console.log('RPC result:', data);

    // If RPC works, read and execute the migration
    const migrationSQL = fs.readFileSync('migrations/001_task_graph_engine_production_safe.sql', 'utf8');
    console.log('Executing migration (', migrationSQL.length, 'bytes)...');

    const { data: migrationResult, error: migrationError } = await supabase.rpc('exec_sql', {
        query: migrationSQL
    });

    if (migrationError) {
        console.error('Migration failed:', migrationError.message);
    } else {
        console.log('Migration completed successfully!');
        console.log(migrationResult);
    }
}

// Alternative: Try to use the admin functions endpoint
async function tryAdminEndpoint() {
    console.log('Trying admin endpoint...\n');

    // Create tables one by one using REST API with proper SQL execution
    // This requires the "exec_sql" function to be installed

    const tables = [
        'task_graphs',
        'task_nodes',
        'task_edges',
        'task_executions',
        'task_node_results',
        'task_webhooks'
    ];

    console.log('Tables to be created:');
    tables.forEach(t => console.log('  -', t));
}

async function main() {
    await executeViaRPC();
    await tryAdminEndpoint();
}

main().catch(console.error);
