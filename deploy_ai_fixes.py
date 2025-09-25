#!/usr/bin/env python3
"""
Deployment script for TORQ Console AI Integration Fixes.

This script applies all necessary fixes to ensure the web interface
properly integrates with the AI backend components.
"""

import sys
import os
import shutil
from pathlib import Path
import re

def update_web_py_routes():
    """Update the web.py file to use enhanced AI routing."""
    web_py_path = Path("E:/TORQ-CONSOLE/torq_console/ui/web.py")

    if not web_py_path.exists():
        print("❌ web.py not found at expected location")
        return False

    print("🔧 Updating web.py routes...")

    # Read current content
    content = web_py_path.read_text(encoding='utf-8')

    # Backup original
    backup_path = web_py_path.with_suffix('.py.backup')
    if not backup_path.exists():
        web_py_path.copy(backup_path)
        print(f"📦 Created backup at {backup_path}")

    # Add import for AI fixes at the top after other imports
    import_section = '''
# CRITICAL FIX: Import enhanced AI integration fixes
try:
    from .web_ai_fix import WebUIAIFixes, apply_web_ai_fixes
    AI_FIXES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AI fixes not available: {e}")
    AI_FIXES_AVAILABLE = False
'''

    # Find the location to add imports (after existing imports)
    if "from .web_ai_fix import" not in content:
        # Add after the last import statement
        import_pattern = r'(from \..*import.*\n)'
        last_import_match = None
        for match in re.finditer(import_pattern, content):
            last_import_match = match

        if last_import_match:
            insert_pos = last_import_match.end()
            content = content[:insert_pos] + import_section + content[insert_pos:]
            print("✅ Added AI fixes import")

    # Update the direct_chat endpoint to use enhanced AI
    direct_chat_pattern = r'@self\.app\.post\("/api/chat"\)\s*async def direct_chat\(request: "DirectChatRequest"\):(.*?)(?=@self\.app\.|def _setup_chat_routes|$)'

    new_direct_chat = '''@self.app.post("/api/chat")
        async def direct_chat(request: "DirectChatRequest"):
            """
            ENHANCED: Direct chat endpoint with proper AI routing.
            Routes all queries through the enhanced AI integration system.
            """
            try:
                self.logger.info(f"Direct chat request: {request.message}")

                # Use enhanced AI routing if available
                if AI_FIXES_AVAILABLE:
                    return await WebUIAIFixes.direct_chat_fixed(self, request)

                # Fallback to enhanced AI integration
                response_content = await self._generate_ai_response(request.message, None)

                return {
                    "success": True,
                    "response": response_content,
                    "agent": "TORQ Console AI",
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                self.logger.error(f"Direct chat error: {e}")
                return {
                    "success": False,
                    "error": f"Error processing your request: {str(e)}",
                    "response": f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again."
                }
'''

    if re.search(r'@self\.app\.post\("/api/chat"\)', content):
        content = re.sub(direct_chat_pattern, new_direct_chat, content, flags=re.DOTALL)
        print("✅ Updated direct_chat endpoint")

    # Add initialization hook in __init__ method
    init_pattern = r'(self\.templates = Jinja2Templates\(directory="torq_console/ui/templates"\))'

    init_addition = '''$1

        # CRITICAL FIX: Apply AI integration fixes
        if AI_FIXES_AVAILABLE:
            try:
                apply_web_ai_fixes(self)
                self.logger.info("Applied AI integration fixes successfully")
            except Exception as e:
                self.logger.error(f"Failed to apply AI fixes: {e}")'''

    if "apply_web_ai_fixes(self)" not in content:
        content = re.sub(init_pattern, init_addition, content)
        print("✅ Added AI fixes initialization")

    # Write updated content
    web_py_path.write_text(content, encoding='utf-8')
    print("✅ web.py updated successfully")
    return True

def verify_environment_variables():
    """Verify that required environment variables are set."""
    print("🔍 Checking environment variables...")

    required_vars = {
        'DEEPSEEK_API_KEY': 'DeepSeek AI API integration',
        'GOOGLE_SEARCH_API_KEY': 'Google Custom Search (optional)',
        'BRAVE_SEARCH_API_KEY': 'Brave Search API (optional)'
    }

    configured = 0
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Configured")
            configured += 1
        else:
            print(f"❌ {var}: Not set ({description})")

    if configured == 0:
        print("⚠️  Warning: No API keys configured. AI will run in basic mode.")
    elif configured < len(required_vars):
        print(f"⚠️  Warning: Only {configured}/{len(required_vars)} API keys configured.")
    else:
        print("✅ All API keys configured!")

    return configured > 0

