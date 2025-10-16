# Import N8N Workflow Tool
try:
    from .tools.n8n_workflow_tool import create_n8n_workflow_tool
    N8N_WORKFLOW_AVAILABLE = True
except ImportError:
    N8N_WORKFLOW_AVAILABLE = False
    logging.warning("N8N Workflow Tool not available")
