"""
N8N Workflow Integration for TORQ Console.

Provides comprehensive N8N workflow automation capabilities including
workflow creation, management, execution, and monitoring.
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import httpx
from pathlib import Path


class WorkflowStatus(Enum):
    """N8N workflow status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    RUNNING = "running"


class NodeType(Enum):
    """Common N8N node types."""
    HTTP_REQUEST = "n8n-nodes-base.httpRequest"
    WEBHOOK = "n8n-nodes-base.webhook"
    CODE = "n8n-nodes-base.code"
    SET = "n8n-nodes-base.set"
    IF = "n8n-nodes-base.if"
    SWITCH = "n8n-nodes-base.switch"
    WAIT = "n8n-nodes-base.wait"
    CRON = "n8n-nodes-base.cron"
    EMAIL_SEND = "n8n-nodes-base.emailSend"
    DISCORD = "n8n-nodes-base.discord"
    SLACK = "n8n-nodes-base.slack"
    TELEGRAM = "n8n-nodes-base.telegram"


@dataclass
class N8NNode:
    """Represents an N8N workflow node."""
    name: str
    type: str
    position: List[int] = field(default_factory=lambda: [0, 0])
    parameters: Dict[str, Any] = field(default_factory=dict)
    credentials: Dict[str, str] = field(default_factory=dict)
    disabled: bool = False
    notes: str = ""
    webhook_id: Optional[str] = None


@dataclass
class N8NWorkflow:
    """Represents an N8N workflow."""
    id: Optional[str] = None
    name: str = ""
    nodes: List[N8NNode] = field(default_factory=list)
    connections: Dict[str, Any] = field(default_factory=dict)
    active: bool = False
    settings: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class N8NWorkflowManager:
    """
    N8N Workflow Integration Manager.

    Features:
    - Connect to N8N instance via API
    - Create and manage workflows programmatically
    - Execute workflows and monitor status
    - Handle webhooks and triggers
    - Template-based workflow generation
    """

    def __init__(self, n8n_host: str = "http://localhost:5678", api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.n8n_host = n8n_host.rstrip('/')
        self.api_key = api_key

        # HTTP client setup
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        if api_key:
            headers['X-N8N-API-KEY'] = api_key

        self.client = httpx.AsyncClient(
            base_url=self.n8n_host,
            headers=headers,
            timeout=30.0
        )

        # Workflow templates
        self.templates = {
            'web_scraper': self._create_web_scraper_template,
            'api_monitor': self._create_api_monitor_template,
            'data_processor': self._create_data_processor_template,
            'notification_system': self._create_notification_template,
            'file_processor': self._create_file_processor_template
        }

    async def initialize(self) -> Dict[str, Any]:
        """Initialize connection to N8N instance."""
        try:
            # Test connection
            response = await self.client.get('/rest/active-workflows')

            if response.status_code == 200:
                active_workflows = response.json()

                return {
                    'success': True,
                    'n8n_host': self.n8n_host,
                    'connection_status': 'connected',
                    'active_workflows_count': len(active_workflows),
                    'api_authenticated': bool(self.api_key)
                }
            else:
                return {
                    'success': False,
                    'error': f'N8N connection failed: HTTP {response.status_code}',
                    'n8n_host': self.n8n_host
                }

        except Exception as e:
            self.logger.error(f"N8N initialization failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'n8n_host': self.n8n_host
            }

    async def create_workflow(
        self,
        name: str,
        template: Optional[str] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a new N8N workflow.

        Args:
            name: Workflow name
            template: Template name to use
            nodes: Custom nodes definition
            **kwargs: Additional workflow parameters

        Returns:
            Workflow creation result
        """
        try:
            if template and template in self.templates:
                # Use template
                workflow = await self.templates[template](name, **kwargs)
            elif nodes:
                # Use custom nodes
                workflow = N8NWorkflow(
                    name=name,
                    nodes=[N8NNode(**node) for node in nodes]
                )
                self._generate_connections(workflow)
            else:
                # Create basic workflow
                workflow = self._create_basic_workflow(name)

            # Convert to N8N format
            workflow_data = self._serialize_workflow(workflow)

            # Create in N8N
            response = await self.client.post('/rest/workflows', json=workflow_data)

            if response.status_code == 201:
                created_workflow = response.json()

                return {
                    'success': True,
                    'workflow_id': created_workflow['id'],
                    'workflow_name': created_workflow['name'],
                    'active': created_workflow.get('active', False),
                    'nodes_count': len(created_workflow.get('nodes', [])),
                    'webhook_urls': self._extract_webhook_urls(created_workflow)
                }
            else:
                return {
                    'success': False,
                    'error': f'Workflow creation failed: HTTP {response.status_code}',
                    'response': response.text
                }

        except Exception as e:
            self.logger.error(f"Workflow creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = False
    ) -> Dict[str, Any]:
        """
        Execute an N8N workflow.

        Args:
            workflow_id: ID of workflow to execute
            input_data: Optional input data for the workflow
            wait_for_completion: Whether to wait for execution completion

        Returns:
            Execution result
        """
        try:
            execution_data = {}
            if input_data:
                execution_data['startNodes'] = ['Start']
                execution_data['destinationNode'] = ''

            response = await self.client.post(
                f'/rest/workflows/{workflow_id}/execute',
                json=execution_data
            )

            if response.status_code == 200:
                execution = response.json()
                execution_id = execution.get('id')

                result = {
                    'success': True,
                    'workflow_id': workflow_id,
                    'execution_id': execution_id,
                    'status': execution.get('status', 'running'),
                    'started_at': execution.get('startedAt')
                }

                # Wait for completion if requested
                if wait_for_completion and execution_id:
                    completion_result = await self._wait_for_execution(execution_id)
                    result.update(completion_result)

                return result
            else:
                return {
                    'success': False,
                    'error': f'Workflow execution failed: HTTP {response.status_code}',
                    'workflow_id': workflow_id
                }

        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'workflow_id': workflow_id
            }

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status and details of a workflow."""
        try:
            response = await self.client.get(f'/rest/workflows/{workflow_id}')

            if response.status_code == 200:
                workflow = response.json()

                # Get recent executions
                executions_response = await self.client.get(
                    f'/rest/executions',
                    params={'filter': json.dumps({'workflowId': workflow_id}), 'limit': 10}
                )

                recent_executions = []
                if executions_response.status_code == 200:
                    executions_data = executions_response.json()
                    recent_executions = executions_data.get('data', [])

                return {
                    'success': True,
                    'workflow_id': workflow_id,
                    'name': workflow['name'],
                    'active': workflow.get('active', False),
                    'nodes_count': len(workflow.get('nodes', [])),
                    'connections_count': len(workflow.get('connections', {})),
                    'created_at': workflow.get('createdAt'),
                    'updated_at': workflow.get('updatedAt'),
                    'recent_executions': len(recent_executions),
                    'last_execution': recent_executions[0] if recent_executions else None,
                    'webhook_urls': self._extract_webhook_urls(workflow)
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to get workflow status: HTTP {response.status_code}',
                    'workflow_id': workflow_id
                }

        except Exception as e:
            self.logger.error(f"Get workflow status failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'workflow_id': workflow_id
            }

    async def list_workflows(self, active_only: bool = False) -> Dict[str, Any]:
        """List all workflows in N8N instance."""
        try:
            endpoint = '/rest/active-workflows' if active_only else '/rest/workflows'
            response = await self.client.get(endpoint)

            if response.status_code == 200:
                workflows = response.json()

                workflow_list = []
                for workflow in workflows:
                    workflow_list.append({
                        'id': workflow['id'],
                        'name': workflow['name'],
                        'active': workflow.get('active', False),
                        'nodes_count': len(workflow.get('nodes', [])),
                        'updated_at': workflow.get('updatedAt'),
                        'tags': workflow.get('tags', [])
                    })

                return {
                    'success': True,
                    'workflows_count': len(workflow_list),
                    'workflows': workflow_list,
                    'filter': 'active_only' if active_only else 'all'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to list workflows: HTTP {response.status_code}'
                }

        except Exception as e:
            self.logger.error(f"List workflows failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def create_webhook_workflow(
        self,
        name: str,
        webhook_path: str,
        processing_code: str,
        response_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a webhook-based workflow."""
        try:
            # Create webhook workflow nodes
            nodes = [
                {
                    'name': 'Webhook',
                    'type': NodeType.WEBHOOK.value,
                    'position': [250, 300],
                    'parameters': {
                        'httpMethod': 'POST',
                        'path': webhook_path,
                        'responseMode': 'responseNode',
                        'options': {}
                    }
                },
                {
                    'name': 'Process Data',
                    'type': NodeType.CODE.value,
                    'position': [450, 300],
                    'parameters': {
                        'jsCode': processing_code
                    }
                },
                {
                    'name': 'Respond',
                    'type': NodeType.HTTP_REQUEST.value,
                    'position': [650, 300],
                    'parameters': {
                        'responseData': response_data or {'success': True, 'processed': True}
                    }
                }
            ]

            return await self.create_workflow(name, nodes=nodes)

        except Exception as e:
            self.logger.error(f"Webhook workflow creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_basic_workflow(self, name: str) -> N8NWorkflow:
        """Create a basic workflow with start and end nodes."""
        nodes = [
            N8NNode(
                name='Start',
                type='n8n-nodes-base.start',
                position=[240, 300]
            ),
            N8NNode(
                name='Set Data',
                type=NodeType.SET.value,
                position=[440, 300],
                parameters={
                    'values': {
                        'string': [
                            {
                                'name': 'message',
                                'value': 'Hello from TORQ Console workflow!'
                            }
                        ]
                    }
                }
            )
        ]

        workflow = N8NWorkflow(
            name=name,
            nodes=nodes
        )

        self._generate_connections(workflow)
        return workflow

    def _generate_connections(self, workflow: N8NWorkflow):
        """Generate connections between workflow nodes."""
        connections = {}

        for i, node in enumerate(workflow.nodes[:-1]):
            next_node = workflow.nodes[i + 1]
            connections[node.name] = {
                'main': [
                    [
                        {
                            'node': next_node.name,
                            'type': 'main',
                            'index': 0
                        }
                    ]
                ]
            }

        workflow.connections = connections

    def _serialize_workflow(self, workflow: N8NWorkflow) -> Dict[str, Any]:
        """Convert workflow object to N8N API format."""
        nodes = []
        for node in workflow.nodes:
            node_data = {
                'name': node.name,
                'type': node.type,
                'position': node.position,
                'parameters': node.parameters
            }

            if node.credentials:
                node_data['credentials'] = node.credentials
            if node.disabled:
                node_data['disabled'] = node.disabled
            if node.notes:
                node_data['notes'] = node.notes

            nodes.append(node_data)

        return {
            'name': workflow.name,
            'nodes': nodes,
            'connections': workflow.connections,
            'active': workflow.active,
            'settings': workflow.settings,
            'tags': workflow.tags
        }

    def _extract_webhook_urls(self, workflow_data: Dict[str, Any]) -> List[str]:
        """Extract webhook URLs from workflow data."""
        webhook_urls = []

        for node in workflow_data.get('nodes', []):
            if node.get('type') == NodeType.WEBHOOK.value:
                webhook_path = node.get('parameters', {}).get('path', '')
                if webhook_path:
                    full_url = f"{self.n8n_host}/webhook/{webhook_path}"
                    webhook_urls.append(full_url)

        return webhook_urls

    async def _wait_for_execution(self, execution_id: str, timeout: int = 60) -> Dict[str, Any]:
        """Wait for workflow execution to complete."""
        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < timeout:
            try:
                response = await self.client.get(f'/rest/executions/{execution_id}')

                if response.status_code == 200:
                    execution = response.json()
                    status = execution.get('status')

                    if status in ['success', 'error', 'failed']:
                        return {
                            'completed': True,
                            'status': status,
                            'finished_at': execution.get('stoppedAt'),
                            'execution_time': execution.get('executionTime'),
                            'data': execution.get('data', {})
                        }

                await asyncio.sleep(2)  # Check every 2 seconds

            except Exception as e:
                self.logger.warning(f"Error checking execution status: {e}")
                break

        return {
            'completed': False,
            'status': 'timeout',
            'message': f'Execution did not complete within {timeout} seconds'
        }

    # Template methods
    async def _create_web_scraper_template(self, name: str, **kwargs) -> N8NWorkflow:
        """Create web scraper workflow template."""
        target_url = kwargs.get('url', 'https://example.com')
        css_selector = kwargs.get('selector', 'title')

        nodes = [
            N8NNode(
                name='Schedule Trigger',
                type=NodeType.CRON.value,
                position=[240, 300],
                parameters={'rule': '0 */6 * * *'}  # Every 6 hours
            ),
            N8NNode(
                name='Fetch Page',
                type=NodeType.HTTP_REQUEST.value,
                position=[440, 300],
                parameters={
                    'url': target_url,
                    'options': {'timeout': 10000}
                }
            ),
            N8NNode(
                name='Extract Data',
                type=NodeType.CODE.value,
                position=[640, 300],
                parameters={
                    'jsCode': f'''
const cheerio = require('cheerio');
const $ = cheerio.load(items[0].json.body);
const result = $('{css_selector}').text();
return [{{json: {{extracted: result, url: '{target_url}', timestamp: new Date()}}}}];
'''
                }
            )
        ]

        workflow = N8NWorkflow(name=name, nodes=nodes)
        self._generate_connections(workflow)
        return workflow

    async def _create_api_monitor_template(self, name: str, **kwargs) -> N8NWorkflow:
        """Create API monitoring workflow template."""
        api_url = kwargs.get('api_url', 'https://api.example.com/health')

        nodes = [
            N8NNode(
                name='Monitor Schedule',
                type=NodeType.CRON.value,
                position=[240, 300],
                parameters={'rule': '*/5 * * * *'}  # Every 5 minutes
            ),
            N8NNode(
                name='Check API',
                type=NodeType.HTTP_REQUEST.value,
                position=[440, 300],
                parameters={
                    'url': api_url,
                    'options': {'timeout': 5000}
                }
            ),
            N8NNode(
                name='Check Status',
                type=NodeType.IF.value,
                position=[640, 300],
                parameters={
                    'conditions': {
                        'string': [
                            {
                                'value1': '={{$node["Check API"].json.status}}',
                                'operation': 'notEqual',
                                'value2': 'ok'
                            }
                        ]
                    }
                }
            )
        ]

        workflow = N8NWorkflow(name=name, nodes=nodes)
        self._generate_connections(workflow)
        return workflow

    async def _create_data_processor_template(self, name: str, **kwargs) -> N8NWorkflow:
        """Create data processing workflow template."""
        # Implementation for data processing workflow
        pass

    async def _create_notification_template(self, name: str, **kwargs) -> N8NWorkflow:
        """Create notification workflow template."""
        # Implementation for notification workflow
        pass

    async def _create_file_processor_template(self, name: str, **kwargs) -> N8NWorkflow:
        """Create file processing workflow template."""
        # Implementation for file processing workflow
        pass

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()


# Export N8N workflow manager
n8n_workflow_manager = N8NWorkflowManager()

async def initialize_n8n_integration(
    n8n_host: str = "http://localhost:5678",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Claude Code compatible N8N initialization function.

    Args:
        n8n_host: N8N instance host URL
        api_key: Optional API key for authentication

    Returns:
        N8N integration initialization result
    """
    global n8n_workflow_manager
    n8n_workflow_manager = N8NWorkflowManager(n8n_host, api_key)
    return await n8n_workflow_manager.initialize()

async def create_n8n_workflow(
    name: str,
    template: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Claude Code compatible N8N workflow creation function.

    Args:
        name: Workflow name
        template: Template to use
        **kwargs: Template parameters

    Returns:
        Workflow creation result
    """
    return await n8n_workflow_manager.create_workflow(name, template, **kwargs)

async def execute_n8n_workflow(
    workflow_id: str,
    input_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Claude Code compatible N8N workflow execution function.

    Args:
        workflow_id: ID of workflow to execute
        input_data: Optional input data

    Returns:
        Execution result
    """
    return await n8n_workflow_manager.execute_workflow(workflow_id, input_data)