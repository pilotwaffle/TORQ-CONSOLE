# N8N Workflow Tool - Quick Reference

## 🚀 Quick Start

### Setup
```bash
# Install dependency
pip install httpx

# Set environment variables
export N8N_API_URL="https://your-n8n.com/api/v1"
export N8N_API_KEY="your_api_key"
```

### Verify Installation
```bash
cd E:\TORQ-CONSOLE
python verify_n8n_integration.py
```

---

## 📦 Import

```python
# Standalone use
from torq_console.agents.tools import create_n8n_workflow_tool

# Via Prince Flowers
from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers
```

---

## 🔧 Basic Usage

### Create Tool
```python
# Using environment variables (recommended)
tool = create_n8n_workflow_tool()

# Using explicit credentials
tool = create_n8n_workflow_tool(
    api_url='https://n8n.example.com/api/v1',
    api_key='your_api_key'
)

# Using MCP server
tool = create_n8n_workflow_tool(mcp_server=mcp_instance)
```

### List Workflows
```python
result = await tool.execute(action='list_workflows')

if result['success']:
    for wf in result['result']['workflows']:
        print(f"{wf['name']} - {wf['id']}")
```

### Trigger Workflow
```python
result = await tool.execute(
    action='trigger_workflow',
    workflow_id='workflow_123',
    data={'customer': 'John', 'amount': 100}
)

if result['success']:
    exec_id = result['result']['execution_id']
    print(f"Execution ID: {exec_id}")
```

### Check Status
```python
result = await tool.execute(
    action='get_workflow_status',
    execution_id='exec_456'
)

print(f"Status: {result['result']['status']}")
print(f"Finished: {result['result']['finished']}")
```

### Get Results
```python
result = await tool.execute(
    action='get_workflow_result',
    execution_id='exec_456'
)

print(f"Data: {result['result']['data']}")
```

---

## 🎯 Via Prince Flowers

```python
prince = TORQPrinceFlowers()

# Check if tool is registered
if 'n8n_workflow' in prince.available_tools:
    # Execute operation
    result = await prince._execute_n8n_workflow(
        action='trigger_workflow',
        workflow_id='workflow_123',
        data={'key': 'value'}
    )
```

---

## 📋 Actions Reference

| Action | Required Params | Returns |
|--------|----------------|---------|
| `list_workflows` | - | List of workflows |
| `trigger_workflow` | `workflow_id`, `data` | Execution ID, status |
| `get_workflow_status` | `execution_id` | Status, finished, timestamps |
| `get_workflow_result` | `execution_id` | Complete execution data |

---

## 🔄 Return Format

```python
{
    'success': bool,          # Operation success status
    'result': dict,           # Operation result data
    'error': str | None,      # Error message if failed
    'execution_time': float,  # Operation duration (seconds)
    'timestamp': str          # ISO format timestamp
}
```

---

## 🛠️ Tool Info

```python
info = tool.get_tool_info()

# Returns:
{
    'name': 'N8N Workflow Automation',
    'description': 'Execute and manage n8n automation workflows',
    'cost': 0.2,
    'success_rate': 0.88,
    'avg_time': 1.5,
    'requires_approval': False,
    'composable': True,
    'available': True/False,
    'access_mode': 'MCP'/'Direct API'/'None',
    'parameters': {...}
}
```

---

## ⚠️ Error Handling

```python
result = await tool.execute(action='trigger_workflow')

if not result['success']:
    error = result['error']

    if 'workflow_id is required' in error:
        # Missing required parameter
        pass
    elif 'not configured' in error:
        # Missing credentials
        pass
    elif 'HTTP error' in error:
        # API communication error
        pass
```

---

## 🔍 Availability Check

```python
if tool.is_available():
    # Tool is configured and ready
    result = await tool.execute(...)
else:
    # Not configured - check credentials
    print("Set N8N_API_URL and N8N_API_KEY")
```

---

## 📦 Files Reference

| File | Path | Purpose |
|------|------|---------|
| **Main Tool** | `torq_console/agents/tools/n8n_workflow_tool.py` | Core implementation |
| **Integration** | `torq_console/agents/torq_prince_flowers.py` | Prince Flowers integration |
| **Examples** | `n8n_usage_example.py` | 10 usage examples |
| **Verification** | `verify_n8n_integration.py` | Automated tests |
| **Guide** | `N8N_INTEGRATION_GUIDE.md` | Integration instructions |

---

## 🔐 Environment Variables

```bash
# Direct API Mode (required)
export N8N_API_URL="https://n8n.example.com/api/v1"
export N8N_API_KEY="your_api_key_here"

# MCP Mode (no env vars needed, just connect MCP server)
```

---

## ✅ Verification Commands

```bash
# Test import
python -c "from torq_console.agents.tools import N8NWorkflowTool; print('✅')"

# Test integration
python -c "from torq_console.agents.torq_prince_flowers import TORQPrinceFlowers; print('✅' if 'n8n_workflow' in TORQPrinceFlowers().available_tools else '❌')"

# Run full verification
python verify_n8n_integration.py
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: httpx` | `pip install httpx` |
| `Tool not configured` | Set `N8N_API_URL` and `N8N_API_KEY` |
| `401 Unauthorized` | Check API key is correct |
| `404 Not Found` | Verify workflow_id exists |
| `Connection refused` | Check n8n instance is accessible |

---

## 📚 Documentation Links

- **Integration Guide**: `N8N_INTEGRATION_GUIDE.md`
- **Complete Summary**: `N8N_INTEGRATION_COMPLETE.md`
- **Deliverables**: `N8N_DELIVERABLES_SUMMARY.md`
- **Usage Examples**: `n8n_usage_example.py`

---

## 🎯 Query Keywords

Prince Flowers triggers on these keywords:
- `workflow`
- `n8n`
- `automate`
- `automation`
- `trigger workflow`
- `list workflows`

---

## 💡 Tips

- Use environment variables for credentials (security)
- Check `is_available()` before execution
- Handle errors gracefully (check `result['success']`)
- Use MCP mode when available (no credentials needed)
- Log operations use `self.logger` (not `print()`)
- Async operations - always use `await`

---

**Need Help?** See `N8N_INTEGRATION_GUIDE.md` for detailed instructions.

**Examples**: See `n8n_usage_example.py` for 10 complete examples.

**Verify**: Run `python verify_n8n_integration.py` to check everything.
