"""
AI Integration Fixes for TORQ CONSOLE Web Interface.

This module contains the fixed methods for proper AI integration routing
in the web interface. These methods should replace the existing ones in web.py.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path


class WebUIAIFixes:
    """Container for AI integration fixes for the WebUI class."""

    @staticmethod
    async def _generate_ai_response_fixed(self, user_content: str, context_matches: Optional[List] = None) -> str:
        """
        FIXED: Generate AI response using enhanced AI integration.

        This method properly routes queries through the enhanced AI integration system
        which includes DeepSeek API, web search, and Prince Flowers capabilities.
        """
        try:
            self.logger.info(f"Processing AI query: {user_content}")

            # Check if this is a Prince Flowers command
            content_lower = user_content.lower().strip()

            # Enhanced detection for Prince Flowers commands and search queries
            is_prince_command = (
                content_lower.startswith("prince ") or
                content_lower.startswith("@prince ") or
                any(keyword in content_lower for keyword in [
                    "prince search", "prince help", "prince status",
                ])
            )

            # Check if this should be routed to search/AI capabilities
            is_search_or_ai_query = any(keyword in content_lower for keyword in [
                "search", "find", "latest", "current", "news", "recent",
                "ai", "artificial intelligence", "developments", "what is",
                "how to", "web search", "search for", "ai news"
            ])

            if is_prince_command:
                return await WebUIAIFixes._handle_prince_command_fixed(self, user_content, context_matches)
            elif is_search_or_ai_query or True:  # Route all queries through enhanced AI
                return await WebUIAIFixes._handle_enhanced_ai_query_fixed(self, user_content, context_matches)
            else:
                return await WebUIAIFixes._handle_basic_query_fixed(self, user_content, context_matches)

        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again."

    @staticmethod
    async def _handle_enhanced_ai_query_fixed(self, query: str, context_matches: Optional[List] = None) -> str:
        """
        FIXED: Handle queries through the enhanced AI integration system.

        This method uses the console's AI integration which includes:
        - DeepSeek API for AI responses
        - Web search capabilities
        - Query classification and routing
        - Fallback handling
        """
        try:
            self.logger.info(f"Processing enhanced AI query: {query}")

            # Use console's AI integration if available
            if hasattr(self.console, 'ai_integration') and self.console.ai_integration:
                # Prepare context for AI integration
                context = {
                    'web_interface': True,
                    'context_matches': context_matches or [],
                    'timestamp': datetime.now().isoformat()
                }

                # Generate response using enhanced AI integration
                response = await self.console.ai_integration.generate_response(query, context)

                if response.get('success', True):
                    content = response.get('content', response.get('response', ''))

                    # Add metadata if available
                    if response.get('metadata'):
                        metadata = response['metadata']
                        if metadata.get('execution_time') and metadata.get('query_type'):
                            content += f"\n\n*{metadata['query_type'].title()} query processed in {metadata['execution_time']:.2f}s*"

                    return content or "I processed your query successfully."
                else:
                    return response.get('content', f"I encountered an issue: {response.get('error', 'Unknown error')}")

            else:
                return await WebUIAIFixes._handle_basic_query_fixed(self, query, context_matches)

        except Exception as e:
            self.logger.error(f"Error in enhanced AI query handling: {e}")
            return f"I encountered an error processing your query: {str(e)}. Please try again."

    @staticmethod
    async def _handle_prince_command_fixed(self, command: str, context_matches: Optional[List] = None) -> str:
        """
        FIXED: Handle Prince Flowers commands with enhanced integration.

        This method properly routes Prince Flowers commands through multiple
        integration layers with comprehensive fallback handling.
        """
        try:
            self.logger.info(f"Processing Prince Flowers command: {command}")

            # Ensure command starts with 'prince' for proper routing
            if not command.lower().startswith('prince'):
                command = f"prince {command}"

            # Method 1: Try enhanced integration wrapper
            if hasattr(self.console, 'prince_flowers_integration') and self.console.prince_flowers_integration:
                integration = self.console.prince_flowers_integration

                enhanced_context = {
                    'web_interface': True,
                    'context_matches': context_matches or [],
                    'timestamp': datetime.now().isoformat()
                }

                response = await integration.query(command, enhanced_context, show_performance=True)

                if response.success:
                    result = response.content
                    if response.execution_time and response.confidence:
                        result += f"\n\n*Processed in {response.execution_time:.2f}s with {response.confidence:.1%} confidence*"
                    return result
                else:
                    self.logger.warning(f"Prince Flowers integration failed: {response.error}")

            # Method 2: Try console's prince command handler
            if hasattr(self.console, 'handle_prince_command'):
                try:
                    result = await self.console.handle_prince_command(command, {'web_interface': True})
                    return result
                except Exception as e:
                    self.logger.warning(f"Console prince handler failed: {e}")

            # Method 3: Try direct Prince Flowers agent
            if hasattr(self.console, 'prince_flowers'):
                try:
                    if hasattr(self.console.prince_flowers, 'handle_prince_command'):
                        result = await self.console.prince_flowers.handle_prince_command(command, {'web_interface': True})
                        return result
                    elif hasattr(self.console.prince_flowers, 'agent'):
                        # Extract query from command
                        query = command
                        if command.lower().startswith('prince '):
                            query = command[7:].strip()

                        result = await self.console.prince_flowers.agent.execute_agentic_task(query)
                        return result.get('answer', 'Prince Flowers processed your request.')
                except Exception as e:
                    self.logger.warning(f"Direct Prince Flowers failed: {e}")

            # Method 4: Fallback to torq_integration
            try:
                import sys
                sys.path.append(str(Path(__file__).parent.parent.parent))
                from torq_integration import PrinceFlowersIntegrationWrapper

                integration = PrinceFlowersIntegrationWrapper(self.console)
                response = await integration.query(command, {'web_interface_fallback': True})
                return response.content
            except Exception as e:
                self.logger.warning(f"Fallback integration failed: {e}")

            # Method 5: Ultimate fallback - route through enhanced AI
            self.logger.info("Routing Prince command through enhanced AI as fallback")
            query = command
            if command.lower().startswith('prince '):
                query = command[7:].strip()

            return await WebUIAIFixes._handle_enhanced_ai_query_fixed(self, query, context_matches)

        except Exception as e:
            self.logger.error(f"Error in Prince command handling: {e}")
            return f"Error processing Prince Flowers command: {str(e)}"

    @staticmethod
    async def _handle_basic_query_fixed(self, query: str, context_matches: Optional[List] = None) -> str:
        """
        FIXED: Handle basic queries with enhanced fallback.

        This method provides a basic response when enhanced AI is not available.
        """
        try:
            self.logger.info(f"Processing basic query: {query}")

            # Try console's generate_response method
            if hasattr(self.console, 'generate_response'):
                try:
                    result = await self.console.generate_response(query, context_matches)
                    return result
                except Exception as e:
                    self.logger.warning(f"Console generate_response failed: {e}")

            # Enhanced fallback response
            query_lower = query.lower()

            if any(keyword in query_lower for keyword in ['search', 'find', 'latest', 'news', 'current']):
                return f"""I understand you're looking for information about: "{query}"

