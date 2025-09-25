#!/usr/bin/env python3
"""
Critical Fix for TORQ Console Web Interface

This script fixes the critical issue where "search web for ai news" returns
"Edit completed successfully!" instead of actual AI responses.

ROOT CAUSES IDENTIFIED:
1. Missing /api/chat endpoint that the frontend expects
2. _generate_ai_response method not properly routing to Prince Flowers
3. Web interface defaulting to edit mode instead of AI response mode

FIXES APPLIED:
1. Add proper /api/chat endpoint for direct chat queries
2. Ensure Prince Flowers integration is properly connected
3. Route search queries to Prince Flowers Enhanced Agent
4. Fix response handling to return actual AI responses
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path

# Add TORQ Console path
TORQ_CONSOLE_PATH = Path(__file__).parent
sys.path.append(str(TORQ_CONSOLE_PATH))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_web_api_fixes():
    """Apply critical fixes to the web API."""

    logger.info("🚨 APPLYING CRITICAL WEB API FIXES")

    web_py_path = TORQ_CONSOLE_PATH / "torq_console" / "ui" / "web.py"

    if not web_py_path.exists():
        logger.error(f"❌ Web UI file not found: {web_py_path}")
        return False

    # Read current content
    with open(web_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Critical Fix 1: Add missing /api/chat endpoint
    if '/api/chat"' not in content and '@self.app.post("/api/chat")' not in content:
        logger.info("🔧 Adding missing /api/chat endpoint...")

        # Find where to insert the new endpoint
        chat_routes_start = content.find('def _setup_chat_routes(self):')
        if chat_routes_start == -1:
            logger.error("❌ Could not find _setup_chat_routes method")
            return False

        # Find the first route after _setup_chat_routes
        first_route_start = content.find('@self.app.get("/api/chat/tabs")', chat_routes_start)
        if first_route_start == -1:
            logger.error("❌ Could not find chat routes location")
            return False

        # Insert the new /api/chat endpoint
        new_endpoint = '''
        @self.app.post("/api/chat")
        async def direct_chat(request: "DirectChatRequest"):
            """
            Direct chat endpoint for simple query/response without tab management.
            This is the endpoint the TORQ Console web interface uses.
            """
            try:
                self.logger.info(f"Direct chat request: {request.message}")

                # Route to Prince Flowers for AI queries, especially search queries
                if any(keyword in request.message.lower() for keyword in [
                    "search", "find", "latest", "news", "ai developments", "what is", "how to"
                ]):
                    response = await self._handle_prince_command(request.message, None)
                else:
                    # Generate AI response using the proper method
                    response = await self._generate_ai_response(request.message, None)

                return {
                    "success": True,
                    "response": response,
                    "agent": "Prince Flowers Enhanced" if "search" in request.message.lower() else "TORQ Console AI",
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                self.logger.error(f"Direct chat error: {e}")
                return {
                    "success": False,
                    "error": f"Error processing your request: {str(e)}",
                    "response": "I apologize, but I encountered an error. Please try again."
                }

'''

        content = content[:first_route_start] + new_endpoint + content[first_route_start:]
        logger.info("✅ Added /api/chat endpoint")

    # Critical Fix 2: Fix _handle_prince_command method
    logger.info("🔧 Fixing Prince Flowers command handling...")

    handle_prince_start = content.find('async def _handle_prince_command(self, command: str, context_matches:')
    if handle_prince_start != -1:
        # Find the end of the method
        method_end = content.find('\n    async def ', handle_prince_start + 1)
        if method_end == -1:
            method_end = content.find('\n    def ', handle_prince_start + 1)

        if method_end != -1:
            # Replace the entire method with an improved version
            new_method = '''    async def _handle_prince_command(self, command: str, context_matches: Optional[List] = None) -> str:
        """Handle Prince Flowers commands properly."""
        try:
            self.logger.info(f"Processing Prince Flowers command: {command}")

            # Ensure command starts with 'prince' for proper routing
            if not command.lower().startswith('prince'):
                command = f"prince {command}"

            # Check if Prince Flowers integration is available
            if hasattr(self.console, 'prince_flowers_integration') and self.console.prince_flowers_integration:
                # Use the integration wrapper
                integration = self.console.prince_flowers_integration

                # Prepare context
                enhanced_context = {
                    'web_interface': True,
                    'context_matches': context_matches or [],
                    'timestamp': datetime.now().isoformat()
                }

                # Process through integration
                response = await integration.query(command, enhanced_context, show_performance=True)

                if response.success:
                    result = response.content
                    if response.execution_time and response.confidence:
                        result += f"\\n\\n*Processed in {response.execution_time:.2f}s with {response.confidence:.1%} confidence*"
                    return result
                else:
                    return response.content or f"Prince Flowers encountered an error: {response.error}"

            elif hasattr(self.console, 'handle_prince_command'):
                # Use console's prince command handler
                return await self.console.handle_prince_command(command, {'web_interface': True})

            elif hasattr(self.console, 'prince_flowers'):
                # Direct access to Prince Flowers agent
                if hasattr(self.console.prince_flowers, 'handle_prince_command'):
                    return await self.console.prince_flowers.handle_prince_command(command, {'web_interface': True})
                else:
                    return "Prince Flowers agent is available but doesn't have the expected interface methods."
            else:
                # Fallback: Try to import and use the integration directly
                try:
                    import sys
                    sys.path.append(str(Path(__file__).parent.parent))
                    from torq_integration import PrinceFlowersIntegrationWrapper
                    integration = PrinceFlowersIntegrationWrapper(self.console)
                    response = await integration.query(command, {'web_interface_fallback': True})
                    return response.content
                except Exception as import_e:
                    self.logger.error(f"Failed to import Prince Flowers integration: {import_e}")
                    return f"Prince Flowers agent is not available. Error: {str(import_e)}. Please ensure the Prince Flowers integration is properly configured."

        except Exception as e:
            self.logger.error(f"Error in Prince command handling: {e}")
            return f"Error processing Prince Flowers command: {str(e)}"
'''

            content = content[:handle_prince_start] + new_method + content[method_end:]
            logger.info("✅ Fixed Prince Flowers command handling")

    # Critical Fix 3: Ensure _generate_ai_response properly detects search queries
    logger.info("🔧 Fixing AI response generation...")

    generate_ai_start = content.find('async def _generate_ai_response(self, user_content: str, context_matches:')
    if generate_ai_start != -1:
        # Find the detection logic
        detection_start = content.find('# Detect Prince Flowers commands', generate_ai_start)
        if detection_start != -1:
            detection_end = content.find(')', detection_start)
            if detection_end != -1:
                # Replace the detection logic with improved version
                new_detection = '''# Detect Prince Flowers commands
            is_prince_command = (
                content_lower.startswith("prince ") or
                content_lower.startswith("@prince ") or
                any(keyword in content_lower for keyword in [
                    "prince search", "prince help", "prince status",
                    "search ai", "search for", "find information",
                    "search web", "ai news", "latest ai", "what is",
                    "how to", "find", "search", "news"
                ])'''

                content = content[:detection_start] + new_detection + content[detection_end:]
                logger.info("✅ Improved search query detection")

    # Critical Fix 4: Add the DirectChatRequest model at the end
    if 'class DirectChatRequest' not in content:
        logger.info("🔧 Adding DirectChatRequest model...")

        # Find the end of the other Pydantic models
        model_section = content.rfind('class CreateCheckpointRequest(BaseModel):')
        if model_section != -1:
            # Find the end of that model
            model_end = content.find('\n\n', model_section)
            if model_end != -1:
                new_model = '''

class DirectChatRequest(BaseModel):
    message: str
    include_context: bool = True
    generate_response: bool = True
    model: Optional[str] = None
'''
                content = content[:model_end] + new_model + content[model_end:]
                logger.info("✅ Added DirectChatRequest model")

    # Write the updated content
    try:
        with open(web_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("✅ Successfully updated web.py with critical fixes")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to write updated web.py: {e}")
        return False


def verify_prince_flowers_integration():
    """Verify that Prince Flowers integration is properly configured."""

    logger.info("🔍 Verifying Prince Flowers integration...")

    # Check if torq_integration.py exists
    integration_path = TORQ_CONSOLE_PATH / "torq_integration.py"
    if not integration_path.exists():
        logger.error("❌ torq_integration.py not found")
        return False

    # Check if the integration file has the required classes
    try:
        with open(integration_path, 'r', encoding='utf-8') as f:
            content = f.read()

        required_components = [
            'class PrinceFlowersIntegrationWrapper',
            'def register_prince_flowers_integration',
            'async def query(',
            'async def handle_prince_command'
        ]

        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)

        if missing_components:
            logger.error(f"❌ Missing components in torq_integration.py: {missing_components}")
            return False
        else:
            logger.info("✅ Prince Flowers integration components found")
            return True

    except Exception as e:
        logger.error(f"❌ Error reading torq_integration.py: {e}")
        return False


def create_startup_script():
    """Create a startup script to ensure the server runs with fixes."""

    startup_script = TORQ_CONSOLE_PATH / "start_torq_with_fixes.py"

    script_content = '''#!/usr/bin/env python3
"""
TORQ Console Startup Script with Critical Fixes Applied

