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
    async def _generate_ai_response_fixed(self, user_content: str, context_matches: Optional[List] = None, tools: Optional[List[str]] = None) -> str:
        """
        FIXED: Generate AI response using enhanced AI integration.

        This method properly routes queries through the enhanced AI integration system
        which includes DeepSeek API, web search, and Prince Flowers capabilities.

        Args:
            user_content: The user's message/query
            context_matches: Optional context matches
            tools: Optional list of tools to use (e.g., ['web_search'])
        """
        try:
            self.logger.info(f"Processing AI query: {user_content} (tools: {tools})")

            # Check if this is a Prince Flowers command
            content_lower = user_content.lower().strip()

            # Enhanced detection for Prince Flowers commands
            # CRITICAL: Only treat as Prince command if it's a SEARCH/RESEARCH request
            # NOT if it's a BUILD/CREATE request!
            is_prince_search = (
                content_lower.startswith("prince search") or
                content_lower.startswith("prince help") or
                content_lower.startswith("prince status") or
                ("prince" in content_lower and any(keyword in content_lower for keyword in [
                    "search", "find", "research", "help", "status"
                ]))
            )

            # Detect BUILD/CODE requests (even with "prince" prefix)
            is_build_request = any(keyword in content_lower for keyword in [
                "create", "build", "generate", "make", "develop", "implement", "code"
            ])

            # Check if web_search tool is explicitly requested
            is_web_search_requested = tools and 'web_search' in tools

            # Only treat as search query if:
            # 1. web_search tool is explicitly requested, OR
            # 2. User explicitly asks for search with keywords like "search web for"
            is_explicit_search = is_web_search_requested or any(phrase in content_lower for phrase in [
                "search web for", "search the web", "web search", "find online", "search for information about"
            ])

            # CRITICAL ROUTING LOGIC:
            # 1. Build requests (even with "prince" prefix) -> Direct Claude code generation
            # 2. Prince search/research -> Prince Flowers
            # 3. Explicit web search -> Enhanced AI with search
            # 4. Everything else -> Basic query (Claude)

            if is_build_request:
                # BUILD MODE: Use Claude directly, bypass Prince Flowers entirely
                self.logger.info(f"Detected BUILD request, using Claude Sonnet 4.5 directly")
                return await WebUIAIFixes._handle_basic_query_fixed(self, user_content, context_matches)
            elif is_prince_search:
                # RESEARCH MODE: Use Prince Flowers for search/research
                self.logger.info(f"Detected Prince SEARCH request, using Prince Flowers")
                return await WebUIAIFixes._handle_prince_command_fixed(self, user_content, context_matches)
            elif is_explicit_search:
                # WEB SEARCH MODE: Use enhanced AI integration
                self.logger.info(f"Detected WEB SEARCH request, using enhanced AI")
                return await WebUIAIFixes._handle_enhanced_ai_query_fixed(self, user_content, context_matches)
            else:
                # DEFAULT: Basic query mode
                return await WebUIAIFixes._handle_basic_query_fixed(self, user_content, context_matches)

        except Exception as e:
            self.logger.error(f"Error generating AI response: {e}")
            return f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again."

    @staticmethod
    async def _handle_enhanced_ai_query_fixed(self, query: str, context_matches: Optional[List] = None) -> str:
        """
        FIXED: Handle WEB SEARCH queries through the enhanced AI integration system.

        This method uses the console's AI integration which includes:
        - DeepSeek API for AI responses
        - Web search capabilities (PRIMARY PURPOSE - this is for SEARCH queries)
        - Query classification and routing
        - Fallback handling

        NOTE: This is for SEARCH queries only. For BUILD/CODE queries, use _handle_basic_query_fixed().
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

            # Method 5: Ultimate fallback - route through basic handler for BUILD MODE
            self.logger.info("Routing Prince command through basic handler for BUILD MODE (not search)")
            query = command
            if command.lower().startswith('prince '):
                query = command[7:].strip()

            # Route to build handler, not search handler
            return await WebUIAIFixes._handle_basic_query_fixed(self, query, context_matches)

        except Exception as e:
            self.logger.error(f"Error in Prince command handling: {e}")
            return f"Error processing Prince Flowers command: {str(e)}"

    @staticmethod
    async def _handle_basic_query_fixed(self, query: str, context_matches: Optional[List] = None) -> str:
        """
        FIXED: Handle basic queries - BUILD MODE (not search).

        This method processes build/code requests through the AI system.
        Uses Claude Sonnet 4.5 directly for code generation (bypasses Prince Flowers research mode).
        """
        try:
            self.logger.info(f"Processing basic query (BUILD MODE): {query}")

            # PRIORITY 1: Try Claude provider directly for code generation
            # This bypasses Prince Flowers' research mode and uses Claude's code generation
            if hasattr(self.console, 'llm_manager') and self.console.llm_manager:
                try:
                    # Get Claude provider
                    providers = self.console.llm_manager.providers
                    claude = providers.get('claude') if hasattr(providers, 'get') else None

                    if claude and hasattr(claude, 'is_configured') and claude.is_configured():
                        self.logger.info("Using Claude Sonnet 4.5 for direct code generation")

                        # Detect language from query
                        query_lower = query.lower()
                        if 'next' in query_lower or 'react' in query_lower:
                            language = 'typescript'
                        elif 'python' in query_lower:
                            language = 'python'
                        else:
                            language = 'typescript'  # Default for modern web apps

                        # Use Claude's code_generation method
                        response = await claude.code_generation(
                            task_description=query,
                            language=language,
                            context='Build a complete, production-ready application with all necessary files and proper structure',
                            temperature=0.3,
                            max_tokens=8000
                        )
                        return response
                except Exception as e:
                    self.logger.warning(f"Claude direct code generation failed: {e}")

            # PRIORITY 2: Try console's generate_response method
            if hasattr(self.console, 'generate_response'):
                try:
                    result = await self.console.generate_response(query, context_matches)
                    return result
                except Exception as e:
                    self.logger.warning(f"Console generate_response failed: {e}")

            # PRIORITY 3: Try AI integration for code/build requests
            if hasattr(self.console, 'ai_integration') and self.console.ai_integration:
                try:
                    context = {
                        'web_interface': True,
                        'context_matches': context_matches or [],
                        'timestamp': datetime.now().isoformat(),
                        'mode': 'build'  # Explicitly set build mode
                    }

                    response = await self.console.ai_integration.generate_response(query, context)

                    if response.get('success', True):
                        return response.get('content', response.get('response', 'Build request processed.'))
                    else:
                        return response.get('content', f"Error: {response.get('error', 'Unknown error')}")
                except Exception as e:
                    self.logger.error(f"AI integration failed: {e}")

            # PRIORITY 4: Try LLM manager generate_response
            if hasattr(self.console, 'llm_manager') and self.console.llm_manager:
                try:
                    response = await self.console.llm_manager.generate_response(
                        query,
                        context={'mode': 'build', 'web_interface': True}
                    )
                    return response
                except Exception as e:
                    self.logger.error(f"LLM manager failed: {e}")

            # Last resort - inform user the system needs configuration
            return f"""I received your request to build:

"{query[:200]}..."

However, I'm unable to process build requests at the moment because the AI backend is not properly configured.

**To fix this, you need:**
1. Ensure DeepSeek or Claude API keys are configured
2. Restart the TORQ Console server
3. Try your request again

**For immediate help:**
- Check if the server logs show any API connection errors
- Verify your API keys in the .env file

I apologize for the inconvenience!"""

        except Exception as e:
            self.logger.error(f"Error in basic query handling: {e}")
            return f"I encountered an error processing your build request: {str(e)}. Please check the server logs."

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
            # Pass the tools parameter to respect user's tool selection
            response_content = await WebUIAIFixes._generate_ai_response_fixed(
                self, request.message, None, tools=getattr(request, 'tools', None)
            )

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