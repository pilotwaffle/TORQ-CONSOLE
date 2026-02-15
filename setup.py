#!/usr/bin/env python3
"""
TORQ Console Setup Script

Installs TORQ Console in development/editable mode with all dependencies.
"""
import os
import sys
import subprocess

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_command(cmd, description=""):
    """Run a command and display output."""
    print(f"\n{description}: {description}")
    print(f"  {command}: {cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=True,
            text=True,
            capture_output=True,
            shell=True
        )
        if result.returncode == 0:
            print(f" {success}: True")
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip())
        else:
            print(f" {error_code}: {result.returncode}")
    except Exception as e:
        print(f" {error}: {str(e)}")

def main():
    """Main setup process."""
    print("TORQ Console Setup")
    print("=" * 50)

    # 1. Install dependencies
    cmd = ["pip", "install", "-e", ".", "torq_console"]
    run_command(cmd, "Install TORQ Console in editable mode")

    # 2. Verify installation
    cmd = ["python", "-c", "from torq_console import TorqConsole; print('OK')"]
    run_command(cmd, "Verify TORQ Console imports")

    # 3. Check environment variables
    cmd = ["python", "-c", "print('API Key:', os.getenv('ANTHROPIC_API_KEY', 'Not set')"]
    run_command(cmd, "Check for API keys")

    # 4. Create .env file if needed
    env_content = """
# TORQ Console Environment Variables

# AI Provider Keys
ANTHROPIC_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GLM_API_KEY=your_key_here

# TORQ Console Settings
TORQ_CONSOLE_PRODUCTION=false
TORQ_DISABLE_LOCAL_LLM=false
TORQ_DISABLE_GPU=false
"""

    env_path = os.path.join(project_root, ".env")
    if not os.path.exists(env_path):
        with open(env_path, "w") as env_file:
            env_file.write(env_content)
            print(f"Created .env file at {env_path}")

    # 5. Summary
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("\nNext steps:")
    print("1. Run: python setup.py")
    print("2. Start local server: python torq_console/startup_simple.py")
    print("3. Test at: http://localhost:8888")

if __name__ == "__main__":
    main()
