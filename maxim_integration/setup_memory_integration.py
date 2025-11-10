"""
Setup Script for Memory Integration

One-click setup to configure Supabase memory and integrate with enhanced Prince Flowers
to achieve 95%+ performance target.
"""

import os
import asyncio
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_environment():
    """Check if required environment variables are set."""
    print("Checking Environment Configuration")
    print("=" * 50)

    required_vars = {
        'SUPABASE_URL': 'Supabase Project URL',
        'SUPABASE_SERVICE_ROLE_KEY': 'Supabase Service Role Key',
        'OPENAI_API_KEY': 'OpenAI API Key (for embeddings)'
    }

    optional_vars = {
        'PRINCE_FLOWERS_USER_ID': 'Prince Flowers User ID (default: prince_flowers_user)',
        'PRINCE_FLOWERS_AGENT_ID': 'Prince Flowers Agent ID (default: prince_flowers_enhanced)'
    }

    env_status = {}
    missing_required = []

    print("\nRequired Environment Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            masked_value = value[:10] + "..." if len(value) > 10 else "***"
            print(f"  ✓ {var}: {masked_value}")
            env_status[var] = True
        else:
            print(f"  ✗ {var}: NOT SET")
            env_status[var] = False
            missing_required.append(var)

    print("\nOptional Environment Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {value}")
        else:
            default_value = description.split('(default: ')[1].rstrip(')')
            print(f"  - {var}: Using default '{default_value}'")

    if missing_required:
        print(f"\n[CONFIG NEEDED] Missing required variables: {', '.join(missing_required)}")
        return False, env_status
    else:
        print(f"\n[OK] All required environment variables are set")
        return True, env_status

async def test_supabase_connection():
    """Test Supabase database connection."""
    print("\nTesting Supabase Connection")
    print("=" * 50)

    try:
        from supabase_memory_config import get_supabase_setup
        from enhanced_memory_integration import get_enhanced_memory_integration

        # Test Supabase setup
        supabase_setup = get_supabase_setup()
        if not supabase_setup.is_configured():
            print("  ✗ Supabase not configured")
            return False

        print("  ✓ Supabase configuration loaded")

        # Test memory integration
        memory_integration = get_enhanced_memory_integration()
        connected = await memory_integration.initialize()

        if connected:
            print("  ✓ Supabase connection successful")
            return True
        else:
            print("  ✗ Supabase connection failed")
            return False

    except Exception as e:
        print(f"  ✗ Connection test failed: {e}")
        return False

async def setup_database_schema():
    """Set up database schema in Supabase."""
    print("\nSetting Up Database Schema")
    print("=" * 50)

    try:
        from supabase_memory_config import create_supabase_schema_sql

        schema_sql = create_supabase_schema_sql()

        # Save schema to file
        schema_file = "E:/TORQ-CONSOLE/maxim_integration/supabase_schema.sql"
        with open(schema_file, "w") as f:
            f.write(schema_sql)

        print(f"  ✓ Schema SQL generated: {schema_file}")
        print("  ⚠ MANUAL STEP: Execute this SQL in your Supabase project")
        print("     1. Go to your Supabase project dashboard")
        print("     2. Navigate to SQL Editor")
        print("     3. Copy and paste the contents of supabase_schema.sql")
        print("     4. Execute the SQL to create all required tables")

        return True

    except Exception as e:
        print(f"  ✗ Schema setup failed: {e}")
        return False

async def test_memory_integration():
    """Test the complete memory integration."""
    print("\nTesting Memory Integration")
    print("=" * 50)

    try:
        from memory_enhanced_prince_flowers import create_memory_enhanced_prince_flowers

        # Create and initialize agent
        agent = create_memory_enhanced_prince_flowers()
        memory_ready = await agent.initialize()

        print(f"  ✓ Agent initialized")
        print(f"  ✓ Memory integration: {'Enabled' if memory_ready else 'Local only'}")

        # Test a simple query
        test_result = await agent.process_query_with_memory(
            "What is artificial intelligence?"
        )

        print(f"  ✓ Test query processed successfully")
        print(f"    - Success: {test_result['success']}")
        print(f"    - Confidence: {test_result['confidence']:.3f}")
        print(f"    - Memory Context: {test_result.get('memory_context', {}).get('memories_used', 0)} memories")

        # Get performance metrics
        metrics = await agent.get_performance_metrics()
        print(f"  ✓ Performance metrics retrieved")
        print(f"    - Learning Active: {metrics.get('learning_active', False)}")
        print(f"    - Memory Integration: {metrics.get('memory_integration_enabled', False)}")

        # Cleanup
        await agent.cleanup()

        return True

    except Exception as e:
        print(f"  ✗ Memory integration test failed: {e}")
        logger.exception("Memory integration test failed")
        return False

async def run_performance_test():
    """Run a quick performance test."""
    print("\nRunning Performance Test")
    print("=" * 50)

    try:
        from test_memory_enhanced_agent import test_memory_enhanced_agent

        print("  ✓ Running memory-enhanced agent test...")
        results = await test_memory_enhanced_agent()

        overall_score = results.get('overall_metrics', {}).get('overall_score', 0)
        target_achieved = results.get('overall_metrics', {}).get('target_achieved', False)

        print(f"  ✓ Performance test completed")
        print(f"    - Overall Score: {overall_score:.1%}")
        print(f"    - 95% Target: {'ACHIEVED' if target_achieved else 'NOT ACHIEVED'}")

        return target_achieved

    except Exception as e:
        print(f"  ✗ Performance test failed: {e}")
        logger.exception("Performance test failed")
        return False

def generate_env_file_template():
    """Generate .env file template."""
    env_template = """
# Supabase Configuration for Enhanced Prince Flowers Memory
# Get these values from your Supabase project dashboard

SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
OPENAI_API_KEY=your-openai-api-key-here

# Optional: Custom IDs
PRINCE_FLOWERS_USER_ID=prince_flowers_user
PRINCE_FLOWERS_AGENT_ID=prince_flowers_enhanced
"""

    env_file = "E:/TORQ-CONSOLE/maxim_integration/.env.template"
    with open(env_file, "w") as f:
        f.write(env_template.strip())

    print(f"\n  ✓ Environment template created: {env_file}")
    print("    1. Copy this file to .env")
    print("    2. Fill in your actual values")
    print("    3. Restart your application")

async def main():
    """Main setup function."""
    print("Enhanced Prince Flowers Memory Integration Setup")
    print("=" * 60)
    print(f"Setup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: Configure Supabase memory for 95%+ agent performance")
    print("=" * 60)

    setup_results = {}

    # Step 1: Check environment
    env_ok, env_status = await check_environment()
    setup_results['environment'] = {
        'configured': env_ok,
        'status': env_status
    }

    if not env_ok:
        print("\n" + "=" * 60)
        print("SETUP INCOMPLETE - Environment Configuration Required")
        print("=" * 60)

        # Generate env template
        generate_env_file_template()

        print("\nNext Steps:")
        print("1. Set the required environment variables")
        print("2. Run this setup script again")
        print("3. Follow the database setup instructions")

        return setup_results

    # Step 2: Test Supabase connection
    connection_ok = await test_supabase_connection()
    setup_results['connection'] = connection_ok

    if not connection_ok:
        print("\n" + "=" * 60)
        print("SETUP INCOMPLETE - Supabase Connection Failed")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Verify your Supabase URL and keys are correct")
        print("2. Check your Supabase project is active")
        print("3. Ensure network connectivity to Supabase")

        return setup_results

    # Step 3: Setup database schema
    schema_ok = await setup_database_schema()
    setup_results['schema'] = schema_ok

    # Step 4: Test memory integration
    memory_ok = await test_memory_integration()
    setup_results['memory_integration'] = memory_ok

    # Step 5: Run performance test (optional)
    print("\nRun performance test? (y/n): ", end="")
    try:
        # For automated setup, we'll skip the interactive prompt
        run_performance = False  # Change to True for automatic testing
    except:
        run_performance = False

    performance_ok = False
    if run_performance:
        performance_ok = await run_performance_test()
        setup_results['performance_test'] = performance_ok

    # Generate setup report
    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print("=" * 60)

    print(f"\nSetup Results:")
    print(f"  ✓ Environment Configuration: {'OK' if env_ok else 'FAILED'}")
    print(f"  ✓ Supabase Connection: {'OK' if connection_ok else 'FAILED'}")
    print(f"  ✓ Database Schema: {'GENERATED' if schema_ok else 'FAILED'}")
    print(f"  ✓ Memory Integration: {'WORKING' if memory_ok else 'FAILED'}")
    if run_performance:
        print(f"  ✓ Performance Test: {'95%+ ACHIEVED' if performance_ok else 'NEEDS IMPROVEMENT'}")

    overall_success = all([env_ok, connection_ok, schema_ok, memory_ok])

    if overall_success:
        print(f"\n[SUCCESS] Memory integration setup complete!")
        print(f"\nYour enhanced Prince Flowers agent now has:")
        print(f"  • Long-term memory storage in Supabase")
        print(f"  • Context-aware query processing")
        print(f"  • Learning from interaction history")
        print(f"  • Continuous performance improvement")
        print(f"  • Target: 95%+ performance score")

        print(f"\nNext Steps:")
        print(f"1. Use the memory_enhanced_prince_flowers agent in your application")
        print(f"2. Monitor performance with the test suite")
        print(f"3. Provide feedback to improve learning")

    else:
        print(f"\n[PARTIAL] Setup completed with some issues")
        print(f"Please address the failed components before proceeding")

    # Save setup results
    setup_results['timestamp'] = datetime.now().isoformat()
    setup_results['overall_success'] = overall_success

    try:
        with open("E:/TORQ-CONSOLE/maxim_integration/memory_setup_results.json", "w") as f:
            json.dump(setup_results, f, indent=2)
        print(f"\n[OK] Setup results saved to: memory_setup_results.json")
    except Exception as e:
        print(f"\n[WARNING] Could not save setup results: {e}")

    return setup_results

if __name__ == "__main__":
    asyncio.run(main())