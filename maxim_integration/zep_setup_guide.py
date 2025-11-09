"""
Zep Memory System Setup Guide

Step-by-step guide to set up Zep for advanced temporal memory with the
enhanced Prince Flowers agent to achieve 95%+ performance.
"""

import os
import asyncio
import logging
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ZepSetupGuide:
    """Comprehensive Zep setup guide for Prince Flowers agent."""

    def __init__(self):
        self.logger = logging.getLogger("ZepSetup")
        self.python_executable = sys.executable
        self.zep_docker_image = "zepai/zep:latest"
        self.zep_port = 8001
        self.zep_url = "http://localhost:8001"

    def check_python_requirements(self) -> bool:
        """Check if required Python packages are available."""
        print("Checking Python Requirements")
        print("=" * 50)

        required_packages = [
            'asyncio',
            'aiohttp',
            'typing',
            'dataclasses',
            'enum',
            'uuid',
            'datetime',
            'logging'
        ]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(f"  [OK] {package}")
            except ImportError:
                print(f"  [MISSING] {package} - MISSING")
                missing_packages.append(package)

        if missing_packages:
            print(f"\n[ERROR] Missing required packages: {', '.join(missing_packages)}")
            print("Please install the missing packages using pip")
            return False

        print("\n[OK] All Python requirements satisfied")
        return True

    def check_docker_availability(self) -> bool:
        """Check if Docker is available and running."""
        print("\nChecking Docker Availability")
        print("=" * 50)

        try:
            # Check if Docker is installed
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  [OK] Docker installed: {result.stdout.strip()}")
                return True
            else:
                print("  [ERROR] Docker not found")
                return False
        except FileNotFoundError:
            print("  [ERROR] Docker command not found")
            return False

    def check_docker_running(self) -> bool:
        """Check if Docker daemon is running."""
        try:
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def setup_zep_with_docker(self) -> bool:
        """Set up Zep using Docker."""
        print("\nSetting up Zep with Docker")
        print("=" * 50)

        try:
            # Check if Zep container is already running
            print("  Checking for existing Zep container...")
            check_result = subprocess.run(
                ['docker', 'ps', '-f', 'name=zep'],
                capture_output=True, text=True
            )

            if 'zep' in check_result.stdout:
                print("  [OK] Zep container already running")
                return True

            # Pull Zep Docker image
            print("  Pulling Zep Docker image...")
            pull_result = subprocess.run(
                ['docker', 'pull', self.zep_docker_image],
                capture_output=True, text=True
            )

            if pull_result.returncode != 0:
                print(f"  [ERROR] Failed to pull Zep image: {pull_result.stderr}")
                return False

            print("  [OK] Zep Docker image pulled successfully")

            # Run Zep container
            print("  Starting Zep container...")
            run_result = subprocess.run([
                'docker', 'run', '-d',
                '--name', 'zep',
                '-p', f'{self.zep_port}:{self.zep_port}',
                '--env', 'ZEP_API_KEY=no-key-required',
                '--env', 'POSTGRES_DBNAME=zep',
                '--env', 'POSTGRES_USER=zep',
                '--env', 'POSTGRES_PASSWORD=zep',
                '--env', 'POSTGRES_HOST=postgres',
                self.zep_docker_image
            ], capture_output=True, text=True)

            if run_result.returncode != 0:
                print(f"  [ERROR] Failed to start Zep container: {run_result.stderr}")
                return False

            print("  [OK] Zep container started successfully")
            return True

        except Exception as e:
            print(f"  [ERROR] Docker setup failed: {e}")
            return False

    async def test_zep_connection(self) -> bool:
        """Test Zep connection and functionality."""
        print("\nTesting Zep Connection")
        print("=" * 50)

        try:
            # Import our Zep integration
            from zep_memory_integration import create_zep_memory_integration

            # Create Zep memory integration
            zep_memory = create_zep_memory_integration(
                zep_api_url=self.zep_url,
                zep_api_key=None  # Zep is open-source
            )

            # Initialize Zep
            initialized = await zep_memory.initialize()

            if initialized:
                print("  [OK] Zep connection established")

                # Test basic operations
                session_id = await zep_memory.create_session(
                    metadata={"test": True, "setup": True}
                )
                print(f"  [OK] Created test session: {session_id}")

                # Add test message
                message_id = await zep_memory.add_message(
                    session_id=session_id,
                    role="user",
                    content="Test message for Zep integration",
                    metadata={"test": True}
                )
                print(f"  [OK] Added test message: {message_id}")

                # Test search
                search_results = await zep_memory.search_memory("test", limit=5)
                print(f"  [OK] Memory search works: {len(search_results)} results")

                # Get statistics
                stats = await zep_memory.get_memory_statistics()
                print(f"  [OK] Memory statistics: {stats.get('total_sessions', 0)} sessions")

                return True
            else:
                print("  [ERROR] Zep initialization failed")
                return False

        except Exception as e:
            print(f"  [ERROR] Zep connection test failed: {e}")
            return False

    def create_environment_file(self):
        """Create environment configuration file."""
        print("\nCreating Environment Configuration")
        print("=" * 50)

        env_content = """
# Zep Memory Configuration for Prince Flowers Agent
# No API key required - Zep is open-source

# Zep Configuration
ZEP_API_URL=http://localhost:8001
ZEP_API_KEY=no-key-required

# Agent Configuration
PRINCE_FLOWERS_AGENT_ID=prince_flowers_zep_enhanced
PRINCE_FLOWERS_USER_ID=king_flowers

# Session Configuration
DEFAULT_SESSION_ID=prince_flowers_default_session

# Memory Configuration
MAX_MESSAGES_PER_SESSION=1000
SESSION_TIMEOUT_HOURS=24
CONSOLIDATION_THRESHOLD=50

# Logging
LOG_LEVEL=INFO
        """.strip()

        env_file = "E:/TORQ-CONSOLE/maxim_integration/.env.zep"
        with open(env_file, "w") as f:
            f.write(env_content)

        print(f"  [OK] Environment file created: {env_file}")
        print("  [OK] Update your main .env file with these values or use .env.zep")

        return env_file

    def create_python_requirements(self):
        """Create Python requirements file."""
        print("\nCreating Python Requirements")
        print("=" * 50)

        requirements = """
# Zep Memory System Requirements
# Core requirements (should already be available)
aiohttp>=3.8.0
typing>=3.8.0
dataclasses>=0.6; python_version<"3.10"

# Maxim AI Tools Integration (existing)
# - Already integrated in the project

# Development and Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
python-dotenv>=0.19.0

# Optional: Vector database for enhanced search
# chromadb>=0.4.0
# weaviate-client>=3.0.0
        """.strip()

        req_file = "E:/TORQ-CONSOLE/maxim_integration/requirements_zep.txt"
        with open(req_file, "w") as f:
            f.write(requirements)

        print(f"  [OK] Requirements file created: {req_file}")
        print("  [OK] Install with: pip install -r requirements_zep.txt")

        return req_file

    def create_usage_examples(self):
        """Create usage examples for Zep integration."""
        print("\nCreating Usage Examples")
        print("=" * 50)

        example_code = '''
"""
# Example: Using Zep-Enhanced Prince Flowers Agent

import asyncio
from zep_enhanced_prince_flowers import create_zep_enhanced_prince_flowers

async def main():
    # Create Zep-enhanced agent
    agent = create_zep_enhanced_prince_flowers()

    # Initialize the agent
    initialized = await agent.initialize()
    if not initialized:
        print("Failed to initialize agent")
        return

    print("Zep-enhanced Prince Flowers agent ready!")

    # Process queries with memory
    queries = [
        "What is artificial intelligence?",
        "Generate a Python function for data analysis",
        "Explain machine learning concepts",
        "What is artificial intelligence?"  # Repeat to test memory
    ]

    for query in queries:
        print(f"\\nQuery: {query}")

        result = await agent.process_query_with_zep_memory(query)

        print(f"Success: {result['success']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Memory Used: {result['zep_memory']['memories_used']}")
        print(f"Context Available: {result['zep_memory']['context_available']}")
        print(f"Response: {result['content'][:200]}...")

        # Learn from feedback (simulate user feedback)
        if result['success']:
            await agent.learn_from_feedback(
                interaction_id=result['interaction_id'],
                feedback_score=0.9,
                feedback_text="Great response!",
                session_id=result['session_id']
            )

    # Get performance metrics
    metrics = await agent.get_performance_metrics()
    print(f"\\nPerformance Metrics:")
    print(f"  Total Interactions: {metrics['session_metrics']['total_interactions']}")
    print(f"  Success Rate: {metrics['session_metrics']['session_success_rate']:.1%}")
    print(f"  Memory Enhancement Rate: {metrics['memory_enhancement_rate']:.1%}")
    print(f"  Zep Memory Stats: {metrics['zep_memory_stats']['total_sessions']} sessions")

    # Cleanup
    await agent.cleanup()
    print("\\nAgent cleaned up successfully")

if __name__ == "__main__":
    asyncio.run(main())
        '''.strip()

        example_file = "E:/TORQ-CONSOLE/maxim_integration/zep_example_usage.py"
        with open(example_file, "w") as f:
            f.write(example_code)

        print(f"  [OK] Usage example created: {example_file}")
        print("  [OK] Run with: python zep_example_usage.py")

        return example_file

    async def run_full_setup(self) -> Dict[str, Any]:
        """Run the complete Zep setup process."""
        print("Zep Memory System Setup for Prince Flowers Agent")
        print("=" * 60)
        print(f"Setup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        setup_results = {}

        # Step 1: Check requirements
        print("STEP 1: Checking System Requirements")
        print("-" * 40)

        python_ok = self.check_python_requirements()
        setup_results['python_requirements'] = python_ok

        if not python_ok:
            return setup_results

        # Step 2: Check Docker
        print("\nSTEP 2: Checking Docker")
        print("-" * 40)

        docker_installed = self.check_docker_availability()
        setup_results['docker_installed'] = docker_installed

        if not docker_installed:
            print("\nDocker Installation Required:")
            print("1. Download Docker Desktop from https://www.docker.com/products/docker-desktop/")
            print("2. Install Docker Desktop")
            print("3. Restart your computer")
            print("4. Run this setup script again")
            return setup_results

        docker_running = self.check_docker_running()
        if not docker_running:
            print("\n[WARNING] Docker Desktop is installed but not running")
            print("Please start Docker Desktop and run this script again")
            return setup_results

        setup_results['docker_running'] = True

        # Step 3: Setup Zep
        print("\nSTEP 3: Setting Up Zep Memory System")
        print("-" * 40)

        zep_setup = self.setup_zep_with_docker()
        setup_results['zep_setup'] = zep_setup

        if not zep_setup:
            return setup_results

        # Step 4: Test Zep connection
        print("\nSTEP 4: Testing Zep Connection")
        print("-" * 40)

        zep_connection = await self.test_zep_connection()
        setup_results['zep_connection'] = zep_connection

        if not zep_connection:
            return setup_results

        # Step 5: Create configuration files
        print("\nSTEP 5: Creating Configuration Files")
        print("-" * 40)

        env_file = self.create_environment_file()
        setup_results['environment_file'] = env_file

        req_file = self.create_python_requirements()
        setup_results['requirements_file'] = req_file

        example_file = self.create_usage_examples()
        setup_results['example_file'] = example_file

        # Generate final report
        print("\n" + "=" * 60)
        print("ZEP SETUP COMPLETE")
        print("=" * 60)

        print(f"\nSetup Results:")
        print(f"  [OK] Python Requirements: {'OK' if python_ok else 'FAILED'}")
        print(f"  [OK] Docker Installed: {'OK' if docker_installed else 'FAILED'}")
        print(f"  [OK] Docker Running: {'OK' if docker_running else 'FAILED'}")
        print(f"  [OK] Zep Setup: {'OK' if zep_setup else 'FAILED'}")
        print(f"  [OK] Zep Connection: {'OK' if zep_connection else 'FAILED'}")
        print(f"  [OK] Configuration Files: {'CREATED'}")

        overall_success = all([
            python_ok,
            docker_installed,
            docker_running,
            zep_setup,
            zep_connection
        ])

        if overall_success:
            print(f"\n[SUCCESS] Zep memory system is ready!")
            print(f"\nYour Prince Flowers agent now has:")
            print(f"  - Advanced temporal memory with dynamic knowledge graphs")
            print(f"  - Session-based memory management")
            print(f"  - Semantic search and context retrieval")
            print(f"  - Memory consolidation and learning")
            print(f"  - Multi-session continuity")
            print(f"  - Target: 95%+ performance achievement")

            print(f"\nNext Steps:")
            print(f"1. Test with the provided example: python zep_example_usage.py")
            print(f"2. Integrate Zep into your existing agent workflows")
            print(f"3. Monitor performance improvements toward 95%+ target")
            print(f"4. Explore Zep's advanced features (knowledge graphs, etc.)")

        else:
            print(f"\n[PARTIAL] Setup completed with issues")
            print(f"Please address the failed components before proceeding")

        # Save setup results
        setup_results['timestamp'] = datetime.now().isoformat()
        setup_results['overall_success'] = overall_success

        try:
            import json
            with open("E:/TORQ-CONSOLE/maxim_integration/zep_setup_results.json", "w") as f:
                json.dump(setup_results, f, indent=2)
            print(f"\n[OK] Setup results saved to: zep_setup_results.json")
        except Exception as e:
            print(f"\n[WARNING] Could not save setup results: {e}")

        return setup_results

def main():
    """Run the Zep setup guide."""
    setup_guide = ZepSetupGuide()
    asyncio.run(setup_guide.run_full_setup())

if __name__ == "__main__":
    main()