def check_file_structure():
    """Check that all required files are in place."""
    print("📁 Checking file structure...")

    required_files = [
        "E:/TORQ-CONSOLE/torq_console/utils/ai_integration.py",
        "E:/TORQ-CONSOLE/torq_console/llm/providers/deepseek.py",
        "E:/TORQ-CONSOLE/torq_console/llm/providers/websearch.py",
        "E:/TORQ-CONSOLE/torq_console/llm/manager.py",
        "E:/TORQ-CONSOLE/torq_console/ui/web_ai_fix.py",
        "E:/TORQ-CONSOLE/torq_integration.py",
        "E:/TORQ-CONSOLE/.env"
    ]

    all_present = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {path.name}")
        else:
            print(f"❌ {path.name} - Missing")
            all_present = False

    return all_present

def update_env_file():
    """Ensure .env file has the DeepSeek API key."""
    env_path = Path("E:/TORQ-CONSOLE/.env")

    if not env_path.exists():
        print("❌ .env file not found")
        return False

    content = env_path.read_text()

    # Check if DeepSeek key is present
    if "DEEPSEEK_API_KEY=sk-1061efb8089744dcad1183fb2ef55960" in content:
        print("✅ DeepSeek API key already configured in .env")
        return True

    # Add DeepSeek key if not present
    if "DEEPSEEK_API_KEY=" not in content:
        content += "\nDEEPSEEK_API_KEY=sk-1061efb8089744dcad1183fb2ef55960\n"
        env_path.write_text(content)
        print("✅ Added DeepSeek API key to .env file")
        return True

    return True

def create_startup_script():
    """Create a startup script for testing the integration."""
    startup_script = '''#!/usr/bin/env python3
"""
TORQ Console Web Interface with Enhanced AI Integration

This script starts the TORQ Console web interface with all AI integration
fixes applied for real search and AI response capabilities.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def main():
    """Start the TORQ Console with enhanced AI integration."""
    print("🚀 Starting TORQ Console with Enhanced AI Integration")
    print("=" * 60)

    # Check API keys
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_key:
        print("✅ DeepSeek AI integration enabled")
    else:
        print("⚠️  DeepSeek API key not found - AI will run in basic mode")

    # Check search APIs
    google_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    brave_key = os.getenv('BRAVE_SEARCH_API_KEY')

    search_methods = []
    if google_key:
        search_methods.append("Google Custom Search")
    if brave_key:
        search_methods.append("Brave Search")

    if search_methods:
        print(f"✅ Web search enabled: {', '.join(search_methods)}")
    else:
        print("⚠️  No search API keys - using fallback search guidance")

    print("🌐 Starting web server at http://localhost:8080")
    print("📝 Test query: 'search web for ai news'")
    print("=" * 60)

    try:
        # Import and run TORQ Console
        from torq_console.main import main as torq_main
        await torq_main(web=True, port=8080)
    except ImportError:
        print("❌ Could not import TORQ Console. Please ensure it's properly installed.")
    except Exception as e:
        print(f"❌ Error starting TORQ Console: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 TORQ Console stopped by user")
    except Exception as e:
        print(f"\\n💥 Fatal error: {e}")
'''

    script_path = Path("E:/TORQ-CONSOLE/start_enhanced_torq.py")
    script_path.write_text(startup_script)
    print(f"✅ Created startup script: {script_path}")
    return True

def main():
    """Deploy all AI integration fixes."""
    print("🚀 TORQ Console AI Integration Deployment")
    print("=" * 50)

    steps = [
        ("File Structure Check", check_file_structure),
        ("Environment Variables", verify_environment_variables),
        ("Update .env File", update_env_file),
        ("Update Web Routes", update_web_py_routes),
        ("Create Startup Script", create_startup_script),
    ]

    all_success = True
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        try:
            success = step_func()
            if success:
                print(f"✅ {step_name} completed successfully")
            else:
                print(f"❌ {step_name} failed")
                all_success = False
        except Exception as e:
            print(f"❌ {step_name} failed with error: {e}")
            all_success = False

    print("\n" + "=" * 50)
    if all_success:
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("\n📋 Next Steps:")
        print("1. Run: python test_ai_integration.py")
        print("2. Start web server: python start_enhanced_torq.py")
        print("3. Test with: 'search web for ai news'")
        print("\n🌐 Web interface will be available at: http://localhost:8080")
    else:
        print("❌ DEPLOYMENT INCOMPLETE")
        print("Please fix the issues above and run again.")

    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())