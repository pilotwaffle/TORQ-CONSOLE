const fs = require('fs');
const path = require('path');

// Load environment variables
const envPath = path.join(__dirname, '.env');
const envContent = fs.readFileSync(envPath, 'utf8');

const supabaseUrl = envContent.match(/SUPABASE_URL=(.+)/)?.[1]?.trim();
const supabaseKey = envContent.match(/SUPABASE_SERVICE_ROLE_KEY=(.+)/)?.[1]?.trim();

if (!supabaseUrl || !supabaseKey) {
    console.error('ERROR: Supabase credentials not found in .env file');
    process.exit(1);
}

// Extract project ref from URL
const projectRef = supabaseUrl.match(/https:\/\/([^.]+)/)?.[1];

// Decode the JWT to get the database password
// For Supabase service role key, the password is in the key itself
// The connection string format for Supabase is:
// postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

// The service role key contains the database password
// We need to use the actual database password, not the JWT token

// Get the database password from env or use a default approach
let dbPassword = envContent.match(/SUPABASE_DB_PASSWORD=(.+)/)?.[1]?.trim();

// If no explicit password, we'll need to get it from the dashboard
// For now, let's try the pooler connection with a different format

console.log('Supabase Project Ref:', projectRef);
console.log('\nNote: Supabase requires the database password for direct PostgreSQL connection.');
console.log('The service role key is for API access, not PostgreSQL connection.\n');

// Read the migration file
const migrationPath = path.join(__dirname, 'migrations', '001_task_graph_engine_production_safe.sql');
const migrationSQL = fs.readFileSync(migrationPath, 'utf8');

console.log('Migration SQL length:', migrationSQL.length, 'characters');

// Write to a temp file
fs.writeFileSync('/tmp/task_graph_migration.sql', migrationSQL);
fs.writeFileSync('E:/TORQ-CONSOLE/task_graph_migration.sql', migrationSQL);

console.log('\nMigration saved to:');
console.log('  - /tmp/task_graph_migration.sql');
console.log('  - E:/TORQ-CONSOLE/task_graph_migration.sql');

console.log('\n========================================');
console.log('MIGRATION EXECUTION OPTIONS');
console.log('========================================\n');

console.log('Option 1: Use Supabase Dashboard (RECOMMENDED)');
console.log('----------------------------------------------');
console.log('1. Go to: https://app.supabase.com/project/' + projectRef + '/sql/new');
console.log('2. Copy the contents of: E:/TORQ-CONSOLE/task_graph_migration.sql');
console.log('3. Paste into the SQL Editor');
console.log('4. Click "Run" to execute\n');

console.log('Option 2: Use Supabase CLI');
console.log('-------------------------');
console.log('1. Install Supabase CLI: npm install -g supabase');
console.log('2. Link your project: supabase link --project-ref ' + projectRef);
console.log('3. Execute: supabase db execute --file task_graph_migration.sql\n');

console.log('Option 3: Use psql with database password');
console.log('----------------------------------------');
console.log('1. Get your database password from:');
console.log('   https://app.supabase.com/project/' + projectRef + '/settings/database');
console.log('2. Run: psql "postgresql://postgres:[PASSWORD]@db.' + projectRef + '.supabase.co:5432/postgres" -f task_graph_migration.sql\n');

console.log('========================================');
console.log('AUTOMATING WITH SUPABASE REST API');
console.log('========================================\n');

// Try using Supabase REST API via fetch
async function executeViaRestAPI() {
    const https = require('https');

    // Split SQL into manageable chunks
    const statements = [];
    let currentStatement = '';
    let inFunction = false;
    let parenDepth = 0;

    const lines = migrationSQL.split('\n');
    for (const line of lines) {
        const trimmed = line.trim();

        if (trimmed.startsWith('CREATE OR REPLACE FUNCTION') || trimmed.startsWith('CREATE FUNCTION')) {
            inFunction = true;
        }

        if (!trimmed.startsWith('--')) {
            parenDepth += (trimmed.match(/\(/g) || []).length;
            parenDepth -= (trimmed.match(/\)/g) || []).length;
        }

        currentStatement += line + '\n';

        if (inFunction && trimmed.endsWith('LANGUAGE plpgsql;')) {
            inFunction = false;
            parenDepth = 0;
            statements.push(currentStatement.trim());
            currentStatement = '';
        } else if (!inFunction && trimmed.endsWith(';') && parenDepth <= 0) {
            const nextLineIdx = lines.indexOf(line) + 1;
            const nextLine = nextLineIdx < lines.length ? lines[nextLineIdx].trim() : '';

            if (!nextLine.startsWith('CREATE INDEX') &&
                !nextLine.startsWith('CREATE UNIQUE INDEX') &&
                !nextLine.startsWith('CREATE POLICY') &&
                !nextLine.startsWith('CREATE TRIGGER') &&
                !nextLine.startsWith('ALTER TABLE') &&
                !nextLine.startsWith('CREATE VIEW')) {
                statements.push(currentStatement.trim());
                currentStatement = '';
            }
        }
    }

    if (currentStatement.trim()) {
        statements.push(currentStatement.trim());
    }

    // Filter out comment-only blocks
    const filteredStatements = statements.filter(s =>
        s.trim() && !s.trim().match(/^--+[\s\S]*?--+$/) && !s.trim().startsWith('-- ===')
    );

    console.log(`Found ${filteredStatements.length} SQL statements to execute\n`);

    // Execute via REST API using node-fetch or https
    for (let i = 0; i < Math.min(3, filteredStatements.length); i++) {
        const stmt = filteredStatements[i];
        if (!stmt || stmt.startsWith('--')) continue;

        console.log(`Statement ${i + 1}: ${stmt.substring(0, 80)}...`);
    }
    console.log(`... and ${filteredStatements.length - 3} more statements\n`);

    console.log('To execute via REST API, use the Supabase client or fetch:');
    console.log('POST ' + supabaseUrl + '/rest/v1/rpc/exec_sql');
    console.log('Headers: apikey: [ANON_KEY], Authorization: Bearer [SERVICE_ROLE_KEY]');
}

executeViaRestAPI().then(() => {
    console.log('\n========================================');
    console.log('SUMMARY');
    console.log('========================================');
    console.log('The Task Graph Engine migration includes:');
    console.log('- 6 tables (task_graphs, task_nodes, task_edges, task_executions, task_node_results, task_webhooks)');
    console.log('- Multiple indexes for performance');
    console.log('- State machine triggers for runtime tables');
    console.log('- RLS policies for tenant isolation');
    console.log('- 1 view for execution summaries');
    console.log('\nPlease execute the SQL using one of the options above.');
}).catch(err => {
    console.error('Error:', err.message);
});
