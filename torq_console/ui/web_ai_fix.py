"""
AI Integration Fixes for TORQ CONSOLE Web Interface.

This module contains the fixed methods for proper AI integration routing
in the web interface with self-correcting intent detection and timeout handling.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

# Import the self-correcting intent detector
try:
    from .intent_detector import get_intent_detector
    INTENT_DETECTOR_AVAILABLE = True
except ImportError:
    INTENT_DETECTOR_AVAILABLE = False
    logging.warning("Intent detector not available, using fallback routing")

# Import the advanced learning system
try:
    from .learning_system import get_learning_system
    LEARNING_SYSTEM_AVAILABLE = True
except ImportError:
    LEARNING_SYSTEM_AVAILABLE = False
    logging.warning("Learning system not available")


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
            start_time = datetime.now()

            # Use self-correcting intent detector if available
            if INTENT_DETECTOR_AVAILABLE:
                detector = get_intent_detector()
                decision = detector.detect_intent(user_content, tools)

                self.logger.info(
                    f"[INTENT DETECTOR] {decision.intent_type} (confidence: {decision.confidence:.2f}) "
                    f"- {decision.reasoning}"
                )

                # Route based on detected intent
                response = None
                if decision.intent_type == 'research':
                    # RESEARCH MODE: Use Prince Flowers for search/research
                    self.logger.info(f"-> Routing to Prince Flowers (RESEARCH mode)")
                    response = await WebUIAIFixes._handle_prince_command_fixed(self, user_content, context_matches)

                elif decision.intent_type == 'content_creation':
                    # CONTENT CREATION MODE: Use Claude to process/create content
                    self.logger.info(f"-> Routing to Claude Sonnet 4.5 (CONTENT CREATION mode)")
                    response = await WebUIAIFixes._handle_basic_query_fixed(self, user_content, context_matches)

                elif decision.intent_type == 'code_generation':
                    # CODE GENERATION MODE: Use Claude directly for code
                    self.logger.info(f"-> Routing to Claude Sonnet 4.5 (CODE GENERATION mode)")
                    response = await WebUIAIFixes._handle_basic_query_fixed(self, user_content, context_matches)

                else:
                    # GENERAL MODE: Default handling
                    self.logger.info(f"-> Routing to basic query handler (GENERAL mode)")
                    response = await WebUIAIFixes._handle_basic_query_fixed(self, user_content, context_matches)

                # LEARNING SYSTEM: Record interaction for continuous improvement
                if LEARNING_SYSTEM_AVAILABLE and response:
                    try:
                        learning_system = get_learning_system()
                        response_time = (datetime.now() - start_time).total_seconds()

                        # Determine if response was successful (no error indicators)
                        success = not any(phrase in response.lower() for phrase in [
                            'error', 'apologize', 'failed', 'unable to', 'cannot'
                        ])

                        learning_system.record_interaction(
                            query=user_content,
                            detected_intent=decision.intent_type,
                            confidence=decision.confidence,
                            success=success,
                            response_time=response_time,
                            tokens_used=len(response.split())  # Rough estimate
                        )

                        self.logger.info(
                            f"[LEARNING] Recorded interaction: {decision.intent_type} "
                            f"(success={success}, time={response_time:.2f}s)"
                        )
                    except Exception as e:
                        self.logger.warning(f"Learning system recording failed: {e}")

                return response

            else:
                # FALLBACK: Use legacy intent detection if new system unavailable
                self.logger.warning("Intent detector unavailable, using legacy routing")
                content_lower = user_content.lower().strip()

                # Simple fallback routing
                if tools and 'web_search' in tools:
                    return await WebUIAIFixes._handle_prince_command_fixed(self, user_content, context_matches)
                elif content_lower.startswith('prince '):
                    return await WebUIAIFixes._handle_prince_command_fixed(self, user_content, context_matches)
                else:
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

            # Use console's AI integration if available (WITH TIMEOUT)
            if hasattr(self.console, 'ai_integration') and self.console.ai_integration:
                # Prepare context for AI integration
                context = {
                    'web_interface': True,
                    'context_matches': context_matches or [],
                    'timestamp': datetime.now().isoformat()
                }

                # Generate response using enhanced AI integration WITH TIMEOUT
                try:
                    response = await asyncio.wait_for(
                        self.console.ai_integration.generate_response(query, context),
                        timeout=180.0  # 180s timeout for AI integration (3 minutes for complex queries)
                    )

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

                except asyncio.TimeoutError:
                    self.logger.error(f"[TIMEOUT] AI integration query exceeded 180s: {query[:100]}")
                    return "I apologize, but your search query took too long to process (>3 minutes). Please try a more specific query."

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
            self.logger.info(f"[PRINCE ROUTING] Processing Prince Flowers command: {command}")

            # Ensure command starts with 'prince' for proper routing
            if not command.lower().startswith('prince'):
                command = f"prince {command}"
                self.logger.info(f"[PRINCE ROUTING] Added 'prince' prefix: {command}")

            # Method 1: Try enhanced integration wrapper (WITH TIMEOUT)
            self.logger.info("[PRINCE ROUTING] Trying Method 1: Enhanced integration wrapper")
            if hasattr(self.console, 'prince_flowers_integration') and self.console.prince_flowers_integration:
                self.logger.info("[PRINCE ROUTING] prince_flowers_integration found, attempting query")
                integration = self.console.prince_flowers_integration

                enhanced_context = {
                    'web_interface': True,
                    'context_matches': context_matches or [],
                    'timestamp': datetime.now().isoformat()
                }

                try:
                    response = await asyncio.wait_for(
                        integration.query(command, enhanced_context, show_performance=True),
                        timeout=180.0  # 180s timeout for Prince Flowers integration (3 minutes for research queries)
                    )

                    if response.success:
                        self.logger.info("[PRINCE ROUTING] [OK] Method 1 SUCCESS")
                        result = response.content
                        if response.execution_time and response.confidence:
                            result += f"\n\n*Processed in {response.execution_time:.2f}s with {response.confidence:.1%} confidence*"
                        return result
                    else:
                        self.logger.warning(f"[PRINCE ROUTING] [X] Method 1 FAILED: {response.error}")
                except asyncio.TimeoutError:
                    self.logger.warning("[PRINCE ROUTING] [X] Method 1 TIMEOUT (>180s)")
            else:
                self.logger.info("[PRINCE ROUTING] Method 1 not available (no prince_flowers_integration)")

            # Method 2: Try console's prince command handler
            self.logger.info("[PRINCE ROUTING] Trying Method 2: Console's handle_prince_command")
            if hasattr(self.console, 'handle_prince_command'):
                try:
                    self.logger.info("[PRINCE ROUTING] handle_prince_command found, attempting call")
                    result = await self.console.handle_prince_command(command, {'web_interface': True})
                    if result:
                        self.logger.info("[PRINCE ROUTING] [OK] Method 2 SUCCESS")
                        return result
                    else:
                        self.logger.warning("[PRINCE ROUTING] [X] Method 2 returned empty result")
                except Exception as e:
                    self.logger.warning(f"[PRINCE ROUTING] [X] Method 2 FAILED: {e}")
            else:
                self.logger.info("[PRINCE ROUTING] Method 2 not available (no handle_prince_command)")

            # Method 3: Try direct Prince Flowers agent
            self.logger.info("[PRINCE ROUTING] Trying Method 3: Direct Prince Flowers agent")
            if hasattr(self.console, 'prince_flowers'):
                self.logger.info("[PRINCE ROUTING] prince_flowers attribute found")
                try:
                    # Check if prince_flowers has handle_prince_command method
                    if hasattr(self.console.prince_flowers, 'handle_prince_command'):
                        self.logger.info("[PRINCE ROUTING] Method 3a: Using prince_flowers.handle_prince_command")
                        result = await self.console.prince_flowers.handle_prince_command(command, {'web_interface': True})
                        if result:
                            self.logger.info("[PRINCE ROUTING] [OK] Method 3a SUCCESS")
                            return result
                        else:
                            self.logger.warning("[PRINCE ROUTING] [X] Method 3a returned empty result")

                    # Check if prince_flowers IS the agent (direct agent object)
                    elif hasattr(self.console.prince_flowers, 'execute_agentic_task'):
                        self.logger.info("[PRINCE ROUTING] Method 3b: Using prince_flowers.execute_agentic_task (direct agent)")
                        query = command
                        if command.lower().startswith('prince '):
                            query = command[7:].strip()

                        result = await self.console.prince_flowers.execute_agentic_task(query)
                        if isinstance(result, dict):
                            answer = result.get('answer', result.get('response', 'Prince Flowers processed your request.'))
                            self.logger.info("[PRINCE ROUTING] [OK] Method 3b SUCCESS")
                            return answer
                        self.logger.info("[PRINCE ROUTING] [OK] Method 3b SUCCESS (string result)")
                        return str(result)

                    # Check if prince_flowers has an agent attribute
                    elif hasattr(self.console.prince_flowers, 'agent'):
                        self.logger.info("[PRINCE ROUTING] Method 3c: Using prince_flowers.agent.execute_agentic_task")
                        query = command
                        if command.lower().startswith('prince '):
                            query = command[7:].strip()

                        result = await self.console.prince_flowers.agent.execute_agentic_task(query)
                        if isinstance(result, dict):
                            answer = result.get('answer', result.get('response', 'Prince Flowers processed your request.'))
                            self.logger.info("[PRINCE ROUTING] [OK] Method 3c SUCCESS")
                            return answer
                        self.logger.info("[PRINCE ROUTING] [OK] Method 3c SUCCESS (string result)")
                        return str(result)

                    else:
                        self.logger.warning("[PRINCE ROUTING] [X] Method 3 FAILED: prince_flowers object found but no known methods available")
                except Exception as e:
                    self.logger.warning(f"[PRINCE ROUTING] [X] Method 3 EXCEPTION: {e}")
            else:
                self.logger.info("[PRINCE ROUTING] Method 3 not available (no prince_flowers attribute)")

            # Method 4: Fallback to torq_integration
            self.logger.info("[PRINCE ROUTING] Trying Method 4: torq_integration fallback")
            try:
                import sys
                sys.path.append(str(Path(__file__).parent.parent.parent))
                from torq_integration import PrinceFlowersIntegrationWrapper

                self.logger.info("[PRINCE ROUTING] Creating PrinceFlowersIntegrationWrapper")
                integration = PrinceFlowersIntegrationWrapper(self.console)
                response = await integration.query(command, {'web_interface_fallback': True})
                if response and hasattr(response, 'content'):
                    self.logger.info("[PRINCE ROUTING] [OK] Method 4 SUCCESS")
                    return response.content
                else:
                    self.logger.warning("[PRINCE ROUTING] [X] Method 4 returned invalid response")
            except Exception as e:
                self.logger.warning(f"[PRINCE ROUTING] [X] Method 4 EXCEPTION: {e}")

            # Method 5: Ultimate fallback - Route to enhanced AI query (RESEARCH MODE)
            # This is critical: When all Prince Flowers integration attempts fail,
            # we should route to RESEARCH mode (enhanced AI query) NOT build mode
            self.logger.warning(
                "[PRINCE ROUTING] ⚠️  ALL METHODS FAILED - Falling back to enhanced AI query (RESEARCH mode)"
            )
            query = command
            if command.lower().startswith('prince '):
                query = command[7:].strip()

            self.logger.info(f"[PRINCE ROUTING] Method 5: Routing to enhanced AI query with query: {query}")
            # Route to enhanced AI query handler (research/search mode)
            result = await WebUIAIFixes._handle_enhanced_ai_query_fixed(self, query, context_matches)
            self.logger.info("[PRINCE ROUTING] [OK] Method 5 (fallback) completed")
            return result

        except Exception as e:
            self.logger.error(f"[PRINCE ROUTING] [X][X][X] CRITICAL ERROR in Prince command handling: {e}")
            import traceback
            self.logger.error(f"[PRINCE ROUTING] Traceback: {traceback.format_exc()}")
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

            # PRIORITY 1: Try Claude provider directly for code generation (WITH TIMEOUT)
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

                        # Adaptive max_tokens based on query complexity
                        # Short content keywords: x.com, post, tweet, short, brief
                        short_keywords = ['x.com', 'post', 'tweet', 'short', 'brief', 'quick', 'simple']
                        is_short_request = any(kw in query_lower for kw in short_keywords)

                        # Set adaptive token limits
                        if is_short_request:
                            max_tokens = 800  # Short content (x.com posts, brief responses)
                            self.logger.info("Using short content mode: max_tokens=800")
                        elif len(query.split()) < 20:
                            max_tokens = 2000  # Medium complexity
                            self.logger.info("Using medium content mode: max_tokens=2000")
                        else:
                            max_tokens = 4000  # Complex requests (reduced from 8000)
                            self.logger.info("Using full content mode: max_tokens=4000")

                        # Use Claude's code_generation method WITH TIMEOUT
                        response = await asyncio.wait_for(
                            claude.code_generation(
                                task_description=query,
                                language=language,
                                context='Build a complete, production-ready application with all necessary files and proper structure',
                                temperature=0.3,
                                max_tokens=max_tokens
                            ),
                            timeout=180.0  # 180s timeout for code generation (3 minutes for complex builds)
                        )
                        return response
                except asyncio.TimeoutError:
                    self.logger.warning("Claude code generation timeout (>180s)")
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
        FIXED: Direct chat endpoint with proper AI routing and timeout handling.

        This endpoint properly routes all queries through the enhanced AI system
        with comprehensive error handling, response formatting, and 30s timeout.
        """
        try:
            self.logger.info(f"Direct chat request: {request.message}")

            # Route all queries through the enhanced AI system WITH TIMEOUT
            # Pass the tools parameter to respect user's tool selection
            try:
                response_content = await asyncio.wait_for(
                    WebUIAIFixes._generate_ai_response_fixed(
                        self, request.message, None, tools=getattr(request, 'tools', None)
                    ),
                    timeout=240.0  # 240-second timeout for entire request chain (4 minutes for complex queries)
                )
            except asyncio.TimeoutError:
                self.logger.error(f"[TIMEOUT] Request exceeded 240s: {request.message[:100]}")
                return {
                    "success": False,
                    "error": "Request timeout",
                    "response": "I apologize, but your request took too long to process (>4 minutes). This might be due to:\n\n"
                               "1. Extremely complex queries requiring extensive processing\n2. LLM API service delays\n3. Network connectivity issues\n\n"
                               "Please try:\n- Simplifying your query\n- Breaking it into smaller parts\n- Trying again in a moment",
                    "timestamp": datetime.now().isoformat(),
                    "timeout": True
                }

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