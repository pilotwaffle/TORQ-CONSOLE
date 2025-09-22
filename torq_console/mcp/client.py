"""
Model Context Protocol (MCP) client implementation.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel


logger = logging.getLogger(__name__)


class JSONRPCRequest:
    """Simple JSON-RPC request builder."""
    
    def __init__(self):
        self.id_counter = 0
    
    def request(self, method: str, params: Dict[str, Any]) -> str:
        """Build a JSON-RPC request."""
        self.id_counter += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": method,
            "params": params
        }
        return json.dumps(request)


class MCPTool(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    

class MCPResource(BaseModel):
    """MCP resource definition."""
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class MCPPrompt(BaseModel):
    """MCP prompt definition."""
    name: str
    description: Optional[str] = None
    arguments: List[Dict[str, Any]] = []


class MCPClient:
    """MCP client for communicating with MCP servers."""
    
    def __init__(self, endpoint_url: str, auth_token: Optional[str] = None):
        self.endpoint_url = endpoint_url
        self.auth_token = auth_token
        self.session: Optional[httpx.AsyncClient] = None
        self.protocol = JSONRPCRequest()
        self.connected = False
        
        # Cached data
        self.tools: List[MCPTool] = []
        self.resources: List[MCPResource] = []
        self.prompts: List[MCPPrompt] = []
        
        logger.info(f"MCP client created for endpoint: {endpoint_url}")
    
    async def connect(self) -> bool:
        """Connect to the MCP server."""
        try:
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            self.session = httpx.AsyncClient(
                timeout=30.0,
                headers=headers,
            )
            
            # Initialize the connection
            init_request = self.protocol.request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                    "prompts": {},
                },
                "clientInfo": {
                    "name": "torq-console",
                    "version": "0.60.0",
                }
            })
            
            response = await self._send_request(init_request)
            if response.get("result"):
                self.connected = True
                await self._load_capabilities()
                logger.info(f"Connected to MCP server: {self.endpoint_url}")
                return True
            else:
                logger.error(f"Failed to initialize MCP connection: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.session:
            await self.session.aclose()
            self.session = None
        self.connected = False
        logger.info("Disconnected from MCP server")
    
    async def _send_request(self, request: str) -> Dict[str, Any]:
        """Send a JSON-RPC request to the server."""
        if not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            response = await self.session.post(
                self.endpoint_url,
                content=request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send MCP request: {e}")
            raise
    
    async def _load_capabilities(self) -> None:
        """Load server capabilities (tools, resources, prompts)."""
        try:
            # Load tools
            tools_request = self.protocol.request("tools/list", {})
            tools_response = await self._send_request(tools_request)
            if tools_response.get("result", {}).get("tools"):
                self.tools = [
                    MCPTool(**tool) 
                    for tool in tools_response["result"]["tools"]
                ]
            
            # Load resources
            resources_request = self.protocol.request("resources/list", {})
            resources_response = await self._send_request(resources_request)
            if resources_response.get("result", {}).get("resources"):
                self.resources = [
                    MCPResource(**resource)
                    for resource in resources_response["result"]["resources"]
                ]
            
            # Load prompts
            prompts_request = self.protocol.request("prompts/list", {})
            prompts_response = await self._send_request(prompts_request)
            if prompts_response.get("result", {}).get("prompts"):
                self.prompts = [
                    MCPPrompt(**prompt)
                    for prompt in prompts_response["result"]["prompts"]
                ]
            
            logger.info(f"Loaded {len(self.tools)} tools, {len(self.resources)} resources, {len(self.prompts)} prompts")
            
        except Exception as e:
            logger.error(f"Failed to load MCP capabilities: {e}")
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool."""
        if not self.connected:
            raise RuntimeError("Not connected to MCP server")
        
        tool_request = self.protocol.request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        
        try:
            response = await self._send_request(tool_request)
            if "result" in response:
                return response["result"]
            else:
                raise RuntimeError(f"Tool call failed: {response.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Failed to call tool {name}: {e}")
            raise
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read an MCP resource."""
        if not self.connected:
            raise RuntimeError("Not connected to MCP server")
        
        resource_request = self.protocol.request("resources/read", {
            "uri": uri
        })
        
        try:
            response = await self._send_request(resource_request)
            if "result" in response:
                return response["result"]
            else:
                raise RuntimeError(f"Resource read failed: {response.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Failed to read resource {uri}: {e}")
            raise
    
    async def get_prompt(self, name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get an MCP prompt."""
        if not self.connected:
            raise RuntimeError("Not connected to MCP server")
        
        prompt_request = self.protocol.request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        
        try:
            response = await self._send_request(prompt_request)
            if "result" in response:
                return response["result"]
            else:
                raise RuntimeError(f"Prompt get failed: {response.get('error', 'Unknown error')}")
        except Exception as e:
            logger.error(f"Failed to get prompt {name}: {e}")
            raise
    
    def get_available_tools(self) -> List[MCPTool]:
        """Get list of available tools."""
        return self.tools
    
    def get_available_resources(self) -> List[MCPResource]:
        """Get list of available resources."""
        return self.resources
    
    def get_available_prompts(self) -> List[MCPPrompt]:
        """Get list of available prompts."""
        return self.prompts
    
    def is_connected(self) -> bool:
        """Check if connected to the server."""
        return self.connected