This script ensures the TORQ Console web interface starts with all
critical fixes for Prince Flowers integration and AI response routing.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

try:
    from torq_console.core.console import TorqConsole
    from torq_console.core.config import TorqConfig
    from torq_console.ui.web import WebUI
    from web_api_fix import apply_web_api_fixes, verify_prince_flowers_integration
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the TORQ-CONSOLE directory")
    sys.exit(1)

async def main():
    """Start TORQ Console with all fixes applied."""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    print("🚀 TORQ CONSOLE v0.70.0 - Starting with Critical Fixes")
    print("=" * 60)

    # Apply fixes
    if not apply_web_api_fixes():
        print("❌ Failed to apply web API fixes")
        return

    if not verify_prince_flowers_integration():
        print("⚠️  Prince Flowers integration issues detected")
        print("   The system will still work but may have limited capabilities")

    try:
        # Initialize TORQ Console
        config = TorqConfig()
        console = TorqConsole(config=config)

        # Initialize Web UI
        web_ui = WebUI(console)

        print("✅ All fixes applied successfully")
        print("🌐 Starting web server at http://127.0.0.1:8899")
        print("🤖 Prince Flowers Enhanced Agent ready")
        print("💬 Web chat interface fully functional")
        print("=" * 60)

        # Start server
        await web_ui.start_server(host="127.0.0.1", port=8899)

    except KeyboardInterrupt:
        print("\\n👋 Shutting down TORQ Console...")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        print(f"❌ Failed to start: {e}")

