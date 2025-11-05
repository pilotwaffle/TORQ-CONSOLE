"""
Prince Flowers Enhanced Integration for TORQ Console

Integrates the advanced capabilities from prince_flowers_enhanced.py into TORQ Console:
- Enhanced meta-planning with 7 planning strategies
- Comprehensive tool ecosystem (core + Claude + MCP tools)
- Advanced query routing with search vs code generation detection
- Browser automation workflows
- Research and file operation workflows
- Adaptive learning from tool usage patterns
- Enhanced memory consolidation

This module provides the ultimate agentic RL agent for TORQ Console with full
MCP and tool integration capabilities from prince_flowers_enhanced.py.
"""

import asyncio
import logging
import time
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import deque

from ..llm.providers.base import BaseLLMProvider
from .torq_search_master import create_search_master
from .intent_detector import create_intent_detector

@dataclass
class PlanStep:
    """Enhanced plan step with tool requirements."""
    action: str
    description: str
    expected_outcome: str
    confidence: float
    tools_required: List[str] = None
    estimated_time: float = 1.0

@dataclass
class ToolResult:
    """Enhanced tool execution result."""
    success: bool
    result: Any
    execution_time: float
    error_message: Optional[str] = None
    tool_name: str = ""
    confidence: float = 0.5

@dataclass
class EnhancedAgentResult:
    """Enhanced agent result with comprehensive metadata."""
    success: bool
    content: str
    confidence: float
    tools_used: List[str]
    tool_categories: List[str]
    execution_time: float
    planning_strategy: str
    workflow_type: Optional[str] = None
    browser_actions: List[Dict] = None
    mcp_interactions: List[str] = None
    learning_triggered: bool = False
    metadata: Dict[str, Any] = None

