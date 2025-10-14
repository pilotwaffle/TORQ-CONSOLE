"""
N8N Workflow Automation Tool for Prince Flowers
Provides workflow automation through n8n MCP server and direct API access
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# Try to import httpx for async HTTP requests
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not installed. Install with: pip install httpx")


class N8NWorkflowTool:
    """
    Prince Flowers tool wrapper for n8n workflow automation.

    Provides a standardized interface for interacting with n8n workflows
    through both MCP server integration and direct n8n API access.

    Supports:
    - List all available workflows
    - Trigger workflow executions with custom data
    - Check execution status
    - Retrieve execution results

    Requires either:
    - MCP n8n server connection (mcp__n8n-server__*)
    - Direct n8n API credentials (N8N_API_URL, N8N_API_KEY)

    Example:
        >>> tool = create_n8n_workflow_tool()
        >>> result = await tool.execute(
        ...     action='trigger_workflow',
        ...     workflow_id='workflow_123',
        ...     data={'customer': 'John Doe', 'amount': 100}
        ... )
        >>> print(result['success'])
        True
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mcp_server: Optional[Any] = None,
        timeout: int = 30
    ):
        """
        Initialize the N8N workflow automation tool.

        Args:
            api_url: n8n API URL (e.g., https://n8n.example.com/api/v1)
            api_key: n8n API key for authentication
            mcp_server: Optional MCP server instance for n8n integration
            timeout: HTTP request timeout in seconds (default: 30)
        """
        self.logger = logging.getLogger(__name__)

        # Tool metadata for Prince's ecosystem
        self.name = "N8N Workflow Automation"
        self.description = "Execute and manage n8n automation workflows"
        self.cost = 0.2  # Time/resource cost for RL system
        self.success_rate = 0.88  # Historical success rate
        self.avg_time = 1.5  # Average execution time in seconds
        self.requires_approval = False  # No approval needed for workflow execution
        self.composable = True  # Can be composed with other tools

        # Get configuration from environment if not provided
        self.api_url = api_url or os.getenv('N8N_API_URL')
        self.api_key = api_key or os.getenv('N8N_API_KEY')
        self.mcp_server = mcp_server
        self.timeout = timeout

        # Remove trailing slash from API URL if present
        if self.api_url and self.api_url.endswith('/'):
            self.api_url = self.api_url.rstrip('/')

        # Initialize HTTP client
        self.client = None
        self.configured = False

        # Determine configuration mode
        self._configure_access_mode()

        if self.configured:
            self.logger.info("N8N Workflow Tool initialized successfully")
        else:
            self.logger.warning("N8N Workflow Tool not fully configured - limited functionality")

    def _configure_access_mode(self):
        """Determine and configure the access mode (MCP vs Direct API)."""
        # Check MCP server availability
        if self.mcp_server:
            self.logger.info("N8N Tool: Using MCP server integration")
            self.configured = True
            return

        # Check direct API configuration
        if HTTPX_AVAILABLE and self.api_url and self.api_key:
            try:
                # Initialize httpx async client with authentication
                self.client = httpx.AsyncClient(
                    base_url=self.api_url,
                    headers={
                        'X-N8N-API-KEY': self.api_key,
                        'Content-Type': 'application/json'
                    },
                    timeout=self.timeout
                )
                self.logger.info("N8N Tool: Using direct API access")
                self.configured = True
            except Exception as e:
                self.logger.error(f"Failed to initialize n8n API client: {e}")
                self.configured = False
        else:
            if not HTTPX_AVAILABLE:
                self.logger.warning("httpx not available - install with: pip install httpx")
            elif not self.api_url or not self.api_key:
                self.logger.warning("N8N API credentials not configured - set N8N_API_URL and N8N_API_KEY")

    def is_available(self) -> bool:
        """
        Check if the tool is available and configured.

        Returns:
            True if either MCP server or direct API is configured, False otherwise
        """
        return self.configured and (self.mcp_server is not None or self.client is not None)

    async def execute(
        self,
        action: str,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute n8n workflow operations.

        Args:
            action: Operation to perform
                - 'list_workflows': List all available workflows
                - 'trigger_workflow': Trigger a workflow execution
                - 'get_workflow_status': Check execution status
                - 'get_workflow_result': Get execution results
            workflow_id: Workflow ID (required for trigger_workflow)
            execution_id: Execution ID (required for status/result queries)
            data: Data payload for workflow trigger (optional)
            **kwargs: Additional parameters for specific actions

        Returns:
            Dict containing:
                - success: bool - Operation success status
                - result: Any - Operation result data
                - error: str - Error message (if failed)
                - execution_time: float - Operation duration in seconds
                - timestamp: str - ISO format timestamp

        Example:
            >>> # List workflows
            >>> result = await tool.execute(action='list_workflows')
            >>>
            >>> # Trigger workflow
            >>> result = await tool.execute(
            ...     action='trigger_workflow',
            ...     workflow_id='123',
            ...     data={'customer': 'John'}
            ... )
            >>>
            >>> # Check status
            >>> result = await tool.execute(
            ...     action='get_workflow_status',
            ...     execution_id='exec_456'
            ... )
        """
        start_time = datetime.now()

        # Validate availability
        if not self.is_available():
            error_msg = self._get_unavailable_error_message()
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }

        # Route to appropriate handler
        try:
            if action == 'list_workflows':
                result = await self._list_workflows()
            elif action == 'trigger_workflow':
                if not workflow_id:
                    raise ValueError("workflow_id is required for trigger_workflow action")
                result = await self._trigger_workflow(workflow_id, data or {})
            elif action == 'get_workflow_status':
                if not execution_id:
                    raise ValueError("execution_id is required for get_workflow_status action")
                result = await self._get_workflow_status(execution_id)
            elif action == 'get_workflow_result':
                if not execution_id:
                    raise ValueError("execution_id is required for get_workflow_result action")
                result = await self._get_workflow_result(execution_id)
            else:
                raise ValueError(f"Unknown action: {action}. Valid actions: list_workflows, trigger_workflow, get_workflow_status, get_workflow_result")

            # Add execution metadata
            result['execution_time'] = (datetime.now() - start_time).total_seconds()
            result['timestamp'] = datetime.now().isoformat()

            if result.get('success'):
                self.logger.info(f"N8N {action} completed successfully")
            else:
                self.logger.warning(f"N8N {action} failed: {result.get('error')}")

            return result

        except ValueError as e:
            error_msg = f"Validation error: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            error_msg = f"Unexpected error during {action}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'result': None,
                'error': error_msg,
                'execution_time': (datetime.now() - start_time).total_seconds(),
                'timestamp': datetime.now().isoformat()
            }

    async def _list_workflows(self) -> Dict[str, Any]:
        """
        List all available workflows.

        Returns:
            Dict with success status and list of workflows
        """
        try:
            # MCP server mode
            if self.mcp_server:
                result = await self._mcp_list_workflows()
                return result

            # Direct API mode
            if self.client:
                response = await self.client.get('/workflows')
                response.raise_for_status()
                workflows = response.json()

                return {
                    'success': True,
                    'result': {
                        'workflows': workflows.get('data', []),
                        'count': len(workflows.get('data', []))
                    },
                    'error': None
                }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error listing workflows: {e.response.status_code} - {e.response.text}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Error listing workflows: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _trigger_workflow(self, workflow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger a workflow execution.

        Args:
            workflow_id: The workflow ID to trigger
            data: Data payload to send to the workflow

        Returns:
            Dict with success status and execution details
        """
        try:
            # MCP server mode
            if self.mcp_server:
                result = await self._mcp_trigger_workflow(workflow_id, data)
                return result

            # Direct API mode
            if self.client:
                response = await self.client.post(
                    f'/workflows/{workflow_id}/execute',
                    json=data
                )
                response.raise_for_status()
                execution_data = response.json()

                return {
                    'success': True,
                    'result': {
                        'execution_id': execution_data.get('data', {}).get('executionId'),
                        'workflow_id': workflow_id,
                        'status': execution_data.get('data', {}).get('status', 'running'),
                        'triggered_at': datetime.now().isoformat()
                    },
                    'error': None
                }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error triggering workflow {workflow_id}: {e.response.status_code} - {e.response.text}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Error triggering workflow {workflow_id}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _get_workflow_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get workflow execution status.

        Args:
            execution_id: The execution ID to check

        Returns:
            Dict with success status and execution status
        """
        try:
            # MCP server mode
            if self.mcp_server:
                result = await self._mcp_get_execution_status(execution_id)
                return result

            # Direct API mode
            if self.client:
                response = await self.client.get(f'/executions/{execution_id}')
                response.raise_for_status()
                execution = response.json()

                return {
                    'success': True,
                    'result': {
                        'execution_id': execution_id,
                        'status': execution.get('data', {}).get('status'),
                        'finished': execution.get('data', {}).get('finished', False),
                        'started_at': execution.get('data', {}).get('startedAt'),
                        'stopped_at': execution.get('data', {}).get('stoppedAt')
                    },
                    'error': None
                }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error getting status for execution {execution_id}: {e.response.status_code} - {e.response.text}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Error getting status for execution {execution_id}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _get_workflow_result(self, execution_id: str) -> Dict[str, Any]:
        """
        Get workflow execution results.

        Args:
            execution_id: The execution ID to retrieve results for

        Returns:
            Dict with success status and execution results
        """
        try:
            # MCP server mode
            if self.mcp_server:
                result = await self._mcp_get_execution_result(execution_id)
                return result

            # Direct API mode
            if self.client:
                response = await self.client.get(f'/executions/{execution_id}')
                response.raise_for_status()
                execution = response.json()

                execution_data = execution.get('data', {})

                return {
                    'success': True,
                    'result': {
                        'execution_id': execution_id,
                        'status': execution_data.get('status'),
                        'finished': execution_data.get('finished', False),
                        'data': execution_data.get('data', {}),
                        'started_at': execution_data.get('startedAt'),
                        'stopped_at': execution_data.get('stoppedAt')
                    },
                    'error': None
                }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error getting result for execution {execution_id}: {e.response.status_code} - {e.response.text}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"Error getting result for execution {execution_id}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    # MCP Server Integration Methods
    async def _mcp_list_workflows(self) -> Dict[str, Any]:
        """
        List workflows via MCP server.

        Returns:
            Dict with success status and workflows list
        """
        try:
            # Call MCP server method for listing workflows
            # Format: mcp__n8n-server__list_workflows()
            result = await self.mcp_server.call_tool('mcp__n8n-server__list_workflows', {})

            return {
                'success': True,
                'result': {
                    'workflows': result.get('workflows', []),
                    'count': len(result.get('workflows', []))
                },
                'error': None
            }
        except Exception as e:
            error_msg = f"MCP error listing workflows: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _mcp_trigger_workflow(self, workflow_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger workflow via MCP server.

        Args:
            workflow_id: Workflow ID
            data: Workflow data payload

        Returns:
            Dict with success status and execution details
        """
        try:
            # Call MCP server method for triggering workflow
            # Format: mcp__n8n-server__trigger_workflow(workflow_id, data)
            result = await self.mcp_server.call_tool(
                'mcp__n8n-server__trigger_workflow',
                {
                    'workflow_id': workflow_id,
                    'data': data
                }
            )

            return {
                'success': True,
                'result': {
                    'execution_id': result.get('execution_id'),
                    'workflow_id': workflow_id,
                    'status': result.get('status', 'running'),
                    'triggered_at': datetime.now().isoformat()
                },
                'error': None
            }
        except Exception as e:
            error_msg = f"MCP error triggering workflow {workflow_id}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _mcp_get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get execution status via MCP server.

        Args:
            execution_id: Execution ID

        Returns:
            Dict with success status and execution status
        """
        try:
            # Call MCP server method for getting execution status
            # Format: mcp__n8n-server__get_execution_status(execution_id)
            result = await self.mcp_server.call_tool(
                'mcp__n8n-server__get_execution_status',
                {
                    'execution_id': execution_id
                }
            )

            return {
                'success': True,
                'result': {
                    'execution_id': execution_id,
                    'status': result.get('status'),
                    'finished': result.get('finished', False),
                    'started_at': result.get('started_at'),
                    'stopped_at': result.get('stopped_at')
                },
                'error': None
            }
        except Exception as e:
            error_msg = f"MCP error getting execution status {execution_id}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    async def _mcp_get_execution_result(self, execution_id: str) -> Dict[str, Any]:
        """
        Get execution result via MCP server.

        Args:
            execution_id: Execution ID

        Returns:
            Dict with success status and execution result
        """
        try:
            # Call MCP server method for getting execution result
            # Format: mcp__n8n-server__get_execution_result(execution_id)
            result = await self.mcp_server.call_tool(
                'mcp__n8n-server__get_execution_result',
                {
                    'execution_id': execution_id
                }
            )

            return {
                'success': True,
                'result': {
                    'execution_id': execution_id,
                    'status': result.get('status'),
                    'finished': result.get('finished', False),
                    'data': result.get('data', {}),
                    'started_at': result.get('started_at'),
                    'stopped_at': result.get('stopped_at')
                },
                'error': None
            }
        except Exception as e:
            error_msg = f"MCP error getting execution result {execution_id}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'result': None,
                'error': error_msg
            }

    def _get_unavailable_error_message(self) -> str:
        """
        Generate detailed error message when tool is unavailable.

        Returns:
            Actionable error message string
        """
        error_msg = "N8N Workflow Tool not available. "

        if not HTTPX_AVAILABLE:
            error_msg += "Missing dependency: httpx. Install with: pip install httpx. "

        if not self.mcp_server and (not self.api_url or not self.api_key):
            error_msg += "Configuration required: Set N8N_API_URL and N8N_API_KEY environment variables, "
            error_msg += "or provide MCP n8n server connection."

        return error_msg

    def get_tool_info(self) -> Dict[str, Any]:
        """
        Get tool information for Prince's tool registry.

        Returns:
            Dict containing tool metadata including parameters and capabilities
        """
        return {
            'name': self.name,
            'description': self.description,
            'cost': self.cost,
            'success_rate': self.success_rate,
            'avg_time': self.avg_time,
            'requires_approval': self.requires_approval,
            'composable': self.composable,
            'available': self.is_available(),
            'dependencies': [],
            'access_mode': 'MCP' if self.mcp_server else 'Direct API' if self.client else 'None',
            'parameters': {
                'action': {
                    'type': 'string',
                    'required': True,
                    'enum': ['list_workflows', 'trigger_workflow', 'get_workflow_status', 'get_workflow_result'],
                    'description': 'Workflow operation to perform'
                },
                'workflow_id': {
                    'type': 'string',
                    'required': False,
                    'description': 'Workflow ID (required for trigger_workflow)'
                },
                'execution_id': {
                    'type': 'string',
                    'required': False,
                    'description': 'Execution ID (required for status and result queries)'
                },
                'data': {
                    'type': 'object',
                    'required': False,
                    'description': 'Data payload for workflow trigger'
                }
            }
        }

    def format_for_prince(self, result: Dict[str, Any]) -> str:
        """
        Format result for Prince Flowers output.

        Args:
            result: Execution result dict

        Returns:
            Formatted string for Prince's response
        """
        if not result.get('success'):
            return f"N8N Workflow operation failed: {result.get('error', 'Unknown error')}"

        result_data = result.get('result', {})

        # Format based on result type
        if 'workflows' in result_data:
            # List workflows result
            workflows = result_data['workflows']
            count = result_data.get('count', 0)
            response = f"N8N Workflows ({count} total):\n\n"
            for wf in workflows[:10]:  # Show first 10
                response += f"- {wf.get('name', 'Unnamed')} (ID: {wf.get('id')})\n"
            if count > 10:
                response += f"\n... and {count - 10} more workflows"
            return response

        elif 'execution_id' in result_data:
            # Execution result
            exec_id = result_data.get('execution_id')
            status = result_data.get('status', 'unknown')
            response = f"N8N Workflow Execution:\n\n"
            response += f"Execution ID: {exec_id}\n"
            response += f"Status: {status}\n"

            if 'workflow_id' in result_data:
                response += f"Workflow ID: {result_data.get('workflow_id')}\n"

            if result_data.get('finished'):
                response += f"Completed at: {result_data.get('stopped_at', 'N/A')}\n"

            return response

        else:
            # Generic result
            return f"N8N Workflow operation completed successfully:\n{result_data}"

    async def cleanup(self):
        """Cleanup resources (close HTTP client if needed)."""
        if self.client:
            await self.client.aclose()
            self.logger.info("N8N HTTP client closed")


# Factory function for easy integration
def create_n8n_workflow_tool(
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    mcp_server: Optional[Any] = None,
    timeout: int = 30
) -> N8NWorkflowTool:
    """
    Factory function to create N8N workflow tool instance.

    Args:
        api_url: Optional n8n API URL (uses N8N_API_URL env var if not provided)
        api_key: Optional n8n API key (uses N8N_API_KEY env var if not provided)
        mcp_server: Optional MCP n8n server instance
        timeout: HTTP request timeout in seconds (default: 30)

    Returns:
        N8NWorkflowTool instance

    Example:
        >>> # Using environment variables
        >>> tool = create_n8n_workflow_tool()
        >>>
        >>> # Using explicit credentials
        >>> tool = create_n8n_workflow_tool(
        ...     api_url='https://n8n.example.com/api/v1',
        ...     api_key='your_api_key_here'
        ... )
        >>>
        >>> # Using MCP server
        >>> tool = create_n8n_workflow_tool(mcp_server=mcp_n8n_instance)
    """
    return N8NWorkflowTool(
        api_url=api_url,
        api_key=api_key,
        mcp_server=mcp_server,
        timeout=timeout
    )