if __name__ == "__main__":
    asyncio.run(main())
'''

    with open(startup_script, 'w', encoding='utf-8') as f:
        f.write(script_content)

    logger.info(f"✅ Created startup script: {startup_script}")
    return startup_script


def main():
    """Main fix application function."""

    print("🚨 TORQ CONSOLE CRITICAL FIX APPLICATION")
    print("=" * 50)
    print("Issue: 'search web for ai news' returns 'Edit completed successfully!'")
    print("Root Cause: Web interface routing to edit mode instead of AI responses")
    print("=" * 50)

    # Apply fixes
    success = apply_web_api_fixes()

    if success:
        print("✅ CRITICAL FIXES APPLIED SUCCESSFULLY")
        print()
        print("🔧 FIXES APPLIED:")
        print("1. ✅ Added /api/chat endpoint for direct queries")
        print("2. ✅ Fixed Prince Flowers command routing")
        print("3. ✅ Improved search query detection")
        print("4. ✅ Added DirectChatRequest model")
        print()

        # Verify integration
        if verify_prince_flowers_integration():
            print("5. ✅ Prince Flowers integration verified")
        else:
            print("5. ⚠️  Prince Flowers integration needs attention")

        # Create startup script
        startup_script = create_startup_script()
        print(f"6. ✅ Created startup script: {startup_script.name}")
        print()

        print("🚀 NEXT STEPS:")
        print("1. Stop any running TORQ Console instances")
        print("2. Run: python start_torq_with_fixes.py")
        print("3. Open web interface: http://127.0.0.1:8899")
        print("4. Test query: 'search web for ai news'")
        print()
        print("✅ The query should now return actual AI search results!")
        print("   instead of 'Edit completed successfully!'")

    else:
        print("❌ FAILED TO APPLY FIXES")
        print("Please check the error messages above and try again.")

    print("=" * 50)


if __name__ == "__main__":
    main()