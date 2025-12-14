"""
Integration Tools Module - Consolidated API and External Service Integrations

This module consolidates mcp_client_tool.py, n8n_workflow_tool.py,
twitter_posting_tool.py, and linkedin_posting_tool.py into a unified
integration framework.

Provides external API and service integration capabilities:
- Common HTTP API client base class
- Unified credential management
- Standardized error handling for external services
- MCP server connection management
- Social media API integrations (Twitter, LinkedIn)
- Workflow automation integrations (n8n)

Author: TORQ Console Development Team
Version: 2.0.0 (Consolidated)
"""

import logging
import json
import asyncio
import subprocess
import os
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# Try to import httpx for HTTP requests
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("httpx not installed. HTTP integrations unavailable. Install with: pip install httpx")

# Try to import tweepy for Twitter
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

# Try to import requests for LinkedIn
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Integration service status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMITED = "rate_limited"


class TransportType(Enum):
    """Transport types for external services."""
    HTTP = "http"
    MCP_STDIO = "mcp_stdio"
    MCP_HTTP = "mcp_http"
    API_DIRECT = "api_direct"


@dataclass
class Credential:
    """Standardized credential structure."""
    service_name: str
    credential_type: str  # api_key, oauth, token, etc.
    value: str
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationResult:
    """Standardized result for integration operations."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    status: IntegrationStatus = IntegrationStatus.CONNECTED
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class IntegrationError(Exception):
    """Base exception for integration errors."""
    pass


class AuthenticationError(IntegrationError):
    """Authentication related errors."""
    pass


class RateLimitError(IntegrationError):
    """Rate limiting errors."""
    pass


class ServiceUnavailableError(IntegrationError):
    """Service unavailable errors."""
    pass


class CredentialManager:
    """Manages secure credential storage and retrieval."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path.home() / '.torq' / 'credentials.json'
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.credentials: Dict[str, Credential] = {}
        self._load_credentials()

    def _load_credentials(self):
        """Load credentials from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for service, cred_data in data.items():
                        expires_at = None
                        if cred_data.get('expires_at'):
                            expires_at = datetime.fromisoformat(cred_data['expires_at'])

                        self.credentials[service] = Credential(
                            service_name=cred_data['service_name'],
                            credential_type=cred_data['credential_type'],
                            value=cred_data['value'],
                            expires_at=expires_at,
                            metadata=cred_data.get('metadata', {})
                        )
            except Exception as e:
                logger.error(f"Failed to load credentials: {e}")

    def _save_credentials(self):
        """Save credentials to storage."""
        try:
            data = {}
            for service, credential in self.credentials.items():
                data[service] = {
                    'service_name': credential.service_name,
                    'credential_type': credential.credential_type,
                    'value': credential.value,
                    'expires_at': credential.expires_at.isoformat() if credential.expires_at else None,
                    'metadata': credential.metadata
                }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")

    def store_credential(self, credential: Credential):
        """Store a credential."""
        self.credentials[credential.service_name] = credential
        self._save_credentials()

    def get_credential(self, service_name: str) -> Optional[Credential]:
        """Retrieve credential for service."""
        credential = self.credentials.get(service_name)

        # Check if credential has expired
        if credential and credential.expires_at and datetime.now() > credential.expires_at:
            logger.warning(f"Credential for {service_name} has expired")
            return None

        return credential

    def delete_credential(self, service_name: str) -> bool:
        """Delete credential for service."""
        if service_name in self.credentials:
            del self.credentials[service_name]
            self._save_credentials()
            return True
        return False


class BaseIntegrationClient(ABC):
    """Base class for all integration clients."""

    def __init__(self, service_name: str, credential_manager: CredentialManager):
        self.service_name = service_name
        self.credential_manager = credential_manager
        self.logger = logging.getLogger(f"torq.integrations.{service_name}")
        self.status = IntegrationStatus.DISCONNECTED

    @abstractmethod
    async def connect(self) -> IntegrationResult:
        """Connect to the service."""
        pass

    @abstractmethod
    async def disconnect(self) -> IntegrationResult:
        """Disconnect from the service."""
        pass

    @abstractmethod
    async def test_connection(self) -> IntegrationResult:
        """Test connection to the service."""
        pass

    def _get_credential(self) -> Optional[Credential]:
        """Get credentials for this service."""
        return self.credential_manager.get_credential(self.service_name)


class HTTPIntegrationClient(BaseIntegrationClient):
    """Base HTTP client for REST API integrations."""

    def __init__(self, service_name: str, credential_manager: CredentialManager, base_url: str):
        super().__init__(service_name, credential_manager)
        self.base_url = base_url.rstrip('/')
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> IntegrationResult:
        """Initialize HTTP client."""
        try:
            if not HTTPX_AVAILABLE:
                return IntegrationResult(
                    success=False,
                    error="httpx not available. Install with: pip install httpx",
                    status=IntegrationStatus.ERROR
                )

            # Configure headers based on credential type
            headers = {}
            credential = self._get_credential()
            if credential:
                if credential.credential_type == 'api_key':
                    headers['Authorization'] = f'Bearer {credential.value}'
                elif credential.credential_type == 'token':
                    headers['Authorization'] = f'Token {credential.value}'

            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0
            )

            # Test connection
            test_result = await self.test_connection()
            if test_result.success:
                self.status = IntegrationStatus.CONNECTED
            else:
                self.status = IntegrationStatus.ERROR

            return test_result

        except Exception as e:
            self.status = IntegrationStatus.ERROR
            return IntegrationResult(
                success=False,
                error=f"Failed to connect to {self.service_name}: {str(e)}",
                status=IntegrationStatus.ERROR
            )

    async def disconnect(self) -> IntegrationResult:
        """Close HTTP client."""
        try:
            if self.client:
                await self.client.aclose()
                self.client = None
            self.status = IntegrationStatus.DISCONNECTED
            return IntegrationResult(success=True, status=IntegrationStatus.DISCONNECTED)
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Failed to disconnect from {self.service_name}: {str(e)}"
            )

    async def test_connection(self) -> IntegrationResult:
        """Test connection with a simple request."""
        if not self.client:
            return IntegrationResult(
                success=False,
                error="Client not initialized",
                status=IntegrationStatus.DISCONNECTED
            )

        try:
            response = await self.client.get('/health')
            if response.status_code == 200:
                return IntegrationResult(success=True, status=IntegrationStatus.CONNECTED)
            else:
                return IntegrationResult(
                    success=False,
                    error=f"Health check failed: {response.status_code}",
                    status=IntegrationStatus.ERROR
                )
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Connection test failed: {str(e)}",
                status=IntegrationStatus.ERROR
            )

    async def make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> IntegrationResult:
        """Make HTTP request with error handling."""
        if not self.client:
            return IntegrationResult(
                success=False,
                error="Client not connected",
                status=IntegrationStatus.DISCONNECTED
            )

        try:
            response = await self.client.request(
                method.upper(),
                endpoint,
                json=data,
                params=params
            )

            # Handle different response codes
            if response.status_code == 401:
                self.status = IntegrationStatus.AUTHENTICATION_ERROR
                raise AuthenticationError("Authentication failed")
            elif response.status_code == 429:
                self.status = IntegrationStatus.RATE_LIMITED
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code >= 500:
                raise ServiceUnavailableError(f"Service error: {response.status_code}")

            response.raise_for_status()

            try:
                data = response.json()
            except:
                data = response.text

            return IntegrationResult(
                success=True,
                data=data,
                metadata={
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
            )

        except (AuthenticationError, RateLimitError, ServiceUnavailableError) as e:
            return IntegrationResult(
                success=False,
                error=str(e),
                status=self.status
            )
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Request failed: {str(e)}"
            )


class MCPServerClient(BaseIntegrationClient):
    """Client for MCP (Model Context Protocol) server connections."""

    def __init__(self, service_name: str, credential_manager: CredentialManager, server_config: Dict[str, Any]):
        super().__init__(service_name, credential_manager)
        self.server_config = server_config
        self.process: Optional[subprocess.Popen] = None
        self.transport_type = TransportType(server_config.get('transport', 'mcp_stdio'))
        self.request_id = 0

    async def connect(self) -> IntegrationResult:
        """Connect to MCP server."""
        try:
            command = self.server_config.get('command')
            if not command:
                return IntegrationResult(
                    success=False,
                    error="No command specified for MCP server",
                    status=IntegrationStatus.ERROR
                )

            # Start MCP server process
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Test connection with initialize request
            test_result = await self.test_connection()
            if test_result.success:
                self.status = IntegrationStatus.CONNECTED
            else:
                self.status = IntegrationStatus.ERROR

            return test_result

        except Exception as e:
            self.status = IntegrationStatus.ERROR
            return IntegrationResult(
                success=False,
                error=f"Failed to connect to MCP server {self.service_name}: {str(e)}",
                status=IntegrationStatus.ERROR
            )

    async def disconnect(self) -> IntegrationResult:
        """Disconnect from MCP server."""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                self.process = None
            self.status = IntegrationStatus.DISCONNECTED
            return IntegrationResult(success=True, status=IntegrationStatus.DISCONNECTED)
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Failed to disconnect from MCP server: {str(e)}"
            )

    async def test_connection(self) -> IntegrationResult:
        """Test MCP server connection."""
        if not self.process or self.process.poll() is not None:
            return IntegrationResult(
                success=False,
                error="MCP server process not running",
                status=IntegrationStatus.DISCONNECTED
            )

        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": self._get_request_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "TORQ Console",
                        "version": "2.0.0"
                    }
                }
            }

            response = await self._send_request(init_request)
            if response and 'result' in response:
                return IntegrationResult(success=True, status=IntegrationStatus.CONNECTED)
            else:
                return IntegrationResult(
                    success=False,
                    error="Invalid response from MCP server",
                    status=IntegrationStatus.ERROR
                )

        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"MCP server test failed: {str(e)}",
                status=IntegrationStatus.ERROR
            )

    def _get_request_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id

    async def _send_request(self, request: Dict) -> Optional[Dict]:
        """Send request to MCP server and wait for response."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            return None

        try:
            # Send request
            request_json = json.dumps(request) + '\n'
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())

        except Exception as e:
            self.logger.error(f"MCP request failed: {e}")

        return None

    async def list_tools(self) -> IntegrationResult:
        """List available tools from MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/list"
        }

        response = await self._send_request(request)
        if response and 'result' in response:
            return IntegrationResult(
                success=True,
                data=response['result'],
                status=self.status
            )
        else:
            return IntegrationResult(
                success=False,
                error="Failed to list tools",
                status=self.status
            )

    async def call_tool(self, tool_name: str, arguments: Dict) -> IntegrationResult:
        """Call a specific tool on the MCP server."""
        request = {
            "jsonrpc": "2.0",
            "id": self._get_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        response = await self._send_request(request)
        if response and 'result' in response:
            return IntegrationResult(
                success=True,
                data=response['result'],
                status=self.status
            )
        elif response and 'error' in response:
            return IntegrationResult(
                success=False,
                error=f"Tool call failed: {response['error']}",
                status=self.status
            )
        else:
            return IntegrationResult(
                success=False,
                error="Invalid response from MCP server",
                status=self.status
            )


class SocialMediaIntegration:
    """Consolidated social media integration client."""

    def __init__(self, credential_manager: CredentialManager):
        self.credential_manager = credential_manager
        self.twitter_client: Optional[TwitterIntegration] = None
        self.linkedin_client: Optional[LinkedInIntegration] = None

    async def initialize(self) -> IntegrationResult:
        """Initialize all social media clients."""
        results = {}

        # Initialize Twitter if available
        if TWEEPY_AVAILABLE:
            self.twitter_client = TwitterIntegration(self.credential_manager)
            results['twitter'] = await self.twitter_client.connect()

        # Initialize LinkedIn if available
        if REQUESTS_AVAILABLE:
            self.linkedin_client = LinkedInIntegration(self.credential_manager)
            results['linkedin'] = await self.linkedin_client.connect()

        return IntegrationResult(
            success=all(r.success for r in results.values()),
            data=results,
            metadata={'initialized_clients': list(results.keys())}
        )


class TwitterIntegration(HTTPIntegrationClient):
    """Twitter/X API integration."""

    def __init__(self, credential_manager: CredentialManager):
        super().__init__('twitter', credential_manager, 'https://api.twitter.com/2')

    async def test_connection(self) -> IntegrationResult:
        """Test Twitter API connection."""
        if not self.client:
            return IntegrationResult(
                success=False,
                error="Client not connected",
                status=IntegrationStatus.DISCONNECTED
            )

        try:
            response = await self.client.get('/users/me')
            if response.status_code == 200:
                return IntegrationResult(success=True, status=IntegrationStatus.CONNECTED)
            else:
                return IntegrationResult(
                    success=False,
                    error=f"Twitter API test failed: {response.status_code}",
                    status=IntegrationStatus.ERROR
                )
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Twitter API connection test failed: {str(e)}",
                status=IntegrationStatus.ERROR
            )

    async def post_tweet(self, text: str) -> IntegrationResult:
        """Post a tweet."""
        if not self.client:
            return IntegrationResult(
                success=False,
                error="Twitter client not connected",
                status=IntegrationStatus.DISCONNECTED
            )

        try:
            response = await self.client.post('/tweets', json={'text': text})

            if response.status_code == 201:
                data = response.json()
                return IntegrationResult(
                    success=True,
                    data=data,
                    metadata={'tweet_id': data.get('id')}
                )
            else:
                return IntegrationResult(
                    success=False,
                    error=f"Failed to post tweet: {response.status_code} - {response.text}"
                )

        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"Tweet posting failed: {str(e)}"
            )


class LinkedInIntegration(HTTPIntegrationClient):
    """LinkedIn API integration."""

    def __init__(self, credential_manager: CredentialManager):
        super().__init__('linkedin', credential_manager, 'https://api.linkedin.com/v2')

    async def test_connection(self) -> IntegrationResult:
        """Test LinkedIn API connection."""
        if not self.client:
            return IntegrationResult(
                success=False,
                error="Client not connected",
                status=IntegrationStatus.DISCONNECTED
            )

        try:
            response = await self.client.get('/people/~:(id,firstName,lastName)')
            if response.status_code == 200:
                return IntegrationResult(success=True, status=IntegrationStatus.CONNECTED)
            else:
                return IntegrationResult(
                    success=False,
                    error=f"LinkedIn API test failed: {response.status_code}",
                    status=IntegrationStatus.ERROR
                )
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"LinkedIn API connection test failed: {str(e)}",
                status=IntegrationStatus.ERROR
            )

    async def post_update(self, text: str) -> IntegrationResult:
        """Post a LinkedIn update."""
        if not self.client:
            return IntegrationResult(
                success=False,
                error="LinkedIn client not connected",
                status=IntegrationStatus.DISCONNECTED
            )

        try:
            # Get person ID first
            profile_response = await self.client.get('/people/~:(id)')
            if profile_response.status_code != 200:
                return IntegrationResult(
                    success=False,
                    error="Failed to get LinkedIn profile ID"
                )

            person_id = profile_response.json().get('id')

            # Post update
            post_data = {
                'author': f'urn:li:person:{person_id}',
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {
                            'text': text
                        },
                        'shareMediaCategory': 'NONE'
                    }
                },
                'visibility': {
                    'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'
                }
            }

            response = await self.client.post('/ugcPosts', json=post_data)

            if response.status_code == 201:
                data = response.json()
                return IntegrationResult(
                    success=True,
                    data=data,
                    metadata={'post_id': data.get('id')}
                )
            else:
                return IntegrationResult(
                    success=False,
                    error=f"Failed to post LinkedIn update: {response.status_code} - {response.text}"
                )

        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"LinkedIn update posting failed: {str(e)}"
            )


class N8NIntegration(HTTPIntegrationClient):
    """n8n workflow automation integration."""

    def __init__(self, credential_manager: CredentialManager, base_url: str = 'http://localhost:5678'):
        super().__init__('n8n', credential_manager, base_url)

    async def test_connection(self) -> IntegrationResult:
        """Test n8n connection."""
        if not self.client:
            return IntegrationResult(
                success=False,
                error="Client not connected",
                status=IntegrationStatus.DISCONNECTED
            )

        try:
            response = await self.client.get('/rest/active-workflows')
            if response.status_code == 200:
                return IntegrationResult(success=True, status=IntegrationStatus.CONNECTED)
            else:
                return IntegrationResult(
                    success=False,
                    error=f"n8n test failed: {response.status_code}",
                    status=IntegrationStatus.ERROR
                )
        except Exception as e:
            return IntegrationResult(
                success=False,
                error=f"n8n connection test failed: {str(e)}",
                status=IntegrationStatus.ERROR
            )

    async def list_workflows(self) -> IntegrationResult:
        """List all available workflows."""
        return await self.make_request('GET', '/rest/workflows')

    async def trigger_workflow(self, workflow_id: str, data: Optional[Dict] = None) -> IntegrationResult:
        """Trigger a workflow execution."""
        return await self.make_request(
            'POST',
            f'/rest/workflows/{workflow_id}/execute',
            data=data or {}
        )

    async def get_execution_status(self, execution_id: str) -> IntegrationResult:
        """Get status of a workflow execution."""
        return await self.make_request('GET', f'/rest/executions/{execution_id}')


class IntegrationManager:
    """Main manager for all integration tools."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.credential_manager = CredentialManager(storage_path)
        self.clients: Dict[str, BaseIntegrationClient] = {}
        self.logger = logging.getLogger(__name__)

    async def initialize(self) -> IntegrationResult:
        """Initialize all integration clients."""
        # Initialize social media integrations
        social_media = SocialMediaIntegration(self.credential_manager)
        result = await social_media.initialize()

        # Store initialized clients
        if social_media.twitter_client:
            self.clients['twitter'] = social_media.twitter_client
        if social_media.linkedin_client:
            self.clients['linkedin'] = social_media.linkedin_client

        return result

    async def add_mcp_server(self, service_name: str, server_config: Dict[str, Any]) -> IntegrationResult:
        """Add and connect to an MCP server."""
        client = MCPServerClient(service_name, self.credential_manager, server_config)
        result = await client.connect()

        if result.success:
            self.clients[service_name] = client

        return result

    async def add_n8n_integration(self, base_url: str = 'http://localhost:5678') -> IntegrationResult:
        """Add n8n integration."""
        client = N8NIntegration(self.credential_manager, base_url)
        result = await client.connect()

        if result.success:
            self.clients['n8n'] = client

        return result

    def get_client(self, service_name: str) -> Optional[BaseIntegrationClient]:
        """Get integration client by service name."""
        return self.clients.get(service_name)

    async def check_all_connections(self) -> Dict[str, IntegrationResult]:
        """Check status of all connected services."""
        results = {}

        for service_name, client in self.clients.items():
            results[service_name] = await client.test_connection()

        return results


# Factory function for easy initialization
def create_integration_manager(storage_path: Optional[Path] = None) -> IntegrationManager:
    """Create and return an integration manager instance."""
    return IntegrationManager(storage_path)


# Export main classes and functions
__all__ = [
    'IntegrationManager',
    'CredentialManager',
    'BaseIntegrationClient',
    'HTTPIntegrationClient',
    'MCPServerClient',
    'TwitterIntegration',
    'LinkedInIntegration',
    'N8NIntegration',
    'SocialMediaIntegration',
    'IntegrationResult',
    'IntegrationStatus',
    'TransportType',
    'Credential',
    'IntegrationError',
    'AuthenticationError',
    'RateLimitError',
    'ServiceUnavailableError',
    'create_integration_manager'
]