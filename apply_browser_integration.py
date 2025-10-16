"""
Automated integration script for Browser Automation Tool into torq_prince_flowers.py
Run this script to automatically apply all necessary changes
"""

import sys
from pathlib import Path


def apply_integration():
    """Apply browser automation integration to torq_prince_flowers.py"""

    file_path = Path('torq_console/agents/torq_prince_flowers.py')

    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        return False

    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Backup original file
    backup_path = file_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Backup created: {backup_path}")

    modifications_made = []

    # STEP 1: Add import after N8N import
    import_marker = '# Import N8N Workflow Tool\ntry:\n    from .tools.n8n_workflow_tool import create_n8n_workflow_tool\n    N8N_WORKFLOW_AVAILABLE = True\nexcept ImportError:\n    N8N_WORKFLOW_AVAILABLE = False\n    logging.warning("N8N Workflow Tool not available")'

    browser_import = '''
# Import Browser Automation Tool
try:
    from .tools.browser_automation_tool import create_browser_automation_tool
    BROWSER_AUTOMATION_AVAILABLE = True
except ImportError:
    BROWSER_AUTOMATION_AVAILABLE = False
    logging.warning("Browser Automation Tool not available")'''

    if 'BROWSER_AUTOMATION_AVAILABLE' not in content:
        content = content.replace(import_marker, import_marker + browser_import)
        modifications_made.append("Added browser automation import")
        print("✓ Step 1: Import added")
    else:
        print("⊘ Step 1: Import already exists")

    # STEP 2: Add to available_tools dict
    n8n_tool_entry = '''            'n8n_workflow': {
                'name': 'N8N Workflow Automation',
                'description': 'Execute and manage n8n automation workflows',
                'cost': 0.2,
                'success_rate': 0.88,
                'avg_time': 1.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },'''

    browser_tool_entry = '''            'n8n_workflow': {
                'name': 'N8N Workflow Automation',
                'description': 'Execute and manage n8n automation workflows',
                'cost': 0.2,
                'success_rate': 0.88,
                'avg_time': 1.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },
            'browser_automation': {
                'name': 'Browser Automation',
                'description': 'Automate web browser interactions using Playwright',
                'cost': 0.4,
                'success_rate': 0.85,
                'avg_time': 2.5,
                'dependencies': [],
                'composable': True,
                'requires_approval': False
            },'''

    if "'browser_automation':" not in content:
        content = content.replace(n8n_tool_entry, browser_tool_entry)
        modifications_made.append("Added browser_automation to available_tools")
        print("✓ Step 2: Tool registry entry added")
    else:
        print("⊘ Step 2: Tool registry entry already exists")

    # STEP 3: Add browser intent signals
    intent_signals_marker = "            'image_generation': ['image', 'picture', 'photo', 'visual', 'draw', 'illustrate', 'artwork']"
    browser_intent = "            'image_generation': ['image', 'picture', 'photo', 'visual', 'draw', 'illustrate', 'artwork'],\n            'browser_automation': ['browse', 'click', 'screenshot', 'playwright', 'web scrape', 'automate', 'fill form']"

    if "'browser_automation': [" not in content:
        content = content.replace(intent_signals_marker, browser_intent)
        modifications_made.append("Added browser_automation intent signals")
        print("✓ Step 3: Intent signals added")
    else:
        print("⊘ Step 3: Intent signals already exist")

    # STEP 4: Add _execute_browser_automation method
    execute_method = """
    async def _execute_browser_automation(
        self,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        javascript: Optional[str] = None,
        path: Optional[str] = None,
        timeout_ms: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        \"\"\"
        Execute browser automation operations.

        Args:
            action: Operation to perform (navigate, click, fill, screenshot,
                    get_text, wait_for, evaluate)
            url: Target URL (required for navigate)
            selector: CSS selector (required for click, fill, get_text, wait_for)
            text: Text content (required for fill)
            javascript: JavaScript code (required for evaluate)
            path: File path (required for screenshot)
            timeout_ms: Operation timeout in milliseconds
            **kwargs: Additional parameters

        Returns:
            Dict with success status and operation results
        \"\"\"
        import time
        start_time = time.time()

        # Update tool performance
        self.tool_performance['browser_automation']['usage_count'] += 1

        if not BROWSER_AUTOMATION_AVAILABLE:
            error_msg = "Browser Automation Tool not available. Install Playwright: pip install playwright && playwright install"
            self.logger.error(f"[BROWSER] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'action': action,
                'execution_time': time.time() - start_time
            }

        try:
            self.logger.info(f"[BROWSER] Executing action: {action}")

            # Create browser automation tool
            browser_tool = create_browser_automation_tool()

            # Check availability
            if not browser_tool.is_available():
                error_msg = ("Browser Automation Tool not configured. Install Playwright with: "
                            "pip install playwright && playwright install")
                self.logger.warning(f"[BROWSER] {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'action': action,
                    'execution_time': time.time() - start_time
                }

            # Execute browser operation
            result = await browser_tool.execute(
                action=action,
                url=url,
                selector=selector,
                text=text,
                javascript=javascript,
                path=path,
                timeout_ms=timeout_ms,
                **kwargs
            )

            execution_time = time.time() - start_time
            result['execution_time'] = execution_time

            # Update success stats
            if result.get('success'):
                self.tool_performance['browser_automation']['success_count'] += 1
                self.tool_performance['browser_automation']['total_time'] += execution_time

                # Log success based on action type
                if action == 'navigate':
                    final_url = result.get('result', {}).get('final_url', 'N/A')
                    self.logger.info(f"[BROWSER] ✓ SUCCESS - Navigated to {final_url}")
                elif action == 'click':
                    self.logger.info(f"[BROWSER] ✓ SUCCESS - Clicked element {selector}")
                elif action == 'fill':
                    self.logger.info(f"[BROWSER] ✓ SUCCESS - Filled element {selector}")
                elif action == 'screenshot':
                    self.logger.info(f"[BROWSER] ✓ SUCCESS - Screenshot saved to {path}")
                elif action == 'get_text':
                    text_length = result.get('result', {}).get('length', 0)
                    self.logger.info(f"[BROWSER] ✓ SUCCESS - Extracted {text_length} chars from {selector}")
                elif action == 'wait_for':
                    self.logger.info(f"[BROWSER] ✓ SUCCESS - Element {selector} found")
                elif action == 'evaluate':
                    self.logger.info(f"[BROWSER] ✓ SUCCESS - JavaScript executed")
            else:
                self.logger.error(f"[BROWSER] ✗ FAILED: {result.get('error')}")

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Browser automation operation error: {str(e)}"
            self.logger.error(f"[BROWSER] ✗ ERROR: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'action': action,
                'execution_time': execution_time
            }
"""

    # Find insertion point (after _execute_n8n_workflow method)
    n8n_method_end = '                \'execution_time\': execution_time\n            }\n\n    async def _execute_content_analysis'

    if '_execute_browser_automation' not in content:
        content = content.replace(
            n8n_method_end,
            '                \'execution_time\': execution_time\n            }\n' + execute_method + '\n    async def _execute_content_analysis'
        )
        modifications_made.append("Added _execute_browser_automation method")
        print("✓ Step 4: Execute method added")
    else:
        print("⊘ Step 4: Execute method already exists")

    # Write modified content
    if modifications_made:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✓ Integration complete! Applied {len(modifications_made)} modifications:")
        for mod in modifications_made:
            print(f"  - {mod}")
        print(f"\nBackup saved to: {backup_path}")
        print(f"\nTo restore original file:")
        print(f"  mv {backup_path} {file_path}")
        return True
    else:
        print("\n⊘ No modifications needed - integration already complete")
        return True


if __name__ == '__main__':
    print("=" * 80)
    print("Browser Automation Tool - Integration Script")
    print("=" * 80)
    print()

    success = apply_integration()

    if success:
        print("\n" + "=" * 80)
        print("✓ Integration successful!")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Run verification: python -c \"from torq_console.agents.tools import BrowserAutomationTool; print('✅ Import OK')\"")
        print("2. Run tests: python test_prince_browser_automation.py")
        print("3. Try examples: python example_browser_automation_usage.py")
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("✗ Integration failed")
        print("=" * 80)
        sys.exit(1)
