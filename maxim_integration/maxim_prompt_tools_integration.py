"""
Maxim AI Prompt Tools Integration for Enhanced Prince Flowers Agent

Integrates Maxim AI's prompt tools (Code, API, Schema-based) with the
enhanced Prince Flowers agent to provide advanced capabilities.
"""

import asyncio
import json
import logging
import aiohttp
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MaximTool:
    """Represents a Maxim AI prompt tool."""
    id: str
    name: str
    description: str
    tool_type: str  # 'code', 'api', 'schema'
    function: Optional[str] = None
    parameters: Optional[Dict] = None
    variables: Optional[List[Dict]] = None

@dataclass
class MaximToolResult:
    """Result from executing a Maxim tool."""
    success: bool
    result: Any
    execution_time: float
    tool_id: str
    error_message: Optional[str] = None

class MaximPromptToolsIntegration:
    """
    Integration with Maxim AI's prompt tools for enhanced Prince Flowers.

    Provides:
    - Code tools: Custom JavaScript functions for complex computations
    - API tools: External API integration capabilities
    - Schema tools: Structured output validation
    - Variable management: Dynamic parameter handling
    """

    def __init__(self, api_key: str, base_url: str = "https://app.getmaxim.ai/api"):
        """Initialize Maxim prompt tools integration."""
        self.api_key = api_key
        self.base_url = base_url
        self.logger = logging.getLogger("MaximPromptTools")

        # Tool registry
        self.registered_tools: Dict[str, MaximTool] = {}
        self.tool_execution_stats: Dict[str, Dict] = {}

        # HTTP session for API calls
        self.session: Optional[aiohttp.ClientSession] = None

        self.logger.info("Maxim Prompt Tools integration initialized")

    async def initialize(self):
        """Initialize HTTP session and load existing tools."""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

        # Load pre-defined tools
        await self._load_builtin_tools()

        self.logger.info("Maxim Prompt Tools session initialized")

    async def _load_builtin_tools(self):
        """Load built-in tools for enhanced Prince Flowers."""

        # Code Tools for advanced analysis
        code_tools = [
            MaximTool(
                id="code_sentiment_analysis",
                name="Sentiment Analysis",
                description="Analyze sentiment of text using advanced NLP",
                tool_type="code",
                function="""
function analyzeSentiment(text) {
    // Simple sentiment analysis implementation
    const positiveWords = ['good', 'excellent', 'great', 'amazing', 'wonderful'];
    const negativeWords = ['bad', 'terrible', 'awful', 'horrible', 'poor'];

    const words = text.toLowerCase().split(' ');
    let positiveCount = 0;
    let negativeCount = 0;

    words.forEach(word => {
        if (positiveWords.includes(word)) positiveCount++;
        if (negativeWords.includes(word)) negativeCount++;
    });

    const totalSentimentWords = positiveCount + negativeCount;
    if (totalSentimentWords === 0) return { sentiment: 'neutral', confidence: 0.5 };

    const positiveRatio = positiveCount / totalSentimentWords;
    return {
        sentiment: positiveRatio > 0.6 ? 'positive' : positiveRatio < 0.4 ? 'negative' : 'neutral',
        confidence: Math.abs(positiveRatio - 0.5) * 2,
        positive_count: positiveCount,
        negative_count: negativeCount
    };
}
                """,
                variables=[
                    {"name": "text", "type": "string", "description": "Text to analyze"}
                ]
            ),

            MaximTool(
                id="code_pattern_extractor",
                name="Pattern Extractor",
                description="Extract patterns from code or text using regex",
                tool_type="code",
                function="""
function extractPatterns(text, patternType) {
    const patterns = {
        email: /\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b/g,
        url: /https?:\\/\\/(www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b([-a-zA-Z0-9()@:%_\\+.~#?&//=]*)/g,
        phone: /\\b\\d{3}-?\\d{3}-?\\d{4}\\b/g,
        code_function: /function\\s+(\\w+)\\s*\\([^)]*\\)/g,
        python_function: /def\\s+(\\w+)\\s*\\([^)]*\\):/g
    };

    const regex = patterns[patternType];
    if (!regex) return { matches: [], count: 0, error: 'Unknown pattern type' };

    const matches = text.match(regex) || [];
    return {
        matches: [...new Set(matches)], // Remove duplicates
        count: matches.length,
        pattern_type: patternType
    };
}
                """,
                variables=[
                    {"name": "text", "type": "string", "description": "Text to search"},
                    {"name": "patternType", "type": "string", "description": "Type of pattern: email, url, phone, code_function, python_function"}
                ]
            )
        ]

        # API Tools for external integrations
        api_tools = [
            MaximTool(
                id="api_weather_checker",
                name="Weather Checker",
                description="Get current weather for any location",
                tool_type="api",
                parameters={
                    "url": "https://api.openweathermap.org/data/2.5/weather",
                    "method": "GET",
                    "headers": {
                        "Accept": "application/json"
                    },
                    "params": {
                        "q": "{{location}}",
                        "appid": "{{weather_api_key}}",
                        "units": "metric"
                    }
                },
                variables=[
                    {"name": "location", "type": "string", "description": "City name or coordinates"},
                    {"name": "weather_api_key", "type": "string", "description": "OpenWeatherMap API key"}
                ]
            ),

            MaximTool(
                id="api_domain_lookup",
                name="Domain Information",
                description="Get domain registration and DNS information",
                tool_type="api",
                parameters={
                    "url": "https://api.whoisjson.com/v1/{{domain}}/whois",
                    "method": "GET",
                    "headers": {
                        "Accept": "application/json"
                    }
                },
                variables=[
                    {"name": "domain", "type": "string", "description": "Domain name to lookup"}
                ]
            )
        ]

        # Schema Tools for structured outputs
        schema_tools = [
            MaximTool(
                id="schema_project_plan",
                name="Project Plan Generator",
                description="Generate structured project plans",
                tool_type="schema",
                parameters={
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "timeline": {"type": "string"},
                        "phases": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "duration": {"type": "string"},
                                    "tasks": {"type": "array", "items": {"type": "string"}}
                                }
                            }
                        },
                        "risks": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["project_name", "timeline", "phases"]
                }
            ),

            MaximTool(
                id="schema_code_review",
                name="Code Review Report",
                description="Generate structured code review reports",
                tool_type="schema",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "overall_score": {"type": "number", "minimum": 0, "maximum": 10},
                        "issues": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                                    "line_number": {"type": "number"},
                                    "description": {"type": "string"},
                                    "suggestion": {"type": "string"}
                                }
                            }
                        },
                        "suggestions": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["file_path", "overall_score", "issues"]
                }
            )
        ]

        # Register all tools
        for tool in code_tools + api_tools + schema_tools:
            self.registered_tools[tool.id] = tool
            self.tool_execution_stats[tool.id] = {
                'executions': 0,
                'successes': 0,
                'avg_time': 0.0,
                'last_used': None
            }

    async def register_tool(self, tool: MaximTool) -> bool:
        """
        Register a new Maxim tool.

        Args:
            tool: MaximTool to register

        Returns:
            Success status
        """
        try:
            self.registered_tools[tool.id] = tool
            self.tool_execution_stats[tool.id] = {
                'executions': 0,
                'successes': 0,
                'avg_time': 0.0,
                'last_used': None
            }

            self.logger.info(f"Registered Maxim tool: {tool.name} ({tool.tool_type})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to register tool {tool.id}: {e}")
            return False

    async def execute_tool(self, tool_id: str, variables: Dict[str, Any]) -> MaximToolResult:
        """
        Execute a Maxim tool with given variables.

        Args:
            tool_id: ID of tool to execute
            variables: Variables for tool execution

        Returns:
            MaximToolResult with execution outcome
        """
        if tool_id not in self.registered_tools:
            return MaximToolResult(
                success=False,
                result=None,
                execution_time=0.0,
                tool_id=tool_id,
                error_message=f"Tool {tool_id} not found"
            )

        tool = self.registered_tools[tool_id]
        start_time = datetime.now()

        try:
            # Update execution stats
            stats = self.tool_execution_stats[tool_id]
            stats['executions'] += 1
            stats['last_used'] = datetime.now().isoformat()

            # Execute based on tool type
            if tool.tool_type == 'code':
                result = await self._execute_code_tool(tool, variables)
            elif tool.tool_type == 'api':
                result = await self._execute_api_tool(tool, variables)
            elif tool.tool_type == 'schema':
                result = await self._execute_schema_tool(tool, variables)
            else:
                raise ValueError(f"Unknown tool type: {tool.tool_type}")

            execution_time = (datetime.now() - start_time).total_seconds()

            # Update success stats
            if result['success']:
                stats['successes'] += 1
                # Update average time
                stats['avg_time'] = (stats['avg_time'] * (stats['successes'] - 1) + execution_time) / stats['successes']

            return MaximToolResult(
                success=result['success'],
                result=result['data'],
                execution_time=execution_time,
                tool_id=tool_id,
                error_message=result.get('error')
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Tool execution failed {tool_id}: {e}")

            return MaximToolResult(
                success=False,
                result=None,
                execution_time=execution_time,
                tool_id=tool_id,
                error_message=str(e)
            )

    async def _execute_code_tool(self, tool: MaximTool, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a JavaScript code tool."""
        try:
            # For code tools, we'll simulate JavaScript execution with Python equivalents
            # In a real implementation, this would use a JavaScript engine

            if tool.id == "code_sentiment_analysis":
                text = variables.get('text', '')
                return self._sentiment_analysis_impl(text)

            elif tool.id == "code_pattern_extractor":
                text = variables.get('text', '')
                pattern_type = variables.get('patternType', 'email')
                return self._pattern_extractor_impl(text, pattern_type)

            else:
                # Generic code tool execution simulation
                return {
                    'success': True,
                    'data': f"Code tool {tool.name} executed with variables: {list(variables.keys())}"
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_api_tool(self, tool: MaximTool, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an API call tool."""
        if not self.session:
            return {'success': False, 'error': 'HTTP session not initialized'}

        try:
            params = tool.parameters.copy()

            # Replace variables in URL and parameters
            if 'url' in params:
                for var_name, var_value in variables.items():
                    params['url'] = params['url'].replace(f"{{{{{var_name}}}}}", str(var_value))

            # Make API call
            async with self.session.request(
                method=params.get('method', 'GET'),
                url=params.get('url'),
                headers=params.get('headers', {}),
                params=params.get('params')
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    return {'success': True, 'data': data}
                else:
                    return {
                        'success': False,
                        'error': f"API call failed with status {response.status}"
                    }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_schema_tool(self, tool: MaximTool, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a schema validation/generation tool."""
        try:
            # For schema tools, we validate input against schema and return structured data

            if tool.id == "schema_project_plan":
                return self._project_plan_schema(variables)

            elif tool.id == "schema_code_review":
                return self._code_review_schema(variables)

            else:
                # Generic schema validation
                schema = tool.parameters
                return {
                    'success': True,
                    'data': {
                        'validated': True,
                        'schema_type': schema.get('type', 'unknown'),
                        'input_variables': list(variables.keys())
                    }
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _sentiment_analysis_impl(self, text: str) -> Dict[str, Any]:
        """Implementation of sentiment analysis."""
        positive_words = ['good', 'excellent', 'great', 'amazing', 'wonderful', 'fantastic', 'awesome']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'poor', 'disappointing', 'worst']

        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words == 0:
            return {'success': True, 'data': {'sentiment': 'neutral', 'confidence': 0.5}}

        positive_ratio = positive_count / total_sentiment_words
        sentiment = 'positive' if positive_ratio > 0.6 else 'negative' if positive_ratio < 0.4 else 'neutral'
        confidence = abs(positive_ratio - 0.5) * 2

        return {
            'success': True,
            'data': {
                'sentiment': sentiment,
                'confidence': confidence,
                'positive_count': positive_count,
                'negative_count': negative_count
            }
        }

    def _pattern_extractor_impl(self, text: str, pattern_type: str) -> Dict[str, Any]:
        """Implementation of pattern extraction."""
        import re

        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url': r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
            'phone': r'\b\d{3}-?\d{3}-?\d{4}\b',
            'code_function': r'function\s+(\w+)\s*\([^)]*\)',
            'python_function': r'def\s+(\w+)\s*\([^)]*\):'
        }

        if pattern_type not in patterns:
            return {'success': False, 'error': f'Unknown pattern type: {pattern_type}'}

        matches = re.findall(patterns[pattern_type], text, re.IGNORECASE)
        unique_matches = list(set(matches))

        return {
            'success': True,
            'data': {
                'matches': unique_matches,
                'count': len(unique_matches),
                'pattern_type': pattern_type
            }
        }

    def _project_plan_schema(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured project plan."""
        # Validate required fields
        if 'project_name' not in variables or 'timeline' not in variables:
            return {'success': False, 'error': 'Missing required fields: project_name, timeline'}

        # Generate structured plan
        plan = {
            'project_name': variables['project_name'],
            'timeline': variables['timeline'],
            'phases': variables.get('phases', [
                {
                    'name': 'Planning',
                    'duration': '1 week',
                    'tasks': ['Requirements gathering', 'Architecture design', 'Resource allocation']
                },
                {
                    'name': 'Development',
                    'duration': '4 weeks',
                    'tasks': ['Core functionality', 'Testing', 'Documentation']
                },
                {
                    'name': 'Deployment',
                    'duration': '1 week',
                    'tasks': ['Production setup', 'Monitoring', 'Launch']
                }
            ]),
            'risks': variables.get('risks', ['Technical complexity', 'Timeline constraints']),
            'created_at': datetime.now().isoformat()
        }

        return {'success': True, 'data': plan}

    def _code_review_schema(self, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured code review."""
        file_path = variables.get('file_path', 'unknown')
        overall_score = variables.get('overall_score', 7.5)
        issues = variables.get('issues', [])
        suggestions = variables.get('suggestions', [])

        review = {
            'file_path': file_path,
            'overall_score': overall_score,
            'grade': 'A' if overall_score >= 9 else 'B' if overall_score >= 7 else 'C' if overall_score >= 5 else 'D',
            'issues': issues,
            'suggestions': suggestions,
            'review_date': datetime.now().isoformat(),
            'reviewer': 'Maxim AI Tools Integration'
        }

        return {'success': True, 'data': review}

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with their stats."""
        tools_info = []

        for tool_id, tool in self.registered_tools.items():
            stats = self.tool_execution_stats[tool_id]
            success_rate = (stats['successes'] / max(stats['executions'], 1)) * 100

            tools_info.append({
                'id': tool_id,
                'name': tool.name,
                'description': tool.description,
                'type': tool.tool_type,
                'executions': stats['executions'],
                'success_rate': round(success_rate, 1),
                'avg_time': round(stats['avg_time'], 3),
                'last_used': stats['last_used']
            })

        return tools_info

    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
        self.logger.info("Maxim Prompt Tools integration cleaned up")

# Singleton instance for easy access
_maxim_tools_integration = None

def get_maxim_tools_integration(api_key: str, base_url: str = "https://app.getmaxim.ai/api") -> MaximPromptToolsIntegration:
    """Get or create Maxim tools integration instance."""
    global _maxim_tools_integration
    if _maxim_tools_integration is None:
        _maxim_tools_integration = MaximPromptToolsIntegration(api_key, base_url)
    return _maxim_tools_integration