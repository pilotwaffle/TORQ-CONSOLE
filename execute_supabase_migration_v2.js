const fs = require('fs');
const { Client } = require('pg');

// Direct connection string format for Supabase
const connectionString = 'postgres://postgres.npukynbaglmcdvzyklqa:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5wdWt5bmJhZ2xtY2R2enlrbHFhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTU2MDUzNCwiZXhwIjoyMDg3MTM2NTM0fQ.-O3TTF2rr9_kUfOk9oD5Q_Fe494wtPxHOJsga5oT7Pk@aws-0-us-east-1.pooler.supabase.com:6543/postgres';

async function executeMigration() {
    const client = new Client({
        connectionString: connectionString,
        ssl: { rejectUnauthorized: false }
    });

    try {
        console.log('Connecting to Supabase...');
        await client.connect();
        console.log('Connected!\n');

        // Read migration file
        const migrationSQL = fs.readFileSync('migrations/001_task_graph_engine_production_safe.sql', 'utf8');

        // Execute the migration as a single block
        console.log('Executing migration (this may take a minute)...\n');
        await client.query(migrationSQL);
        console.log('Migration executed successfully!\n');

        // Verify objects created
        console.log('Verifying created objects...\n');

        const tablesResult = await client.query(`
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'task_%'
            ORDER BY table_name
        `);
        console.log('Tables created:', tablesResult.rows.map(r => r.table_name).join(', '));

        const indexesResult = await client.query(`
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'task_node_results'
            ORDER BY indexname
        `);
        console.log('Indexes on task_node_results:', indexesResult.rows.length);

        const triggersResult = await client.query(`
            SELECT tgname
            FROM pg_trigger
            WHERE tgname LIKE '%task%'
            OR tgname LIKE '%update%'
            OR tgname LIKE '%enforce%'
            ORDER BY tgname
        `);
        console.log('Triggers created:', triggersResult.rows.map(r => r.tgname).join(', '));

        const functionsResult = await client.query(`
            SELECT proname
            FROM pg_proc
            WHERE proname LIKE '%task%'
            OR proname LIKE '%generate%'
            OR proname LIKE '%update%'
            ORDER BY proname
        `);
        console.log('Functions created:', functionsResult.rows.map(r => r.proname).join(', '));

        await client.end();
        console.log('\nMigration complete!');

    } catch (err) {
        console.error('Migration failed:', err.message);
        if (err.stack) {
            console.error(err.stack);
        }
        await client.end().catch(() => {});
        process.exit(1);
    }
}

executeMigration();
