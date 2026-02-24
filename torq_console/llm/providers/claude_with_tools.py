"""
Claude Provider with Tool Use Support for TORQ Console.

This provider extends the base Claude provider with:
- Anthropic's Tool Use API for web browsing
- Integration with Tavily and Brave Search APIs
- Real-time web research capabilities
- Support for Claude's Computer Use API

Based on Anthropic's Claude API with tools:
https://docs.anthropic.com/claude/docs/tool-use
"""

import os
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from anthropic import Anthropic, AsyncAnthropic

from .base import BaseLLMProvider
from .claude import ClaudeProvider

# Import typed exceptions for proper error classification
from torq_console.ui.web_ai_fix import AIResponseError, AITimeoutError, ProviderError


def _is_policy_violation(error: Exception) -> bool:
    """
    Detect if an Anthropic error represents a content policy/safety violation.
    """
    error_str = str(error).lower()
    policy_markers = [
        "content policy",
        "safety",
        "against our policies",
        "policy violation",
        "inappropriate content",
        "safety guidelines",
        "violates content policy",
    ]
    return any(marker in error_str for marker in policy_markers)


class ClaudeToolUseProvider(ClaudeProvider):
    """
    Extended Claude provider with Tool Use API support.

    This provider enables Claude to use tools for:
    - Web search and research
    - Information retrieval
    - Computer use for browsing (when enabled)

    Tool Use allows Claude to interact with external APIs and services
    to perform actions beyond text generation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Claude provider with tool use support.

        Args:
            config: Configuration dict with api_key, model, and tool settings
        """
        super().__init__(config)

        # Tool use configuration
        self.tool_use_enabled = self.config.get('tool_use_enabled', True)
        self.computer_use_enabled = self.config.get('computer_use_enabled', False)
        self.max_tool_iterations = self.config.get('max_tool_iterations', 10)

        # Import enhanced web search
        try:
            from torq_console.agents.torq_prince_flowers.tools.websearch_enhanced import (
                create_enhanced_web_search_tool
            )
            self.web_search_tool = create_enhanced_web_search_tool()
            self.web_search_available = True
            self.logger.info("Enhanced web search tool available")
        except ImportError:
            self.web_search_tool = None
            self.web_search_available = False
            self.logger.warning("Enhanced web search tool not available")

        # Define available tools
        self.tools = self._define_tools()
        self._in_research_mode = False  # Flag to prevent recursive searches

        self.logger.info(f"Claude Tool Use provider initialized (tools: {len(self.tools)})")

    def _define_tools(self) -> List[Dict[str, Any]]:
        """
        Define the tools available to Claude.

        Returns:
            List of tool definitions in Anthropic's format
        """
        tools = []

        # Web Search Tool
        if self.web_search_available:
            tools.append({
                "name": "web_search",
                "description": (
                    "Search the web for current information. "
                    "Use this when you need up-to-date information, facts, current events, "
                    "or information the user says is recent. "
                    "Returns relevant web pages with snippets and URLs."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to look up"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            })

        # News Search Tool
        if self.web_search_available:
            tools.append({
                "name": "news_search",
                "description": (
                    "Search for recent news articles. "
                    "Use this when the user asks about current events, breaking news, "
                    "or recent developments."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The news search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10
                        }
                    },
                    "required": ["query"]
                }
            })

        return tools

    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool call.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            Tool result as a string
        """
        try:
            if tool_name == "web_search":
                return await self._execute_web_search(tool_input)
            elif tool_name == "news_search":
                return await self._execute_news_search(tool_input)
            else:
                return f"Error: Unknown tool '{tool_name}'"

        except Exception as e:
            self.logger.error(f"Tool execution failed for '{tool_name}': {e}")
            return f"Error executing {tool_name}: {str(e)}"

    async def _execute_web_search(self, params: Dict[str, Any]) -> str:
        """Execute web search with the given parameters."""
        if not self.web_search_tool:
            return "Error: Web search tool not available"

        query = params.get("query", "")
        max_results = params.get("max_results", 10)

        results = await self.web_search_tool.search(
            query=query,
            max_results=max_results
        )

        # Format results for Claude
        formatted = f"Web search results for '{query}':\n\n"

        for i, result in enumerate(results[:10], 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            snippet = result.get("snippet", "No description")
            source = result.get("source", "unknown")

            formatted += f"{i}. {title}\n"
            formatted += f"   Source: {source}\n"
            if url:
                formatted += f"   URL: {url}\n"
            formatted += f"   {snippet[:500]}\n\n"

        return formatted

    async def _execute_news_search(self, params: Dict[str, Any]) -> str:
        """Execute news search with the given parameters."""
        if not self.web_search_tool:
            return "Error: News search tool not available"

        query = params.get("query", "")
        max_results = params.get("max_results", 10)

        results = await self.web_search_tool.news_search(
            query=query,
            max_results=max_results
        )

        # Format results for Claude
        formatted = f"News search results for '{query}':\n\n"

        for i, result in enumerate(results[:10], 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            snippet = result.get("snippet", "No description")
            published = result.get("published_date", "Unknown date")

            formatted += f"{i}. {title}\n"
            formatted += f"   Published: {published}\n"
            if url:
                formatted += f"   URL: {url}\n"
            formatted += f"   {snippet[:500]}\n\n"

        return formatted

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        system_message: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Chat with Claude using Tool Use API.

        This method enables Claude to use tools during the conversation.
        It handles the tool use loop automatically.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_message: Optional system message
            **kwargs: Additional parameters

        Returns:
            The final response string
        """
        if not self.is_configured():
            raise ProviderError("Claude provider not configured (missing API key)", code="401")

        if not self.tool_use_enabled or not self.tools:
            # Fall back to regular chat without tools
            return await self.chat(messages, system_message, **kwargs)

        try:
            # System prompt with tool use instructions
            base_system = system_message or "You are Claude, a helpful AI assistant with web research capabilities."
            tool_system = base_system + "\n\nYou have access to web search tools. Use them when you need current information or facts."

            # Initialize conversation
            current_messages = []

            # Format messages for Claude
            for msg in messages:
                if msg.get('role') in ['user', 'assistant']:
                    current_messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })

            # Tool use loop
            max_iterations = self.max_tool_iterations
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # Call Claude API
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=kwargs.get('max_tokens', 4096),
                    temperature=kwargs.get('temperature', 0.7),
                    system=tool_system,
                    messages=current_messages,
                    tools=self.tools if iteration == 1 else []
                )

                # Process response
                assistant_message = {"role": "assistant", "content": []}
                tool_use_blocks = []
                text_content = []

                for block in response.content:
                    block_type = block.type if hasattr(block, 'type') else block.__class__.__name__

                    if block_type == "tool_use" or block.__class__.__name__ == "ToolUseBlock":
                        tool_use_blocks.append(block)
                        assistant_message["content"].append({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": block.input
                        })
                    else:
                        text = block.text if hasattr(block, 'text') else str(block)
                        text_content.append(text)
                        assistant_message["content"].append({"type": "text", "text": text})

                current_messages.append(assistant_message)

                # If no tool use, we're done
                if not tool_use_blocks:
                    return "".join(text_content)

                # Execute each tool use
                for tool_block in tool_use_blocks:
                    tool_result = await self._execute_tool(tool_block.name, tool_block.input)

                    current_messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_block.id,
                                "content": tool_result
                            }
                        ]
                    })

            # Max iterations reached - return last response
            return "I reached the maximum number of tool iterations. Please try a more specific query."

        except asyncio.TimeoutError:
            self.logger.error("Claude chat with tools timed out")
            raise AITimeoutError("Claude request timed out")
        except Exception as e:
            if _is_policy_violation(e):
                self.logger.error(f"Content policy violation: {e}")
                raise AIResponseError(
                    f"Content policy violation: {str(e)}",
                    error_category="ai_error"
                )

            if hasattr(e, 'status_code'):
                status = e.status_code
                if status == 429:
                    raise ProviderError(f"Rate limited: {str(e)}", code="429")
                elif status >= 500:
                    raise ProviderError(f"Server error: {str(e)}", code=str(status))
                elif status in [400, 401, 403, 404]:
                    raise ProviderError(f"Provider error: {str(e)}", code=str(status))

            raise ProviderError(f"Claude adapter exception: {str(e)}")

    async def research_mode(
        self,
        query: str,
        context: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Execute a research query with automatic web search tool use.

        This method is optimized for research queries and will
        automatically use web search to find current information.

        Args:
            query: The research query
            context: Optional context to guide the research
            **kwargs: Additional parameters

        Returns:
            Comprehensive research response
        """
        # Instead of using Tool Use API (which has compatibility issues),
        # we'll manually perform web search and then query Claude
        if self.web_search_available:
            search_results = await self.web_search_tool.search(
                query=query,
                max_results=10
            )

            # Build context with search results (truncated to avoid issues)
            context_parts = []
            context_parts.append(f"Web search results for '{query}':\n")

            for i, result in enumerate(search_results[:5], 1):  # Limit to 5 results
                title = result.get("title", "No title")
                snippet = result.get("snippet", "No description")
                source = result.get("source", "unknown")

                context_parts.append(f"{i}. {title}")
                context_parts.append(f"   [{source}] {snippet[:200]}")

            context_text = "\n".join(context_parts)

            # Query Claude with search results using base class method directly
            research_prompt = f"""Research Question: {query}

Search Results:
{context_text}

Based on these search results, please provide:
1. A direct answer to the question
2. Key points from the search results
3. Sources for your information

Be concise and cite your sources."""

            # Use base class's query method to avoid recursive search
            self._in_research_mode = True
            try:
                response = await super().query(research_prompt, **kwargs)
            finally:
                self._in_research_mode = False

            return response
        else:
            # Fallback to regular query
            system_message = """You are a research assistant. When asked about current events or facts,
provide accurate information based on your training data, but acknowledge any limitations
regarding very recent information."""

            messages = [{"role": "user", "content": f"Research this topic: {query}"}]
            if context:
                messages[0]["content"] += f"\n\nContext: {context}"

            return await self.chat(messages, system_message, **kwargs)

    async def query(self, prompt: str, **kwargs) -> str:
        """
        Execute a query with automatic tool use if needed.

        Args:
            prompt: The query prompt
            **kwargs: Additional parameters

        Returns:
            The response string
        """
        # Skip search detection if we're already in research mode
        if self._in_research_mode:
            return await super().query(prompt, **kwargs)

        # Detect if this query needs web search
        needs_search = self._detect_search_need(prompt)

        if needs_search and self.web_search_available:
            # Use research mode which performs search then queries Claude
            return await self.research_mode(prompt, **kwargs)
        else:
            # Use regular query without tools
            return await super().query(prompt, **kwargs)

    def _detect_search_need(self, prompt: str) -> bool:
        """
        Detect if a prompt needs web search.

        Returns True if the prompt asks for:
        - Current events or recent information
        - Latest facts or data
        - Real-time information
        - Recent developments
        """
        search_keywords = [
            "latest", "recent", "current", "breaking", "news",
            "today", "this week", "this month", "this year",
            "price", "stock", "weather", "forecast",
            "what are the", "search for", "find", "look up",
            "status", "update", "happening now", "trends"
        ]

        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in search_keywords)

    async def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response with tool use support.

        Args:
            prompt: The input prompt
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        return await self.query(prompt, **kwargs)

    def get_tool_status(self) -> Dict[str, Any]:
        """Get status of available tools."""
        return {
            "tool_use_enabled": self.tool_use_enabled,
            "computer_use_enabled": self.computer_use_enabled,
            "available_tools": [t["name"] for t in self.tools],
            "web_search_available": self.web_search_available,
            "tools_count": len(self.tools)
        }


def create_claude_tool_use_provider(config: Dict[str, Any] = None) -> ClaudeToolUseProvider:
    """
    Convenience function to create a Claude provider with tool use support.

    Args:
        config: Configuration dictionary

    Returns:
        Configured ClaudeToolUseProvider instance
    """
    # Get API key from environment if not in config
    if config is None:
        config = {}

    if 'api_key' not in config:
        config['api_key'] = os.getenv('ANTHROPIC_API_KEY')

    if 'model' not in config:
        config['model'] = 'claude-sonnet-4-6'

    return ClaudeToolUseProvider(config)