class PrinceFlowersEnhancedIntegration:
    """
    Prince Flowers Enhanced Integration for TORQ Console.

    Provides the ultimate agentic RL agent with:
    - Advanced meta-planning (7 strategies)
    - Comprehensive tool ecosystem
    - Enhanced query routing (search vs code detection)
    - Browser automation workflows
    - Adaptive learning and memory consolidation
    - Full MCP integration
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        """Initialize enhanced Prince Flowers agent."""
        self.agent_name = "Prince Flowers Enhanced"
        self.agent_id = "prince_flowers_enhanced"
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(f"PrinceFlowers.Enhanced")

        # Initialize all systems
        self._init_enhanced_planning_system()
        self._init_enhanced_tool_system()
        self._init_enhanced_memory_system()
        self._init_enhanced_learning_system()
        self._init_query_router()

        # Performance tracking
        self.active_since = time.time()
        self.total_interactions = 0
        self.successful_completions = 0

        self.logger.info(f"{self.agent_name} initialized with full MCP & tool ecosystem")

    def _init_enhanced_planning_system(self):
        """Initialize enhanced meta-planning with 7 strategies."""
        self.planning = {
            'max_depth': 7,
            'strategies': [
                'direct', 'linear_chain', 'tree_search', 'conditional',
                'parallel', 'adaptive', 'mcp_integrated',
                'browser_workflow', 'research_workflow', 'file_workflow'
            ],
            'strategy_success_rates': {
                'direct': 0.7,
                'linear_chain': 0.75,
                'tree_search': 0.65,
                'conditional': 0.7,
                'parallel': 0.6,
                'adaptive': 0.8,
                'mcp_integrated': 0.75,
                'browser_workflow': 0.7,
                'research_workflow': 0.85,
                'file_workflow': 0.8
            },
            'depth_success_rates': {i: 0.5 for i in range(1, 8)},
            'tool_combinations': {},
            'workflow_patterns': {}
        }

        self.logger.info(f"Enhanced planning initialized with {len(self.planning['strategies'])} strategies")

    def _init_enhanced_tool_system(self):
        """Initialize comprehensive tool ecosystem."""
        # Core computation tools
        self.core_tools = {
            'calculator': 'Mathematical calculations and computations',
            'analyzer': 'Data and content analysis',
            'synthesizer': 'Information synthesis and summarization',
            'memory_search': 'Memory retrieval and pattern matching'
        }

        # Claude Code integrated tools
        self.claude_tools = {
            'web_search': 'Web search using SearchMaster multi-provider',
            'web_fetch': 'Fetch content from URLs',
            'read_file': 'Read file contents',
            'write_file': 'Write content to files',
            'edit_file': 'Edit existing files',
            'glob_search': 'Search files by pattern',
            'grep_search': 'Search file contents',
            'bash_execute': 'Execute bash commands',
            'todo_write': 'Task management'
        }

        # MCP integrated tools
        self.mcp_tools = {
            'kapture_navigate': 'Browser navigation',
            'kapture_click': 'Browser element interaction',
            'kapture_screenshot': 'Browser screenshots',
            'kapture_new_tab': 'Browser tab management',
            'mcp_resource_list': 'MCP resource listing',
            'mcp_resource_read': 'MCP resource reading'
        }

        # Combine all tools
        self.available_tools = {**self.core_tools, **self.claude_tools, **self.mcp_tools}

        # Tool performance tracking
        self.tool_stats = {
            tool: {
                'success_rate': 0.75,
                'avg_time': 1.0,
                'usage_count': 0,
                'cost': self._get_tool_cost(tool),
                'category': self._get_tool_category(tool)
            } for tool in self.available_tools.keys()
        }

        self.logger.info(f"Enhanced tool system initialized: {len(self.available_tools)} tools available")

    def _init_enhanced_memory_system(self):
        """Initialize enhanced memory with workflow tracking."""
        self.memory = {
            'episodic': deque(maxlen=1000),
            'semantic': {},
            'working': {},
            'procedural': {},
            'tool_workflows': {},
            'browser_sessions': {},
            'search_patterns': {}
        }

        self.memory_stats = {
            'total_stored': 0,
            'total_retrieved': 0,
            'consolidations': 0,
            'workflow_patterns': 0
        }

    def _init_enhanced_learning_system(self):
        """Initialize adaptive learning system."""
        self.learning = {
            'experience_buffer': deque(maxlen=10000),
            'learning_rate': 0.01,
            'exploration_rate': 0.1,
            'performance_history': [],
            'tool_combination_rewards': {},
            'workflow_patterns': {},
            'query_routing_patterns': {}  # NEW: Track successful routing decisions
        }

    def _init_query_router(self):
        """Initialize enhanced query router with search vs code detection."""
        # Priority 1: Explicit code request patterns (HIGHEST PRIORITY)
        self.explicit_code_patterns = [
            'write code', 'generate code', 'create code', 'implement code',
            'code for', 'write a script', 'generate a script', 'create a script',
            'write application', 'generate application', 'build application'
        ]

        # Priority 2: Search intent patterns
        self.search_patterns = [
            'search', 'find', 'look up', 'lookup', 'research', 'investigate',
            'what is', 'who is', 'where is', 'when is', 'how to', 'why does',
            'tell me about', 'information about', 'details on'
        ]

        # Tool-based search patterns (e.g., "use X to search")
        self.tool_based_search_patterns = [
            'use .* to (search|find|lookup|look up)',
            'with .* (search|find|lookup|look up)',
            'via .* (search|find|lookup|look up)',
            'through .* (search|find|lookup|look up)'
        ]

        # Code generation indicators
        self.code_indicators = [
            'typescript', 'javascript', 'python', 'application', 'script',
            'api', 'function', 'class', 'module', 'package'
        ]

        self.logger.info("Enhanced query router initialized with search vs code detection")

    async def route_query(self, query: str) -> Dict[str, Any]:
        """
        Enhanced query routing with search vs code generation detection.

        PRIORITY ORDER:
        1. Explicit code requests (write code, generate code, etc.)
        2. Tool-based search patterns (use X to search)
        3. General search patterns (search, find, lookup)
        4. Default to research/analysis

        Args:
            query: User query string

        Returns:
            Dict with routing decision and confidence
        """
        query_lower = query.lower()

        # Priority 1: Explicit code generation request?
        for pattern in self.explicit_code_patterns:
            if query_lower.startswith(pattern) or f" {pattern} " in query_lower:
                return {
                    'intent': 'CODE_GENERATION',
                    'confidence': 0.95,
                    'strategy': 'direct',
                    'reasoning': f'Explicit code request detected: "{pattern}"'
                }

        # Check for "generate X functionality" pattern (code generation)
        if query_lower.startswith('generate ') and 'functionality' in query_lower:
            return {
                'intent': 'CODE_GENERATION',
                'confidence': 0.85,
                'strategy': 'direct',
                'reasoning': 'Generate functionality pattern detected'
            }

        # Priority 2: Tool-based search pattern? (e.g., "use perplexity to search")
        import re
        for pattern in self.tool_based_search_patterns:
            if re.search(pattern, query_lower):
                return {
                    'intent': 'WEB_SEARCH',
                    'confidence': 0.9,
                    'strategy': 'research_workflow',
                    'reasoning': f'Tool-based search pattern detected: "{pattern}"'
                }

        # Priority 3: General search intent?
        search_score = 0
        matched_patterns = []
        for pattern in self.search_patterns:
            if pattern in query_lower:
                search_score += 1
                matched_patterns.append(pattern)

        if search_score > 0:
            return {
                'intent': 'WEB_SEARCH',
                'confidence': min(0.7 + (search_score * 0.1), 0.95),
                'strategy': 'research_workflow',
                'reasoning': f'Search patterns detected: {matched_patterns}'
            }

        # Priority 4: Code generation indicators without explicit request?
        code_score = sum(1 for indicator in self.code_indicators if indicator in query_lower)
        if code_score >= 2:
            return {
                'intent': 'CODE_GENERATION',
                'confidence': 0.6 + (code_score * 0.1),
                'strategy': 'linear_chain',
                'reasoning': f'Multiple code indicators detected: {code_score}'
            }

        # Default: Research/Analysis
        return {
            'intent': 'RESEARCH',
            'confidence': 0.5,
            'strategy': 'adaptive',
            'reasoning': 'Default routing to research/analysis'
        }

    async def process_query_enhanced(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> EnhancedAgentResult:
        """
        Enhanced query processing with full MCP and tool integration.

        Args:
            query: User query string
            context: Optional context dictionary

        Returns:
            EnhancedAgentResult with comprehensive metadata
        """
        start_time = time.time()
        context = context or {}
        self.total_interactions += 1

        try:
            # 1. Enhanced query routing
            routing_decision = await self.route_query(query)
            self.logger.info(f"[ROUTING] Intent: {routing_decision['intent']}, "
                           f"Confidence: {routing_decision['confidence']:.2f}, "
                           f"Reasoning: {routing_decision['reasoning']}")

            # 2. Select planning strategy based on intent
            strategy = routing_decision['strategy']

            # 3. Execute based on intent
            if routing_decision['intent'] == 'WEB_SEARCH':
                result = await self._execute_web_search_workflow(query, context)
            elif routing_decision['intent'] == 'CODE_GENERATION':
                result = await self._execute_code_generation_workflow(query, context)
            elif routing_decision['intent'] == 'RESEARCH':
                result = await self._execute_research_workflow(query, context)
            else:
                result = await self._execute_adaptive_workflow(query, context)

            # 4. Update statistics and learning
            execution_time = time.time() - start_time
            if result['success']:
                self.successful_completions += 1

            # 5. Store experience for learning
            await self._store_routing_experience(query, routing_decision, result)

            # 6. Return enhanced result
            return EnhancedAgentResult(
                success=result['success'],
                content=result['content'],
                confidence=result.get('confidence', routing_decision['confidence']),
                tools_used=result.get('tools_used', []),
                tool_categories=result.get('tool_categories', []),
                execution_time=execution_time,
                planning_strategy=strategy,
                workflow_type=routing_decision['intent'],
                browser_actions=result.get('browser_actions', []),
                mcp_interactions=result.get('mcp_interactions', []),
                learning_triggered=result.get('learning_triggered', False),
                metadata={
                    'routing_decision': routing_decision,
                    'query_length': len(query),
                    'timestamp': time.time()
                }
            )

        except Exception as e:
            self.logger.error(f"[ERROR] Enhanced query processing failed: {e}")
            execution_time = time.time() - start_time
            return EnhancedAgentResult(
                success=False,
                content=f"Error processing query: {str(e)}",
                confidence=0.0,
                tools_used=[],
                tool_categories=[],
                execution_time=execution_time,
                planning_strategy='error_recovery',
                metadata={'error': str(e)}
            )

    async def _execute_web_search_workflow(
        self,
        query: str,
        context: Dict
    ) -> Dict[str, Any]:
        """Execute web search workflow using SearchMaster."""
        try:
            self.logger.info(f"[SEARCH] Executing web search workflow for: {query[:50]}...")

            # Use SearchMaster for comprehensive search
            search_result = await self._search_master_query(query)

            return {
                'success': True,
                'content': search_result,
                'confidence': 0.85,
                'tools_used': ['web_search', 'search_master'],
                'tool_categories': ['research'],
                'workflow_type': 'web_search'
            }

        except Exception as e:
            self.logger.error(f"[SEARCH ERROR] {e}")
            return {
                'success': False,
                'content': f"Search failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': [],
                'tool_categories': []
            }

    async def _execute_code_generation_workflow(
        self,
        query: str,
        context: Dict
    ) -> Dict[str, Any]:
        """Execute code generation workflow."""
        try:
            self.logger.info(f"[CODE GEN] Executing code generation for: {query[:50]}...")

            # Use LLM provider for code generation
            if self.llm_provider:
                response = await self.llm_provider.generate(
                    prompt=f"Generate code for: {query}",
                    system_prompt="You are an expert code generator. Provide clean, well-documented code."
                )

                return {
                    'success': True,
                    'content': response,
                    'confidence': 0.8,
                    'tools_used': ['code_generation', 'llm'],
                    'tool_categories': ['code'],
                    'workflow_type': 'code_generation'
                }
            else:
                return {
                    'success': False,
                    'content': "Code generation requires LLM provider configuration",
                    'confidence': 0.0,
                    'tools_used': [],
                    'tool_categories': []
                }

        except Exception as e:
            self.logger.error(f"[CODE GEN ERROR] {e}")
            return {
                'success': False,
                'content': f"Code generation failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': [],
                'tool_categories': []
            }

    async def _execute_research_workflow(
        self,
        query: str,
        context: Dict
    ) -> Dict[str, Any]:
        """Execute comprehensive research workflow."""
        try:
            self.logger.info(f"[RESEARCH] Executing research workflow for: {query[:50]}...")

            # Multi-step research workflow
            steps = []

            # Step 1: Web search
            search_result = await self._search_master_query(query)
            steps.append(('web_search', True))

            # Step 2: Analyze results
            if self.llm_provider:
                analysis = await self.llm_provider.generate(
                    prompt=f"Analyze and summarize: {search_result[:1000]}",
                    system_prompt="You are a research analyst. Provide comprehensive analysis."
                )
                steps.append(('analysis', True))
            else:
                analysis = search_result

            return {
                'success': True,
                'content': analysis,
                'confidence': 0.8,
                'tools_used': ['web_search', 'analyzer'],
                'tool_categories': ['research', 'analysis'],
                'workflow_type': 'research',
                'workflow_steps': len(steps)
            }

        except Exception as e:
            self.logger.error(f"[RESEARCH ERROR] {e}")
            return {
                'success': False,
                'content': f"Research failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': [],
                'tool_categories': []
            }

    async def _execute_adaptive_workflow(
        self,
        query: str,
        context: Dict
    ) -> Dict[str, Any]:
        """Execute adaptive workflow based on query characteristics."""
        try:
            self.logger.info(f"[ADAPTIVE] Executing adaptive workflow for: {query[:50]}...")

            # Adaptive logic based on query
            if self.llm_provider:
                response = await self.llm_provider.generate(
                    prompt=query,
                    system_prompt="You are an intelligent AI assistant with comprehensive capabilities."
                )

                return {
                    'success': True,
                    'content': response,
                    'confidence': 0.7,
                    'tools_used': ['llm', 'adaptive'],
                    'tool_categories': ['general'],
                    'workflow_type': 'adaptive'
                }
            else:
                return {
                    'success': False,
                    'content': "Adaptive workflow requires LLM provider configuration",
                    'confidence': 0.0,
                    'tools_used': [],
                    'tool_categories': []
                }

        except Exception as e:
            self.logger.error(f"[ADAPTIVE ERROR] {e}")
            return {
                'success': False,
                'content': f"Adaptive workflow failed: {str(e)}",
                'confidence': 0.0,
                'tools_used': [],
                'tool_categories': []
            }

    async def _search_master_query(self, query: str) -> str:
        """Execute query using SearchMaster."""
        try:
            # Create SearchMaster instance
            search_master = create_search_master(llm_provider=self.llm_provider)

            # Execute search
            result = await search_master.search(query)

            # Update tool stats
            self.tool_stats['web_search']['usage_count'] += 1

            return result

        except Exception as e:
            self.logger.error(f"[SEARCH MASTER ERROR] {e}")
            # Fallback to simple response
            return f"Search query: {query}\n\nSearchMaster unavailable. Please check configuration."

    async def _store_routing_experience(
        self,
        query: str,
        routing_decision: Dict,
        result: Dict
    ):
        """Store routing experience for learning."""
        experience = {
            'timestamp': time.time(),
            'query': query,
            'routing_decision': routing_decision,
            'result_success': result['success'],
            'confidence': result.get('confidence', 0.0),
            'tools_used': result.get('tools_used', [])
        }

        self.learning['experience_buffer'].append(experience)

        # Update routing patterns
        intent = routing_decision['intent']
        if intent not in self.learning['query_routing_patterns']:
            self.learning['query_routing_patterns'][intent] = []
        self.learning['query_routing_patterns'][intent].append({
            'query_snippet': query[:50],
            'success': result['success'],
            'confidence': routing_decision['confidence']
        })

    def _get_tool_cost(self, tool_name: str) -> float:
        """Get estimated cost for tool usage."""
        cost_map = {
            'calculator': 0.05,
            'analyzer': 0.1,
            'synthesizer': 0.1,
            'memory_search': 0.05,
            'web_search': 0.3,
            'web_fetch': 0.2,
            'read_file': 0.05,
            'write_file': 0.1,
            'bash_execute': 0.15,
            'kapture_navigate': 0.4,
            'kapture_click': 0.2,
            'kapture_screenshot': 0.3
        }
        return cost_map.get(tool_name, 0.1)

    def _get_tool_category(self, tool_name: str) -> str:
        """Get tool category for organization."""
        if tool_name in self.core_tools:
            return 'core'
        elif tool_name in self.claude_tools:
            return 'claude'
        elif tool_name in self.mcp_tools:
            return 'mcp'
        return 'general'

    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive enhanced agent status."""
        uptime = time.time() - self.active_since
        success_rate = self.successful_completions / max(self.total_interactions, 1)

        return {
            'agent_name': self.agent_name,
            'version': 'Enhanced with Full MCP Integration',
            'uptime_seconds': uptime,
            'total_interactions': self.total_interactions,
            'successful_completions': self.successful_completions,
            'success_rate': success_rate,

            'planning': {
                'strategies_available': len(self.planning['strategies']),
                'max_depth': self.planning['max_depth'],
                'tool_combinations': len(self.planning['tool_combinations'])
            },

            'tools': {
                'total_tools': len(self.available_tools),
                'core_tools': len(self.core_tools),
                'claude_tools': len(self.claude_tools),
                'mcp_tools': len(self.mcp_tools),
                'total_tool_uses': sum(stats['usage_count'] for stats in self.tool_stats.values())
            },

            'memory': {
                'episodic_memories': len(self.memory['episodic']),
                'total_stored': self.memory_stats['total_stored'],
                'total_retrieved': self.memory_stats['total_retrieved']
            },

            'learning': {
                'experiences_stored': len(self.learning['experience_buffer']),
                'routing_patterns': len(self.learning['query_routing_patterns']),
                'workflow_patterns': len(self.learning['workflow_patterns'])
            }
        }


def create_prince_flowers_enhanced(llm_provider: Optional[BaseLLMProvider] = None):
    """Factory function to create enhanced Prince Flowers agent."""
    return PrinceFlowersEnhancedIntegration(llm_provider)
