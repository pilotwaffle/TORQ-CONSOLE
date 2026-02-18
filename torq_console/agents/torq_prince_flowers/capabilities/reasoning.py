"""
Reasoning engine for TORQ Prince Flowers agent.

This module provides advanced reasoning capabilities including:
- Query analysis and intent detection
- Reasoning mode selection
- Multi-step reasoning execution
- Response synthesis
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from ..core.state import ReasoningMode, ReasoningTrajectory
from ..tools.websearch import WebSearchTool
from ..tools.file_ops import FileOperationsTool


class ReasoningEngine:
    """Advanced reasoning engine for the Prince Flowers agent."""

    def __init__(self, llm_provider=None):
        """Initialize the reasoning engine."""
        self.llm_provider = llm_provider
        self.logger = logging.getLogger("ReasoningEngine")

        # Initialize tools
        self.web_search_tool = WebSearchTool()
        self.file_operations_tool = FileOperationsTool()

        # Reasoning patterns
        self.reasoning_patterns = {
            "research": [
                "analyze information needs",
                "search multiple sources",
                "extract and validate content",
                "synthesize findings"
            ],
            "analysis": [
                "deconstruct the problem",
                "identify key components",
                "evaluate relationships",
                "provide insights"
            ],
            "composition": [
                "break into subtasks",
                "execute sequentially",
                "monitor progress",
                "integrate results"
            ],
            "direct": [
                "understand intent",
                "generate response",
                "validate quality"
            ]
        }

    async def analyze_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze a query to determine intent, complexity, and requirements.

        Args:
            query: The user's query
            context: Additional context

        Returns:
            Analysis results with intent, complexity, and recommendations
        """
        try:
            # Basic query analysis
            analysis = {
                "query": query,
                "intent": self._detect_intent(query),
                "complexity": self._assess_complexity(query),
                "tools_needed": self._identify_required_tools(query),
                "estimated_time": self._estimate_execution_time(query),
                "requires_approval": self._check_approval_requirements(query),
                "context": context or {}
            }

            # Enhanced analysis if LLM provider is available
            if self.llm_provider:
                enhanced_analysis = await self._enhanced_query_analysis(query, context)
                analysis.update(enhanced_analysis)

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            return {
                "query": query,
                "intent": "unknown",
                "complexity": "medium",
                "tools_needed": [],
                "error": str(e)
            }

    async def select_reasoning_mode(self, analysis: Dict[str, Any], trajectory: ReasoningTrajectory) -> ReasoningMode:
        """
        Select the appropriate reasoning mode based on query analysis.

        Args:
            analysis: Query analysis results
            trajectory: Current reasoning trajectory

        Returns:
            Selected reasoning mode
        """
        try:
            intent = analysis.get("intent", "general")
            complexity = analysis.get("complexity", "medium")
            tools_needed = analysis.get("tools_needed", [])

            # Mode selection logic
            if intent == "research" or "search" in tools_needed:
                return ReasoningMode.RESEARCH
            elif intent == "analysis" or complexity in ["high", "very_high"]:
                return ReasoningMode.ANALYSIS
            elif intent == "composition" or len(tools_needed) > 2:
                return ReasoningMode.COMPOSITION
            elif intent == "planning" or complexity == "very_high":
                return ReasoningMode.META_PLANNING
            else:
                return ReasoningMode.DIRECT

        except Exception as e:
            self.logger.error(f"Error selecting reasoning mode: {e}")
            return ReasoningMode.DIRECT

    async def execute_reasoning_strategy(
        self,
        mode: ReasoningMode,
        query: str,
        analysis: Dict[str, Any],
        trajectory: ReasoningTrajectory,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute the selected reasoning strategy.

        Args:
            mode: The reasoning mode to execute
            query: Original query
            analysis: Query analysis
            trajectory: Reasoning trajectory
            context: Additional context

        Returns:
            Execution results with response and metadata
        """
        try:
            if mode == ReasoningMode.RESEARCH:
                return await self._execute_research_reasoning(query, analysis, trajectory, context)
            elif mode == ReasoningMode.ANALYSIS:
                return await self._execute_analysis_reasoning(query, analysis, trajectory, context)
            elif mode == ReasoningMode.COMPOSITION:
                return await self._execute_composition_reasoning(query, analysis, trajectory, context)
            elif mode == ReasoningMode.META_PLANNING:
                return await self._execute_meta_planning_reasoning(query, analysis, trajectory, context)
            else:
                return await self._execute_direct_reasoning(query, analysis, trajectory, context)

        except Exception as e:
            self.logger.error(f"Error executing reasoning strategy: {e}")
            return {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "error": str(e),
                "success": False
            }

    def _detect_intent(self, query: str) -> str:
        """Detect the primary intent of the query."""
        query_lower = query.lower()

        # Research intents
        if any(keyword in query_lower for keyword in ["search", "find", "research", "look up", "what are", "latest"]):
            return "research"

        # Analysis intents
        if any(keyword in query_lower for keyword in ["analyze", "compare", "evaluate", "explain", "how does"]):
            return "analysis"

        # Composition intents
        if any(keyword in query_lower for keyword in ["create", "build", "implement", "generate", "develop"]):
            return "composition"

        # Planning intents
        if any(keyword in query_lower for keyword in ["plan", "strategy", "approach", "design"]):
            return "planning"

        return "general"

    def _assess_complexity(self, query: str) -> str:
        """Assess the complexity of the query."""
        # Simple heuristics for complexity assessment
        complexity_indicators = {
            "simple": ["what is", "how to", "help", "status"],
            "medium": ["explain", "compare", "analyze"],
            "high": ["implement", "create", "build", "complex"],
            "very_high": ["system", "architecture", "enterprise", "comprehensive"]
        }

        query_lower = query.lower()
        complexity_score = 0

        for complexity, keywords in complexity_indicators.items():
            if any(keyword in query_lower for keyword in keywords):
                complexity_score += {"simple": 1, "medium": 2, "high": 3, "very_high": 4}[complexity]

        # Additional complexity factors
        if len(query.split()) > 20:
            complexity_score += 1
        if "?" in query and query.count("?") > 1:
            complexity_score += 1

        # Map score to complexity level
        if complexity_score <= 1:
            return "low"
        elif complexity_score <= 2:
            return "medium"
        elif complexity_score <= 3:
            return "high"
        else:
            return "very_high"

    def _identify_required_tools(self, query: str) -> List[str]:
        """Identify which tools are needed for the query."""
        query_lower = query.lower()
        tools_needed = []

        tool_indicators = {
            "web_search": ["search", "find", "research", "latest", "news"],
            "image_generation": ["image", "picture", "generate image", "create image"],
            "file_operations": ["file", "save", "read", "write", "create file"],
            "code_generation": ["code", "implement", "function", "class"],
            "browser_automation": ["browser", "web page", "scrape", "automate"],
            "terminal_commands": ["run", "execute", "command", "shell"]
        }

        for tool, keywords in tool_indicators.items():
            if any(keyword in query_lower for keyword in keywords):
                tools_needed.append(tool)

        return tools_needed

    def _estimate_execution_time(self, query: str) -> float:
        """Estimate the execution time in seconds."""
        base_time = 5.0  # Base time for simple queries

        # Add time based on complexity
        if self._assess_complexity(query) == "high":
            base_time += 10.0
        elif self._assess_complexity(query) == "very_high":
            base_time += 20.0

        # Add time for tools
        tools = self._identify_required_tools(query)
        if "web_search" in tools:
            base_time += 5.0
        if "image_generation" in tools:
            base_time += 10.0
        if "browser_automation" in tools:
            base_time += 15.0

        return base_time

    def _check_approval_requirements(self, query: str) -> bool:
        """Check if the query requires user approval."""
        approval_required_keywords = [
            "delete", "remove", "terminate", "post", "send", "execute",
            "install", "modify", "change", "publish", "share"
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in approval_required_keywords)

    async def _enhanced_query_analysis(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Enhanced analysis using LLM if available."""
        try:
            if not self.llm_provider:
                return {}

            analysis_prompt = f"""
            Analyze this query for intent and requirements:

            Query: "{query}"
            Context: {context or {}}

            Provide analysis in JSON format with:
            - primary_intent: main user intention
            - specific_requirements: list of specific needs
            - potential_risks: any security or operational risks
            - recommended_approach: suggested execution approach
            - confidence_level: how confident you are in this analysis (0-1)
            """

            # This would use the LLM provider for enhanced analysis
            # For now, return basic enhanced analysis
            return {
                "confidence_level": 0.8,
                "recommended_approach": "sequential_execution",
                "potential_risks": []
            }

        except Exception as e:
            self.logger.error(f"Error in enhanced query analysis: {e}")
            return {}

    async def _execute_research_reasoning(self, query: str, analysis: Dict, trajectory: ReasoningTrajectory, context: Dict) -> Dict[str, Any]:
        """
        Execute research reasoning strategy with web search and LLM synthesis.

        Includes robust tool failure handling:
        - Search timeout handling
        - Empty results handling
        - Exception handling (429, network errors, etc.)
        - Low-quality results filtering
        - Graceful fallback when tools fail
        """
        search_failed = False
        search_failure_reason = None
        search_results = []

        # Step 1: Perform web search with comprehensive error handling
        if hasattr(self.web_search_tool, 'search'):
            try:
                # Attempt web search with timeout
                import asyncio
                results = await asyncio.wait_for(
                    self.web_search_tool.search(query, num_results=5),
                    timeout=15.0  # 15 second timeout
                )

                if results:
                    # Filter out low-quality results (empty snippets)
                    quality_results = []
                    for result in results:
                        if isinstance(result, dict):
                            snippet = result.get('snippet', result.get('body', ''))
                            # Only include results with meaningful content
                            if snippet and len(snippet.strip()) > 20:
                                quality_results.append(result)
                        elif hasattr(result, 'snippet') and result.snippet:
                            if len(result.snippet.strip()) > 20:
                                quality_results.append(result)

                    search_results = quality_results

                    if not search_results:
                        search_failed = True
                        search_failure_reason = "All search results were low quality (empty snippets)"

                else:
                    search_failed = True
                    search_failure_reason = "Search returned no results"

            except asyncio.TimeoutError:
                search_failed = True
                search_failure_reason = "Search timed out after 15 seconds"
                self.logger.warning(f"Web search timeout: {query}")

            except Exception as e:
                # Categorize different error types
                error_str = str(e).lower()
                if '429' in error_str or 'rate' in error_str:
                    search_failed = True
                    search_failure_reason = "Rate limited (429)"
                elif 'network' in error_str or 'connection' in error_str:
                    search_failed = True
                    search_failure_reason = "Network error"
                elif 'timeout' in error_str:
                    search_failed = True
                    search_failure_reason = "Request timeout"
                else:
                    search_failed = True
                    search_failure_reason = f"Search error: {type(e).__name__}"

                self.logger.warning(f"Web search failed: {search_failure_reason} - {e}")
        else:
            search_failed = True
            search_failure_reason = "Web search tool not available"

        # Step 2: Build prompt with search results or fallback
        prompt = f"User Query: {query}\n\n"

        if search_results and not search_failed:
            # Web search succeeded - inject results
            prompt += "Web Search Results:\n"
            for i, result in enumerate(search_results[:5], 1):
                if isinstance(result, dict):
                    title = result.get('title', 'Unknown')
                    snippet = result.get('snippet', result.get('body', ''))
                    url = result.get('url', '')
                else:
                    title = getattr(result, 'title', 'Unknown')
                    snippet = getattr(result, 'snippet', getattr(result, 'body', ''))
                    url = getattr(result, 'url', '')

                # Include source title and snippet
                prompt += f"{i}. {title}\n"
                # Cap snippet length to avoid prompt bloat
                prompt += f"   {snippet[:400]}\n"
                if url:
                    prompt += f"   Source: {url}\n"
                prompt += "\n"

            prompt += "\nUsing the web search results above, provide a comprehensive and accurate response to the user's query.\n"

        else:
            # Web search failed - use fallback prompt
            prompt += (
                "Web search was unavailable. "
                "Please answer using your general knowledge and clearly label any uncertainty where needed. "
                "If you're not certain about current information (like real-time data), acknowledge that limitation.\n\n"
                f"User Query: {query}\n\n"
            )

        # Step 3: Call LLM if available
        if self.llm_provider:
            try:
                system_prompt = "You are Prince Flowers, an advanced AI research assistant. Provide accurate, well-researched responses."

                full_prompt = f"{system_prompt}\n\n{prompt}"

                # Use the LLM provider's generate_response method
                if hasattr(self.llm_provider, 'generate_response'):
                    response_text = await self.llm_provider.generate_response(
                        prompt=full_prompt,
                        max_tokens=4000
                    )

                    # Add web search unavailability notice if needed
                    if search_failed:
                        response_text += "\n\n---\n"
                        response_text += "Note: Web search was unavailable, so this answer may be less current or complete."

                    return {
                        "response": response_text,
                        "tools_used": ["llm"] if search_failed else ["web_search", "llm"],
                        "confidence": 0.85 if search_failed else 0.9
                    }
            except Exception as e:
                self.logger.warning(f"LLM generation failed: {e}")
                search_failed = True
                search_failure_reason = f"LLM error: {str(e)}"

        # Fallback: Return search results directly if LLM failed
        if search_results and not search_failed:
            response = f"Based on web search for '{query}':\n\n"
            for i, result in enumerate(search_results[:5], 1):
                if isinstance(result, dict):
                    title = result.get('title', 'Unknown')
                    snippet = result.get('snippet', result.get('body', ''))
                    url = result.get('url', '')
                else:
                    title = getattr(result, 'title', 'Unknown')
                    snippet = getattr(result, 'snippet', getattr(result, 'body', ''))
                    url = getattr(result, 'url', '')

                response += f"{i}. **{title}**\n"
                response += f"   {snippet[:400]}\n"
                if url:
                    response += f"   Source: {url}\n"
                response += "\n"

            return {
                "response": response,
                "tools_used": ["web_search"],
                "confidence": 0.8
            }

        # Final fallback when both search and LLM fail
        error_msg = f"I processed your query: '{query}'"
        if search_failure_reason:
            error_msg += f"\n\nHowever, I couldn't access web search ({search_failure_reason})."

        return {
            "response": error_msg + " Please check your API configuration.",
            "tools_used": [],
            "confidence": 0.3
        }

    async def _execute_direct_reasoning(self, query: str, analysis: Dict, trajectory: ReasoningTrajectory, context: Dict) -> Dict[str, Any]:
        """Execute direct reasoning strategy with LLM."""
        try:
            # Use LLM provider if available
            if self.llm_provider:
                try:
                    system_prompt = "You are Prince Flowers, an advanced AI assistant. Provide helpful, accurate, and thorough responses to user queries."

                    full_prompt = f"{system_prompt}\n\nUser Query: {query}"

                    # Use the LLM provider's generate_response method
                    if hasattr(self.llm_provider, 'generate_response'):
                        response_text = await self.llm_provider.generate_response(
                            prompt=full_prompt,
                            max_tokens=4000
                        )

                        return {
                            "response": response_text,
                            "tools_used": ["llm"],
                            "confidence": 0.9
                        }
                except Exception as e:
                    self.logger.warning(f"LLM generation failed: {e}")

            # Fallback response
            return {
                "response": f"I received your query: {query}. However, I cannot generate a response without an LLM provider. Please configure your API keys.",
                "tools_used": [],
                "confidence": 0.3
            }

        except Exception as e:
            self.logger.error(f"Direct reasoning failed: {e}")
            return {
                "response": f"I encountered an error: {str(e)}",
                "tools_used": [],
                "confidence": 0.1
            }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the reasoning engine."""
        try:
            # Check tools availability
            tools_health = {
                "web_search_tool": self.web_search_tool.is_available(),
                "file_operations_tool": self.file_operations_tool.is_available()
            }

            # Overall health
            healthy_tools = sum(1 for status in tools_health.values() if status)
            overall_health = healthy_tools / len(tools_health)

            return {
                "healthy": overall_health >= 0.5,
                "overall_health_score": overall_health,
                "components": tools_health,
                "reasoning_patterns": len(self.reasoning_patterns),
                "llm_provider": self.llm_provider is not None
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }