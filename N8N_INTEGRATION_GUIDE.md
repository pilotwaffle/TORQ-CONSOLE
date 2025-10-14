# N8N Workflow Tool Integration Guide

## Phase 1.6: Integration Instructions for torq_prince_flowers.py

This document provides the exact code modifications needed to integrate the N8N Workflow Tool into Prince Flowers.

---

## Step 1: Add Import Statement

**Location:** After line 78 in `torq_console/agents/torq_prince_flowers.py`

**Add this code block:**

```python
# Import N8N Workflow Tool
try:
    from .tools.n8n_workflow_tool import create_n8n_workflow_tool
    N8N_WORKFLOW_AVAILABLE = True
except ImportError:
    N8N_WORKFLOW_AVAILABLE = False
    logging.warning("N8N Workflow Tool not available")
```

---

## Step 2: Add Tool Registry Entry

**Location:** In the `_init_tool_ecosystem` method, after the 'code_generation' entry (around line 394)

**Add this dictionary entry:**

```python
'n8n_workflow': {
    'name': 'N8N Workflow Automation',
    'description': 'Execute and manage n8n automation workflows',
    'cost': 0.2,
    'success_rate': 0.88,
    'avg_time': 1.5,
    'dependencies': [],
    'composable': True,
    'requires_approval': False
},
```

---

## Step 3: Add Execute N8N Workflow Method

**Location:** After the `_execute_code_generation` method (around line 2213)

**Add this complete method:**

```python
async def _execute_n8n_workflow(
    self,
    action: str,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute n8n workflow automation operations.

    Args:
        action: Operation to perform (list_workflows, trigger_workflow,
                get_workflow_status, get_workflow_result)
        workflow_id: Workflow ID (required for trigger_workflow)
        execution_id: Execution ID (required for status/result queries)
        data: Data payload for workflow trigger
        **kwargs: Additional parameters

    Returns:
        Dict with success status and operation results
    """
    import time
    start_time = time.time()

    # Update tool performance
    self.tool_performance['n8n_workflow']['usage_count'] += 1

    if not N8N_WORKFLOW_AVAILABLE:
        error_msg = "N8N Workflow Tool not available. Install httpx: pip install httpx"
        self.logger.error(f"[N8N] {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'action': action,
            'execution_time': time.time() - start_time
        }

    try:
        self.logger.info(f"[N8N] Executing action: {action}")

        # Create N8N workflow tool
        n8n_tool = create_n8n_workflow_tool()

        # Check availability
        if not n8n_tool.is_available():
            error_msg = ("N8N Workflow Tool not configured. Set N8N_API_URL and N8N_API_KEY "
                        "environment variables, or connect MCP n8n server.")
            self.logger.warning(f"[N8N] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'action': action,
                'execution_time': time.time() - start_time
            }

        # Execute workflow operation
        result = await n8n_tool.execute(
            action=action,
            workflow_id=workflow_id,
            execution_id=execution_id,
            data=data,
            **kwargs
        )

        execution_time = time.time() - start_time
        result['execution_time'] = execution_time

        # Update success stats
        if result.get('success'):
            self.tool_performance['n8n_workflow']['success_count'] += 1
            self.tool_performance['n8n_workflow']['total_time'] += execution_time

            # Log success based on action type
            if action == 'list_workflows':
                count = result.get('result', {}).get('count', 0)
                self.logger.info(f"[N8N] ✓ SUCCESS - Listed {count} workflows")
            elif action == 'trigger_workflow':
                exec_id = result.get('result', {}).get('execution_id', 'N/A')
                self.logger.info(f"[N8N] ✓ SUCCESS - Triggered workflow {workflow_id}, execution: {exec_id}")
            elif action == 'get_workflow_status':
                status = result.get('result', {}).get('status', 'unknown')
                self.logger.info(f"[N8N] ✓ SUCCESS - Execution {execution_id} status: {status}")
            elif action == 'get_workflow_result':
                status = result.get('result', {}).get('status', 'unknown')
                finished = result.get('result', {}).get('finished', False)
                self.logger.info(f"[N8N] ✓ SUCCESS - Execution {execution_id} finished: {finished}, status: {status}")
        else:
            self.logger.error(f"[N8N] ✗ FAILED: {result.get('error')}")

        return result

    except Exception as e:
        execution_time = time.time() - start_time
        error_msg = f"N8N workflow operation error: {str(e)}"
        self.logger.error(f"[N8N] ✗ ERROR: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'action': action,
            'execution_time': execution_time
        }
```

---

## Query Routing Keywords

The N8N Workflow Tool should be triggered when queries contain these keywords:

- `workflow`
- `n8n`
- `automate`
- `automation`
- `execute workflow`
- `trigger workflow`
- `workflow status`
- `list workflows`

These keywords should be added to the query routing logic in the `process_query` method or wherever tool selection happens based on query content.

---

## Environment Variables Required

For Direct API Mode:
```bash
N8N_API_URL=https://your-n8n-instance.com/api/v1
N8N_API_KEY=your_api_key_here
```

For MCP Server Mode:
- Ensure MCP n8n server is connected and available
- No additional environment variables needed

---

## Verification

After integration, verify with:

```bash
# Test import
python -c "from torq_console.agents.tools import N8NWorkflowTool, create_n8n_workflow_tool; print('✅ Import OK')"

# Test integration
cd TORQ-CONSOLE && python -c "from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers; prince = TORQPrinceFlowers(); print('✅ Integration OK' if 'n8n_workflow' in prince.available_tools else '❌ Not in registry')"

# Test execute method
cd TORQ-CONSOLE && python -c "from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers; prince = TORQPrinceFlowers(); print('✅ Execute method exists' if hasattr(prince, '_execute_n8n_workflow') else '❌ Method missing')"
```

---

## Usage Example

```python
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers

# Initialize Prince Flowers
prince = TORQPrinceFlowers()

# List workflows
result = await prince._execute_n8n_workflow(action='list_workflows')
print(result)

# Trigger a workflow
result = await prince._execute_n8n_workflow(
    action='trigger_workflow',
    workflow_id='workflow_123',
    data={'customer': 'John Doe', 'amount': 100}
)
print(result)

# Check execution status
result = await prince._execute_n8n_workflow(
    action='get_workflow_status',
    execution_id='exec_456'
)
print(result)

# Get execution results
result = await prince._execute_n8n_workflow(
    action='get_workflow_result',
    execution_id='exec_456'
)
print(result)
```

---

## Integration Complete!

All three modifications above will complete the N8N Workflow Tool integration into Prince Flowers.