I don't have access to real-time search capabilities at the moment, but I can suggest some ways to find current information:

**For General Searches:**
• Use search engines like Google, Bing, or DuckDuckGo
• Check relevant official websites and documentation
• Look for recent news articles and press releases

**For AI-Related Information:**
• TechCrunch AI section for industry news
• MIT Technology Review for in-depth analysis
• Official AI company blogs (OpenAI, Google, Anthropic, etc.)
• arXiv.org for research papers

**For Breaking News:**
• Reuters, Associated Press, BBC News
• Industry-specific news sources
• Social media accounts of relevant organizations

Would you like me to help you formulate a more specific search strategy for "{query}"?"""

            else:
                return f"""Thank you for your question: "{query}"

I'm currently operating in basic mode, which means I have limited capabilities. While I can provide general assistance and guidance, I recommend:

1. **For complex queries**: Try using the full TORQ Console interface
2. **For search-related questions**: Use "prince search <your query>"
3. **For AI assistance**: Connect with external AI services directly
4. **For current information**: Check recent online sources

How else can I help you today?"""

        except Exception as e:
            self.logger.error(f"Error in basic query handling: {e}")
            return f"I'm available to help, but encountered an error: {str(e)}. Please try again."

    @staticmethod
    async def direct_chat_fixed(self, request) -> Dict[str, Any]:
        """
        FIXED: Direct chat endpoint with proper AI routing.

        This endpoint properly routes all queries through the enhanced AI system
        with comprehensive error handling and response formatting.
        """
        try:
            self.logger.info(f"Direct chat request: {request.message}")

            # Route all queries through the enhanced AI system
            response_content = await WebUIAIFixes._generate_ai_response_fixed(self, request.message, None)

            return {
                "success": True,
                "response": response_content,
                "agent": "TORQ Console Enhanced AI",
                "timestamp": datetime.now().isoformat(),
                "enhanced_mode": hasattr(self.console, 'ai_integration') and
                                getattr(self.console.ai_integration, 'enhanced_mode', False)
            }

        except Exception as e:
            self.logger.error(f"Direct chat error: {e}")
            return {
                "success": False,
                "error": f"Error processing your request: {str(e)}",
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again.",
                "timestamp": datetime.now().isoformat()
            }


# Monkey patch method to apply fixes
def apply_web_ai_fixes(web_ui_instance):
    """
    Apply the AI integration fixes to a WebUI instance.

    Args:
        web_ui_instance: Instance of the WebUI class to fix
    """
    # Replace the methods with fixed versions
    web_ui_instance._generate_ai_response = WebUIAIFixes._generate_ai_response_fixed.__get__(web_ui_instance)
    web_ui_instance._handle_enhanced_ai_query = WebUIAIFixes._handle_enhanced_ai_query_fixed.__get__(web_ui_instance)
    web_ui_instance._handle_prince_command = WebUIAIFixes._handle_prince_command_fixed.__get__(web_ui_instance)
    web_ui_instance._handle_general_query = WebUIAIFixes._handle_basic_query_fixed.__get__(web_ui_instance)

    logging.getLogger(__name__).info("Applied AI integration fixes to WebUI instance")


# Auto-apply fixes when this module is imported by web.py
def auto_apply_fixes():
    """Auto-apply fixes when this module is imported."""
    import sys

    # Check if web.py is in the call stack
    for frame_info in sys._current_frames().values():
        if 'web.py' in str(frame_info.f_code.co_filename):
            # Get the WebUI instance from the frame
            frame_locals = frame_info.f_locals
            if 'self' in frame_locals and hasattr(frame_locals['self'], '_generate_ai_response'):
                apply_web_ai_fixes(frame_locals['self'])
                break