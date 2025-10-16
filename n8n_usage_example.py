"""
N8N Workflow Tool - Complete Usage Example
Demonstrates all operations supported by the N8N Workflow Tool
"""

import asyncio
import os
from torq_console.agents.tools import create_n8n_workflow_tool


async def main():
    """Main demonstration function."""

    print("=" * 60)
    print("N8N Workflow Tool - Usage Examples")
    print("=" * 60)

    # ================================================================
    # Example 1: Direct API Mode with Explicit Credentials
    # ================================================================
    print("\n### Example 1: Create tool with explicit credentials ###\n")

    tool = create_n8n_workflow_tool(
        api_url='https://n8n.example.com/api/v1',
        api_key='your_api_key_here'
    )

    print(f"Tool Name: {tool.name}")
    print(f"Tool Description: {tool.description}")
    print(f"Tool Available: {tool.is_available()}")
    print(f"Access Mode: {tool.get_tool_info()['access_mode']}")

    # ================================================================
    # Example 2: Environment Variable Mode (Recommended)
    # ================================================================
    print("\n### Example 2: Create tool using environment variables ###\n")

    # Set environment variables (normally done in shell or .env file)
    os.environ['N8N_API_URL'] = 'https://n8n.example.com/api/v1'
    os.environ['N8N_API_KEY'] = 'your_api_key_here'

    tool = create_n8n_workflow_tool()

    print(f"Tool configured from environment: {tool.is_available()}")

    # ================================================================
    # Example 3: List All Workflows
    # ================================================================
    print("\n### Example 3: List all workflows ###\n")

    result = await tool.execute(action='list_workflows')

    if result['success']:
        workflows = result['result']['workflows']
        count = result['result']['count']
        print(f"Found {count} workflows:")
        for wf in workflows[:5]:  # Show first 5
            print(f"  - {wf.get('name', 'Unnamed')} (ID: {wf.get('id')})")
    else:
        print(f"Error: {result['error']}")

    print(f"Execution time: {result['execution_time']:.2f}s")

    # ================================================================
    # Example 4: Trigger a Workflow
    # ================================================================
    print("\n### Example 4: Trigger a workflow with data ###\n")

    result = await tool.execute(
        action='trigger_workflow',
        workflow_id='workflow_123',
        data={
            'customer_name': 'John Doe',
            'order_amount': 100.00,
            'items': ['Product A', 'Product B'],
            'notification_email': 'john@example.com'
        }
    )

    if result['success']:
        exec_id = result['result']['execution_id']
        status = result['result']['status']
        print(f"Workflow triggered successfully!")
        print(f"Execution ID: {exec_id}")
        print(f"Status: {status}")
    else:
        print(f"Error: {result['error']}")

    print(f"Execution time: {result['execution_time']:.2f}s")

    # ================================================================
    # Example 5: Check Workflow Execution Status
    # ================================================================
    print("\n### Example 5: Check execution status ###\n")

    # Assuming we got execution_id from previous trigger
    execution_id = 'exec_456'

    result = await tool.execute(
        action='get_workflow_status',
        execution_id=execution_id
    )

    if result['success']:
        status = result['result']['status']
        finished = result['result']['finished']
        print(f"Execution ID: {execution_id}")
        print(f"Status: {status}")
        print(f"Finished: {finished}")

        if finished:
            print(f"Started at: {result['result'].get('started_at', 'N/A')}")
            print(f"Stopped at: {result['result'].get('stopped_at', 'N/A')}")
    else:
        print(f"Error: {result['error']}")

    print(f"Execution time: {result['execution_time']:.2f}s")

    # ================================================================
    # Example 6: Get Workflow Execution Results
    # ================================================================
    print("\n### Example 6: Get execution results ###\n")

    result = await tool.execute(
        action='get_workflow_result',
        execution_id=execution_id
    )

    if result['success']:
        exec_result = result['result']
        print(f"Execution ID: {exec_result['execution_id']}")
        print(f"Status: {exec_result['status']}")
        print(f"Finished: {exec_result['finished']}")
        print(f"\nResult Data:")
        print(exec_result.get('data', {}))
    else:
        print(f"Error: {result['error']}")

    print(f"Execution time: {result['execution_time']:.2f}s")

    # ================================================================
    # Example 7: Get Tool Information (for RL system)
    # ================================================================
    print("\n### Example 7: Get tool metadata ###\n")

    tool_info = tool.get_tool_info()

    print(f"Name: {tool_info['name']}")
    print(f"Description: {tool_info['description']}")
    print(f"Cost: {tool_info['cost']}")
    print(f"Success Rate: {tool_info['success_rate']}")
    print(f"Average Time: {tool_info['avg_time']}s")
    print(f"Requires Approval: {tool_info['requires_approval']}")
    print(f"Composable: {tool_info['composable']}")
    print(f"Available: {tool_info['available']}")
    print(f"Access Mode: {tool_info['access_mode']}")

    print("\nSupported Parameters:")
    for param_name, param_info in tool_info['parameters'].items():
        required = "required" if param_info['required'] else "optional"
        print(f"  - {param_name} ({param_info['type']}, {required})")
        print(f"    {param_info['description']}")

    # ================================================================
    # Example 8: Format Results for Prince Flowers
    # ================================================================
    print("\n### Example 8: Format result for Prince Flowers output ###\n")

    # Example result
    example_result = {
        'success': True,
        'result': {
            'execution_id': 'exec_789',
            'workflow_id': 'workflow_123',
            'status': 'success',
            'finished': True,
            'triggered_at': '2025-10-13T12:00:00Z'
        }
    }

    formatted_output = tool.format_for_prince(example_result)
    print(formatted_output)

    # ================================================================
    # Example 9: Error Handling
    # ================================================================
    print("\n### Example 9: Error handling ###\n")

    # Try to trigger workflow without workflow_id
    result = await tool.execute(
        action='trigger_workflow'
        # Missing workflow_id - should raise error
    )

    if not result['success']:
        print(f"Expected error caught: {result['error']}")

    # Try invalid action
    result = await tool.execute(action='invalid_action')

    if not result['success']:
        print(f"Expected error caught: {result['error']}")

    # ================================================================
    # Example 10: Integration with Prince Flowers
    # ================================================================
    print("\n### Example 10: Integration with Prince Flowers ###\n")

    from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

    # Initialize Prince Flowers
    prince = TORQPrinceFlowers()

    # Check if n8n_workflow tool is registered
    if 'n8n_workflow' in prince.available_tools:
        print("✅ N8N Workflow Tool registered in Prince Flowers")
        tool_info = prince.available_tools['n8n_workflow']
        print(f"   Name: {tool_info['name']}")
        print(f"   Description: {tool_info['description']}")
    else:
        print("❌ N8N Workflow Tool NOT registered in Prince Flowers")

    # Check if execute method exists
    if hasattr(prince, '_execute_n8n_workflow'):
        print("✅ _execute_n8n_workflow method exists")

        # Execute via Prince Flowers
        result = await prince._execute_n8n_workflow(
            action='list_workflows'
        )

        if result['success']:
            print(f"✅ Successfully executed via Prince Flowers")
            print(f"   Found {result['result']['count']} workflows")
        else:
            print(f"⚠ Execution failed: {result['error']}")
    else:
        print("❌ _execute_n8n_workflow method NOT found")

    # ================================================================
    # Cleanup
    # ================================================================
    print("\n### Cleanup ###\n")

    await tool.cleanup()
    print("✅ Tool resources cleaned up")

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)


