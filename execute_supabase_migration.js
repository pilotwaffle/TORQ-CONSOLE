const fs = require('fs');
const { Client } = require('pg');

// Load environment variables
const envContent = fs.readFileSync('.env', 'utf8');
const supabaseUrl = envContent.match(/SUPABASE_URL=(.+)/)?.[1]?.trim();
const supabaseKey = envContent.match(/SUPABASE_SERVICE_ROLE_KEY=(.+)/)?.[1]?.trim();

if (!supabaseUrl || !supabaseKey) {
    console.error('ERROR: Supabase credentials not found in .env file');
    process.exit(1);
}

// Extract project ref from URL and create connection string
const projectRef = supabaseUrl.match(/https:\/\/([^.]+)/)?.[1];
const connectionString = `postgresql://postgres.${projectRef}:${supabaseKey}@aws-0-us-east-1.pooler.supabase.com:6543/postgres`;

console.log('Supabase Project Ref:', projectRef);
console.log('Executing migration...\n');

// Read the migration file
const migrationSQL = fs.readFileSync('migrations/001_task_graph_engine_production_safe.sql', 'utf8');

async function executeMigration() {
    const client = new Client({
        connectionString: connectionString,
        ssl: { rejectUnauthorized: false }
    });

    try {
        await client.connect();
        console.log('Connected to Supabase PostgreSQL database\n');

        // Split the SQL into individual statements
        const statements = [];
        let currentStatement = '';
        let inFunction = false;
        let inDollarQuote = false;
        let dollarQuoteTag = '';

        const lines = migrationSQL.split('\n');

        for (const line of lines) {
            // Check for dollar quote start/end
            const dollarMatch = line.match(/\$\$/g);
            if (dollarMatch && dollarMatch.length === 1) {
                inDollarQuote = !inDollarQuote;
            }

            // Check for CREATE OR REPLACE FUNCTION
            if (line.trim().match(/CREATE\s+OR\s+REPLACE\s+FUNCTION/i)) {
                inFunction = true;
            }

            currentStatement += line + '\n';

            // End of function (with LANGUAGE plpgsql or similar)
            if (inFunction && line.trim().match(/\$\s*LANGUAGE\s+\w+/)) {
                inFunction = false;
                statements.push(currentStatement.trim());
                currentStatement = '';
            }
            // Regular statement end (outside of function/dollar quote)
            else if (!inFunction && !inDollarQuote && line.trim() && !line.trim().startsWith('--') && line.trim().endsWith(';')) {
                statements.push(currentStatement.trim());
                currentStatement = '';
            }
        }

        if (currentStatement.trim()) {
            statements.push(currentStatement.trim());
        }

        console.log(`Executing ${statements.length} statements...\n`);

        let successCount = 0;
        let errorCount = 0;
        let skipCount = 0;

        for (let i = 0; i < statements.length; i++) {
            const stmt = statements[i].trim();
            if (!stmt || stmt.startsWith('--') || stmt.match(/^\/\*/)) {
                skipCount++;
                continue;
            }

            try {
                await client.query(stmt);
                console.log(`[${i + 1}/${statements.length}] OK`);
                successCount++;
            } catch (err) {
                const stmtPreview = stmt.substring(0, 100).replace(/\n/g, ' ');
                console.error(`[${i + 1}/${statements.length}] ERROR: ${err.message}`);
                console.error(`   Statement: ${stmtPreview}...`);
                errorCount++;

                // Don't fail on "already exists" errors
                if (!err.message.includes('already exists') && !err.message.includes('duplicate')) {
                    // Continue anyway for idempotency
                }
            }
        }

        await client.end();

        console.log('\n=====================================');
        console.log('Migration Summary:');
        console.log(`  Success: ${successCount}`);
        console.log(`  Errors:  ${errorCount}`);
        console.log(`  Skipped: ${skipCount}`);
        console.log('=====================================\n');

        // Verify objects created
        console.log('Verifying created objects...\n');

        const verifyClient = new Client({
            connectionString: connectionString,
            ssl: { rejectUnauthorized: false }
        });
        await verifyClient.connect();

        // Check tables
        const tablesResult = await verifyClient.query(`
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'task_%'
            ORDER BY table_name
        `);
        console.log('Tables created:', tablesResult.rows.map(r => r.table_name).join(', '));

        // Check indexes on task_node_results
        const indexesResult = await verifyClient.query(`
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'task_node_results'
            ORDER BY indexname
        `);
        console.log('Indexes on task_node_results:', indexesResult.rows.length);

        // Check triggers
        const triggersResult = await verifyClient.query(`
            SELECT tgname
            FROM pg_trigger
            WHERE tgname LIKE '%task%'
            OR tgname LIKE '%update%'
            OR tgname LIKE '%enforce%'
            ORDER BY tgname
        `);
        console.log('Triggers created:', triggersResult.rows.map(r => r.tgname).join(', '));

        // Check functions
        const functionsResult = await verifyClient.query(`
            SELECT proname
            FROM pg_proc
            WHERE proname LIKE '%task%'
            OR proname LIKE '%generate%'
            OR proname LIKE '%update%'
            ORDER BY proname
        `);
        console.log('Functions created:', functionsResult.rows.map(r => r.proname).join(', '));

        await verifyClient.end();

        console.log('\nMigration execution complete!');

    } catch (err) {
        console.error('Migration failed:', err.message);
        console.error(err.stack);
        process.exit(1);
    }
}

executeMigration();
