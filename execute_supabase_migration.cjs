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
const connectionString = `postgresql://postgres.${projectRef}:${supabaseKey}@aws-0-us-east-1.pooler.supabase.com:6543/postgres`;

console.log('Supabase Project Ref:', projectRef);

// Read the migration file
const migrationPath = path.join(__dirname, 'migrations', '001_task_graph_engine_production_safe.sql');
const migrationSQL = fs.readFileSync(migrationPath, 'utf8');

console.log('Migration SQL length:', migrationSQL.length, 'characters');

// Write to a temp file for execution
fs.writeFileSync('/tmp/task_graph_migration.sql', migrationSQL);

console.log('\nMigration written to /tmp/task_graph_migration.sql');

// Try using pg module
async function executeMigration() {
    let client;
    try {
        const { Client } = require('pg');
        console.log('\nAttempting direct execution using node-postgres...');

        client = new Client({
            connectionString: connectionString,
            ssl: { rejectUnauthorized: false }
        });

        await client.connect();
        console.log('Connected to Supabase PostgreSQL');

        // Execute the entire migration
        await client.query(migrationSQL);
        console.log('Migration executed successfully!');

    } catch (err) {
        console.error('Execution error:', err.message);

        // Try statement-by-statement
        if (err.message.includes('syntax')) {
            console.log('\nTrying statement-by-statement execution...');

            const statements = [];
            let currentStatement = '';
            let inFunction = false;
            let parenDepth = 0;

            const lines = migrationSQL.split('\n');
            for (const line of lines) {
                const trimmed = line.trim();

                if (trimmed.startsWith('CREATE OR REPLACE FUNCTION')) {
                    inFunction = true;
                }

                // Track parentheses
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

                    // Combine related statements
                    if (!nextLine.startsWith('CREATE INDEX') &&
                        !nextLine.startsWith('CREATE UNIQUE INDEX') &&
                        !nextLine.startsWith('CREATE POLICY') &&
                        !nextLine.startsWith('CREATE TRIGGER') &&
                        !nextLine.startsWith('ALTER TABLE')) {
                        statements.push(currentStatement.trim());
                        currentStatement = '';
                    }
                }
            }

            if (currentStatement.trim()) {
                statements.push(currentStatement.trim());
            }

            console.log(`Executing ${statements.length} statements...`);

            let successCount = 0;
            let failCount = 0;

            for (let i = 0; i < statements.length; i++) {
                const stmt = statements[i].trim();
                if (!stmt || stmt.match(/^--+\s*$/)) continue;

                try {
                    await client.query(stmt);
                    successCount++;
                    if (successCount % 5 === 0) {
                        console.log(`Progress: ${successCount} statements executed...`);
                    }
                } catch (err) {
                    failCount++;
                    console.error(`Statement ${i + 1} failed:`, err.message.substring(0, 200));
                    // Continue with next statement
                }
            }

            console.log(`\nExecution complete: ${successCount} succeeded, ${failCount} failed`);
        }
    } finally {
        if (client) {
            await client.end();
        }
    }
}

// Run the migration
executeMigration().then(() => {
    console.log('\nMigration process completed!');
}).catch((err) => {
    console.error('\nFatal error:', err.message);
    console.log('\nPlease execute the SQL manually:');
    console.log('1. Copy the contents of: migrations/001_task_graph_engine_production_safe.sql');
    console.log('2. Go to Supabase Dashboard > SQL Editor');
    console.log('3. Paste and execute the SQL');
    process.exit(1);
});
