"""
Enhanced AI Integration for TORQ CONSOLE Web Interface.

This module provides comprehensive AI integration that connects the web interface
with multiple AI providers including DeepSeek, web search capabilities, and
Prince Flowers agent routing.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json

# Import LLM components
try:
    from ..llm.manager import LLMManager
    from ..llm.providers.websearch import WebSearchProvider
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False


class AIIntegration:
    """
    Enhanced AI integration that orchestrates multiple AI providers and capabilities
    for the TORQ CONSOLE web interface.
    """

    def __init__(self, model: str = "deepseek-chat", config: Optional[Dict[str, Any]] = None):
        """
        Initialize AI integration with multiple providers.

        Args:
            model: Default AI model to use
            config: Configuration dictionary
        """
        self.model = model
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize LLM Manager if available
        if LLM_AVAILABLE:
            try:
                self.llm_manager = LLMManager(config)
                self.web_search_provider = WebSearchProvider(config)
                self.enhanced_mode = True
                self.logger.info("AI Integration initialized in enhanced mode")
            except Exception as e:
                self.logger.error(f"Failed to initialize enhanced AI components: {e}")
                self.llm_manager = None
                self.web_search_provider = None
                self.enhanced_mode = False
        else:
            self.llm_manager = None
            self.web_search_provider = None
            self.enhanced_mode = False
            self.logger.warning("AI Integration initialized in basic mode (LLM components not available)")

        # Provider mapping for different query types
        self.provider_mapping = {
            'search': 'web_search',
            'ai_news': 'deepseek',
            'analysis': 'deepseek',
            'general': 'deepseek',
            'default': 'deepseek'
        }

        # Query classification keywords
        self.search_keywords = [
            'search', 'find', 'latest', 'current', 'news', 'recent',
            'what is happening', 'developments', 'updates', 'trending'
        ]

        self.ai_keywords = [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'deep learning', 'neural network', 'llm', 'gpt', 'chatgpt',
            'claude', 'openai', 'anthropic', 'deepseek'
        ]

    def classify_query(self, query: str) -> str:
        """
        Classify the query type to determine the best processing approach.

        Args:
            query: The user query

        Returns:
            Query classification ('content_creation', 'search', 'ai_news', 'analysis', 'general')
        """
        query_lower = query.lower().strip()

        # HIGHEST PRIORITY: Check for content creation/generation intent
        # This must be checked BEFORE search detection to avoid false positives
        content_creation_indicators = [
            "create a post", "create an x.com post", "create a tweet", "write a post",
            "use this information to create", "use this to create", "turn this into",
            "make a post", "format this as", "summarize this", "based on this information",
            "based on search results", "based on the above", "use the above"
        ]
        if any(indicator in query_lower for indicator in content_creation_indicators):
            return 'content_creation'

        # Prioritize explicit web search intent (but not if creating content from search)
        web_search_indicators = ['search web', 'search the web', 'web search', 'google', 'find online']
        if any(indicator in query_lower for indicator in web_search_indicators):
            return 'search'

        # Check for search queries
        if any(keyword in query_lower for keyword in self.search_keywords):
            # Only classify as ai_news if there's no explicit search intent and it's AI-related
            if any(ai_keyword in query_lower for ai_keyword in self.ai_keywords):
                # If it contains specific search terms like "search", "find", prioritize search
                priority_search = ['search', 'find', 'look for', 'get', 'fetch']
                if any(term in query_lower for term in priority_search):
                    return 'search'
                return 'ai_news'
            else:
                return 'search'

        # Check for analysis queries
        if any(keyword in query_lower for keyword in ['analyze', 'analysis', 'explain', 'compare', 'evaluate']):
            return 'analysis'

        # Default to general
        return 'general'

    async def generate_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        provider_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI response using the most appropriate provider and approach.

        Args:
            query: User query
            context: Optional context information
            provider_hint: Optional hint for provider selection

        Returns:
            Dictionary with response and metadata
        """
        start_time = datetime.now()
        context = context or {}

        try:
            if self.enhanced_mode and self.llm_manager:
                # Enhanced mode with full AI capabilities
                return await self._generate_enhanced_response(query, context, provider_hint, start_time)
            else:
                # Basic mode fallback
                return await self._generate_basic_response(query, context, start_time)

        except Exception as e:
            self.logger.error(f"AI response generation failed: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                'success': False,
                'content': f"I apologize, but I encountered an error processing your request: {str(e)}",
                'error': str(e),
                'metadata': {
                    'query_type': 'error',
                    'execution_time': execution_time,
                    'timestamp': start_time.isoformat(),
                    'enhanced_mode': self.enhanced_mode
                }
            }

    async def _generate_enhanced_response(
        self,
        query: str,
        context: Dict[str, Any],
        provider_hint: Optional[str],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Generate response using enhanced AI capabilities."""
        # Classify query type
        query_type = self.classify_query(query)
        self.logger.info(f"Query classified as: {query_type}")

        # Route to appropriate handler
        if query_type == 'content_creation':
            # HIGHEST PRIORITY: Route content creation to general handler (Claude)
            # This bypasses search entirely and uses Claude for content generation
            response = await self._handle_general_query(query, context)
        elif query_type == 'search':
            response = await self._handle_search_query(query, context)
        elif query_type == 'ai_news':
            response = await self._handle_ai_news_query(query, context)
        elif query_type == 'analysis':
            response = await self._handle_analysis_query(query, context)
        else:
            response = await self._handle_general_query(query, context)

        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()

        return {
            'success': True,
            'content': response,
            'response': response,  # Backward compatibility
            'metadata': {
                'query_type': query_type,
                'execution_time': execution_time,
                'provider_used': 'enhanced_ai',
                'timestamp': start_time.isoformat(),
                'enhanced_mode': True
            }
        }

    async def _generate_basic_response(
        self,
        query: str,
        context: Dict[str, Any],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Generate response using basic capabilities when enhanced mode is not available."""
        execution_time = (datetime.now() - start_time).total_seconds()

        # Basic response logic
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in self.search_keywords):
            response = f"""I understand you're looking for information about: "{query}"

Unfortunately, I don't have access to real-time web search capabilities at the moment. For the most current information, I recommend:

1. **Search Engines**: Use Google, Bing, or DuckDuckGo
2. **News Websites**: Check reputable news sources for recent developments
3. **Official Sources**: Look for information on official websites or documentation
4. **Social Media**: Check official accounts for updates

If this is about AI developments specifically, consider:
- TechCrunch AI section
- MIT Technology Review
- Official AI company blogs (OpenAI, Google, Anthropic, etc.)
- AI research repositories like arXiv"""

        else:
            response = f"""Thank you for your question: "{query}"

I'm operating in basic mode currently, which means I have limited AI processing capabilities. While I can provide general assistance and guidance, I cannot access:
- Real-time web search
- Current news and developments
- Advanced AI model responses

For complex queries, I recommend using the full TORQ Console interface or connecting with external AI services directly."""

        return {
            'success': True,
            'content': response,
            'response': response,
            'metadata': {
                'query_type': 'basic',
                'execution_time': execution_time,
                'provider_used': 'basic_fallback',
                'timestamp': start_time.isoformat(),
                'enhanced_mode': False
            }
        }

    async def _handle_search_query(self, query: str, context: Dict[str, Any]) -> str:
        """Handle search queries with web search integration."""
        try:
            self.logger.info(f"Processing search query: {query}")

            # Use web search provider
            if self.web_search_provider:
                search_results = await self.web_search_provider.search(query, max_results=5)

                if search_results.get('results'):
                    # Format search results into a comprehensive response
                    response_parts = [
                        f"I searched for information about '{query}' and found the following:"
                    ]

                    for i, result in enumerate(search_results['results'][:3], 1):
                        title = result.get('title', 'No title')
                        snippet = result.get('snippet', 'No description available')
                        url = result.get('url', '')

                        if url and url.startswith('http'):
                            response_parts.append(f"\n{i}. **{title}**")
                            response_parts.append(f"   {snippet}")
                            response_parts.append(f"   Source: {url}")
                        else:
                            response_parts.append(f"\n{i}. {snippet}")

                    # Only add helpful suggestions if results are limited
                    if len(search_results.get('results', [])) < 3:
                        response_parts.append(f"\n\n📌 **Need more information?** Try searching directly on:")
                        response_parts.append("• Google or Bing for latest updates")
                        response_parts.append("• Official news sources")
                        response_parts.append("• Social media platforms")

                    return ''.join(response_parts)

            # Fallback when search fails or not available
            return await self._generate_search_fallback(query)

        except Exception as e:
            self.logger.error(f"Search query failed: {e}")
            return await self._generate_search_fallback(query)

    async def _handle_ai_news_query(self, query: str, context: Dict[str, Any]) -> str:
        """Handle AI news and development queries."""
        try:
            self.logger.info(f"Processing AI news query: {query}")

            response_parts = []

            # Try to get AI analysis first
            if self.llm_manager:
                try:
                    ai_response = await self.llm_manager.ai_news_query(query)
                    response_parts.append(ai_response)
                except Exception as e:
                    self.logger.error(f"LLM AI news query failed: {e}")

            # Try web search for current AI news
            if self.web_search_provider:
                try:
                    search_results = await self.web_search_provider.search_ai_news(query)
                    if search_results.get('results'):
                        response_parts.append("\n\n**Current Sources for More Information:**")
                        for result in search_results['results'][:2]:
                            if result.get('url') and result.get('url').startswith('http'):
                                title = result.get('title', 'AI News Source')
                                url = result.get('url')
                                response_parts.append(f"• [{title}]({url})")
                except Exception as e:
                    self.logger.error(f"Web search for AI news failed: {e}")

            if response_parts:
                response_parts.append(f"\n\n*Note: For the latest AI developments, consider checking sources like TechCrunch AI, MIT Technology Review, VentureBeat, or official AI company announcements.*")
                return ''.join(response_parts)
            else:
                return await self._generate_ai_fallback(query)

        except Exception as e:
            self.logger.error(f"AI news query failed: {e}")
            return await self._generate_ai_fallback(query)

    async def _handle_analysis_query(self, query: str, context: Dict[str, Any]) -> str:
        """Handle analysis and explanation queries."""
        try:
            self.logger.info(f"Processing analysis query: {query}")

            if self.llm_manager:
                # Use Claude for analysis (faster and more efficient)
                # Adaptive max_tokens based on query length
                query_words = len(query.split())
                max_tokens = 800 if query_words < 20 else 1500

                response = await self.llm_manager.query('claude', query,
                                                      temperature=0.3,  # Reduced for faster generation
                                                      max_tokens=max_tokens)

                return response or "I apologize, but I couldn't generate an analysis for your query."
            else:
                return f"I understand you want me to analyze: '{query}'\n\nUnfortunately, I don't have access to advanced AI analysis capabilities at the moment. For detailed analysis, please try using external AI services or the full TORQ Console interface."

        except Exception as e:
            self.logger.error(f"Analysis query failed: {e}")
            return f"I encountered an error while analyzing your query: {str(e)}. Please try rephrasing your question."

    async def _handle_general_query(self, query: str, context: Dict[str, Any]) -> str:
        """Handle general queries."""
        try:
            self.logger.info(f"Processing general query: {query}")

            if self.llm_manager:
                # Use Claude for general queries (faster response time)
                # Adaptive tokens for short vs long queries
                short_keywords = ['x.com', 'post', 'tweet', 'short', 'brief', 'quick']
                is_short = any(kw in query.lower() for kw in short_keywords)
                max_tokens = 500 if is_short else 1000

                response = await self.llm_manager.query('claude', query,
                                                      temperature=0.3,  # Reduced for faster generation
                                                      max_tokens=max_tokens)

                return response or "I processed your query but couldn't generate a specific response."
            else:
                return f"Thank you for your question: '{query}'\n\nI'm currently operating in basic mode and cannot provide advanced AI responses. For more detailed assistance, please try the full TORQ Console interface or external AI services."

        except Exception as e:
            self.logger.error(f"General query failed: {e}")
            return f"I encountered an error processing your query: {str(e)}. Please try again."

    async def _generate_search_fallback(self, query: str) -> str:
        """Generate fallback response for search queries when search fails."""
        return f"""I apologize, but I cannot search for current information about '{query}' at the moment due to technical limitations.

For the most up-to-date information, I recommend:

**Search Engines:**
• Google: https://www.google.com/search?q={query.replace(' ', '+')}
• Bing: https://www.bing.com/search?q={query.replace(' ', '+')}
• DuckDuckGo: https://duckduckgo.com/?q={query.replace(' ', '+')}

**News Sources:**
• Reuters, Associated Press, BBC News
• Industry-specific publications
• Official websites and press releases

**For AI-related queries:**
• TechCrunch AI, MIT Technology Review
• Official AI company blogs and announcements
• AI research repositories (arXiv.org)"""

    async def _generate_ai_fallback(self, query: str) -> str:
        """Generate fallback response for AI news queries."""
        return f"""I apologize, but I cannot access current AI news and developments about '{query}' at the moment.

For the latest AI news and developments, I recommend checking:
• **TechCrunch AI**: Latest AI industry news and company announcements
• **MIT Technology Review**: In-depth analysis of AI developments
• **VentureBeat AI**: Business and technology AI news
• **Official AI Company Blogs**: OpenAI, Google DeepMind, Anthropic, etc.
• **AI Research Papers**: arXiv.org for academic developments
• **AI Newsletters**: The Batch (deeplearning.ai), Import AI, etc.

These sources will have the most current information about AI developments and trends."""

    async def select_relevant_files(self, message: str, candidate_files: List[str]) -> List[str]:
        """Select relevant files based on AI analysis."""
        # Enhanced implementation that considers the new capabilities
        relevant = []
        message_lower = message.lower()

        for file in candidate_files:
            file_lower = file.lower()

            # Check for direct file name mentions
            if any(word in file_lower for word in message_lower.split()):
                relevant.append(file)
            # Prioritize Python files for coding tasks
            elif file.endswith('.py') and any(word in message_lower for word in ['function', 'class', 'method', 'code']):
                relevant.append(file)
            # Prioritize config files for configuration tasks
            elif any(ext in file_lower for ext in ['.json', '.yaml', '.toml', '.ini']) and 'config' in message_lower:
                relevant.append(file)

        return relevant[:5]  # Limit to 5 files

    async def generate_plan(self, message: str, repo_structure: Dict[str, Any],
                          mcp_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate implementation plan using AI."""
        plan = {
            "message": message,
            "steps": [
                "Analyze requirements",
                "Identify files to modify",
                "Implement changes",
                "Test implementation",
                "Update documentation"
            ],
            "files_to_modify": [],
            "estimated_complexity": "medium",
            "mcp_context_used": bool(mcp_context),
            "enhanced_mode": self.enhanced_mode
        }

        if self.enhanced_mode and self.llm_manager:
            try:
                # Use AI to enhance the plan
                planning_prompt = f"""Analyze this development task and create a detailed plan:

Task: {message}

Repository structure context: {json.dumps(repo_structure, indent=2) if repo_structure else 'Not available'}

MCP context: {json.dumps(mcp_context, indent=2) if mcp_context else 'Not available'}

Please provide a structured implementation plan with specific steps and file recommendations."""

                ai_plan = await self.llm_manager.query('deepseek', planning_prompt, temperature=0.3)
                if ai_plan:
                    plan["ai_generated_details"] = ai_plan
            except Exception as e:
                self.logger.error(f"AI plan generation failed: {e}")

        return plan

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of all AI components."""
        health_results = {
            'overall_status': 'unknown',
            'enhanced_mode': self.enhanced_mode,
            'components': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            if self.enhanced_mode:
                # Check LLM Manager
                if self.llm_manager:
                    try:
                        llm_health = await self.llm_manager.health_check()
                        health_results['components']['llm_manager'] = llm_health
                    except Exception as e:
                        health_results['components']['llm_manager'] = {
                            'status': 'unhealthy',
                            'error': str(e)
                        }

                # Check Web Search Provider
                if self.web_search_provider:
                    try:
                        search_health = await self.web_search_provider.health_check()
                        health_results['components']['web_search'] = search_health
                    except Exception as e:
                        health_results['components']['web_search'] = {
                            'status': 'unhealthy',
                            'error': str(e)
                        }

            # Test basic functionality
            try:
                test_response = await self.generate_response("test query", {'test_mode': True})
                health_results['components']['integration'] = {
                    'status': 'healthy' if test_response.get('success') else 'degraded',
                    'test_successful': test_response.get('success', False)
                }
            except Exception as e:
                health_results['components']['integration'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }

            # Determine overall status
            if health_results['components']:
                component_statuses = [comp.get('status', 'unknown') for comp in health_results['components'].values()]
                if all(status == 'healthy' for status in component_statuses):
                    health_results['overall_status'] = 'healthy'
                elif any(status == 'healthy' for status in component_statuses):
                    health_results['overall_status'] = 'degraded'
                else:
                    health_results['overall_status'] = 'unhealthy'
            else:
                health_results['overall_status'] = 'basic'

        except Exception as e:
            health_results['overall_status'] = 'unhealthy'
            health_results['error'] = str(e)

        return health_results

    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about AI integration capabilities."""
        capabilities = {
            'enhanced_mode': self.enhanced_mode,
            'query_types': list(self.provider_mapping.keys()),
            'features': []
        }

        if self.enhanced_mode:
            capabilities['providers'] = {
                'llm_manager': {
                    'available': bool(self.llm_manager),
                    'providers': list(self.llm_manager.providers.keys()) if self.llm_manager else [],
                    'default_provider': getattr(self.llm_manager, 'default_provider', 'unknown')
                },
                'web_search': {
                    'available': bool(self.web_search_provider),
                    'methods': getattr(self.web_search_provider, 'search_methods', []) if self.web_search_provider else []
                }
            }
            capabilities['features'] = [
                'Multi-provider AI responses',
                'Web search integration',
                'AI news specialization',
                'Query classification',
                'Context-aware responses',
                'Error handling and fallbacks'
            ]
        else:
            capabilities['providers'] = {
                'basic_mode': {
                    'available': True,
                    'description': 'Basic response generation without external AI providers'
                }
            }
            capabilities['features'] = [
                'Basic response generation',
                'Query classification',
                'Helpful fallback responses',
                'Search suggestions'
            ]

        return capabilities