# ================================================================
# Expected Output Examples
# ================================================================

"""
EXPECTED OUTPUT (with valid credentials):

============================================================
N8N Workflow Tool - Usage Examples
============================================================

### Example 1: Create tool with explicit credentials ###

Tool Name: N8N Workflow Automation
Tool Description: Execute and manage n8n automation workflows
Tool Available: True
Access Mode: Direct API

### Example 2: Create tool using environment variables ###

Tool configured from environment: True

### Example 3: List all workflows ###

Found 12 workflows:
  - Customer Onboarding (ID: workflow_001)
  - Order Processing (ID: workflow_002)
  - Email Notifications (ID: workflow_003)
  - Data Sync (ID: workflow_004)
  - Report Generation (ID: workflow_005)
Execution time: 0.45s

### Example 4: Trigger a workflow with data ###

Workflow triggered successfully!
Execution ID: exec_abc123
Status: running
Execution time: 0.78s

### Example 5: Check execution status ###

Execution ID: exec_456
Status: success
Finished: True
Started at: 2025-10-13T11:58:00Z
Stopped at: 2025-10-13T11:59:32Z
Execution time: 0.32s

### Example 6: Get execution results ###

Execution ID: exec_456
Status: success
Finished: True

Result Data:
{'customer_id': 12345, 'order_id': 67890, 'total': 100.0, 'status': 'completed'}
Execution time: 0.34s

### Example 7: Get tool metadata ###

Name: N8N Workflow Automation
Description: Execute and manage n8n automation workflows
Cost: 0.2
Success Rate: 0.88
Average Time: 1.5s
Requires Approval: False
Composable: True
Available: True
Access Mode: Direct API

Supported Parameters:
  - action (string, required)
    Workflow operation to perform
  - workflow_id (string, optional)
    Workflow ID (required for trigger_workflow)
  - execution_id (string, optional)
    Execution ID (required for status and result queries)
  - data (object, optional)
    Data payload for workflow trigger

### Example 8: Format result for Prince Flowers output ###

N8N Workflow Execution:

Execution ID: exec_789
Status: success
Workflow ID: workflow_123
Completed at: 2025-10-13T12:00:00Z

### Example 9: Error handling ###

Expected error caught: Validation error: workflow_id is required for trigger_workflow action
Expected error caught: Validation error: Unknown action: invalid_action. Valid actions: list_workflows, trigger_workflow, get_workflow_status, get_workflow_result

### Example 10: Integration with Prince Flowers ###

✅ N8N Workflow Tool registered in Prince Flowers
   Name: N8N Workflow Automation
   Description: Execute and manage n8n automation workflows
✅ _execute_n8n_workflow method exists
✅ Successfully executed via Prince Flowers
   Found 12 workflows

### Cleanup ###

✅ Tool resources cleaned up

============================================================
Examples Complete!
============================================================
"""


if __name__ == '__main__':
    # Run the examples
    asyncio.run(main())
