"""
MCP Manager for handling multiple MCP connections.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from ..core.config import TorqConfig, MCPEndpoint
from .client import MCPClient, MCPTool


logger = logging.getLogger(__name__)


class MCPManager:
    """Manager for multiple MCP connections."""
    
    def __init__(self, config: TorqConfig):
        self.config = config
        self.clients: Dict[str, MCPClient] = {}
        self.active_endpoints: List[str] = []
        
    async def initialize(self) -> None:
        """Initialize MCP connections."""
        logger.info("Initializing MCP connections...")
        
        for endpoint in self.config.mcp_endpoints:
            if endpoint.enabled:
                try:
                    await self.connect_endpoint_config(endpoint)
                except Exception as e:
                    logger.error(f"Failed to connect to {endpoint.name}: {e}")
        
        logger.info(f"MCP initialization complete. Active endpoints: {len(self.active_endpoints)}")
    
    async def connect_endpoint_config(self, endpoint: MCPEndpoint) -> bool:
        """Connect to an MCP endpoint using configuration."""
        client = MCPClient(endpoint.url, endpoint.token)
        
        if await client.connect():
            self.clients[endpoint.name] = client
            self.active_endpoints.append(endpoint.name)
            return True
        return False
    
    async def connect_endpoint(self, endpoint_url: str, auth_token: Optional[str] = None) -> bool:
        """Connect to an MCP endpoint by URL."""
        # Extract name from URL for identification
        endpoint_name = endpoint_url.split("/")[-1] or "custom"
        
        client = MCPClient(endpoint_url, auth_token)
        
        if await client.connect():
            self.clients[endpoint_name] = client
            if endpoint_name not in self.active_endpoints:
                self.active_endpoints.append(endpoint_name)
            return True
        return False
    
    async def disconnect_endpoint(self, endpoint_name: str) -> None:
        """Disconnect from an MCP endpoint."""
        if endpoint_name in self.clients:
            await self.clients[endpoint_name].disconnect()
            del self.clients[endpoint_name]
            if endpoint_name in self.active_endpoints:
                self.active_endpoints.remove(endpoint_name)
    
    async def shutdown(self) -> None:
        """Shutdown all MCP connections."""
        logger.info("Shutting down MCP connections...")
        
        for client in self.clients.values():
            await client.disconnect()
        
        self.clients.clear()
        self.active_endpoints.clear()
        
        logger.info("MCP shutdown complete")
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools from all connected endpoints."""
        all_tools = []
        
        for endpoint_name, client in self.clients.items():
            if client.is_connected():
                for tool in client.get_available_tools():
                    all_tools.append({
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.input_schema,
                        "endpoint": endpoint_name,
                    })
        
        return all_tools
    
    async def call_tool(self, tool_name: str, endpoint_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Call an MCP tool."""
        if endpoint_name:
            # Call tool on specific endpoint
            if endpoint_name not in self.clients:
                raise ValueError(f"Endpoint {endpoint_name} not connected")
            
            client = self.clients[endpoint_name]
            if not client.is_connected():
                raise RuntimeError(f"Endpoint {endpoint_name} not connected")
            
            return await client.call_tool(tool_name, kwargs)
        else:
            # Find tool across all endpoints
            for endpoint_name, client in self.clients.items():
                if client.is_connected():
                    for tool in client.get_available_tools():
                        if tool.name == tool_name:
                            return await client.call_tool(tool_name, kwargs)
            
            raise ValueError(f"Tool {tool_name} not found in any connected endpoint")
    
    async def read_resource(self, uri: str, endpoint_name: Optional[str] = None) -> Dict[str, Any]:
        """Read a resource from MCP."""
        if endpoint_name:
            # Read from specific endpoint
            if endpoint_name not in self.clients:
                raise ValueError(f"Endpoint {endpoint_name} not connected")
            
            client = self.clients[endpoint_name]
            return await client.read_resource(uri)
        else:
            # Try all endpoints until one succeeds
            for client in self.clients.values():
                if client.is_connected():
                    try:
                        return await client.read_resource(uri)
                    except Exception:
                        continue
            
            raise ValueError(f"Resource {uri} not found in any connected endpoint")
    
    async def get_prompt(self, name: str, endpoint_name: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get a prompt from MCP."""
        if endpoint_name:
            # Get from specific endpoint
            if endpoint_name not in self.clients:
                raise ValueError(f"Endpoint {endpoint_name} not connected")
            
            client = self.clients[endpoint_name]
            return await client.get_prompt(name, kwargs)
        else:
            # Find prompt across all endpoints
            for client in self.clients.values():
                if client.is_connected():
                    for prompt in client.get_available_prompts():
                        if prompt.name == name:
                            return await client.get_prompt(name, kwargs)
            
            raise ValueError(f"Prompt {name} not found in any connected endpoint")
    
    def get_active_endpoints(self) -> List[str]:
        """Get list of active endpoint names."""
        return self.active_endpoints.copy()
    
    def is_connected(self) -> bool:
        """Check if any endpoints are connected."""
        return len(self.active_endpoints) > 0
    
    def get_endpoint_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all endpoints."""
        status = {}
        
        for endpoint_name, client in self.clients.items():
            status[endpoint_name] = {
                "connected": client.is_connected(),
                "tools_count": len(client.get_available_tools()),
                "resources_count": len(client.get_available_resources()),
                "prompts_count": len(client.get_available_prompts()),
                "endpoint_url": client.endpoint_url,
            }
        
        return status