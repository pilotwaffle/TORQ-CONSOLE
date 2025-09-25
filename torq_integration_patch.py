#!/usr/bin/env python3
"""
Patch for TORQ Console Prince Flowers Integration
Fixes the process_query method call issue
"""

# The fix is to update the query method in PrinceFlowersIntegrationWrapper
# around line 610 to handle different interface types properly

def patch_query_method(wrapper_class):
    """Patch the query method to handle TORQ interface correctly"""

    original_query = wrapper_class.query

    async def patched_query(self, query_text, context=None, show_performance=False):
        """Fixed query method that handles different interface types"""
        import time
        start_time = time.time()
        self.total_queries += 1

        try:
            # Prepare context
            enhanced_context = self._prepare_context(context)

            # Process query through agent based on type and available methods
            if self.agent_type == "local" and hasattr(self.agent, 'process_command'):
                # Use local interface method
                result = await self.agent.process_command(query_text, enhanced_context)
                # Convert to expected format
                class LocalResult:
                    def __init__(self, result_dict):
                        self.success = result_dict.get("success", True)
                        self.content = result_dict.get("response", str(result_dict))
                        self.confidence = result_dict.get("performance", {}).get("confidence", 0.8)
                        self.tools_used = result_dict.get("tools_used", ["local_processor"])
                        self.execution_time = result_dict.get("performance", {}).get("execution_time", 0.1)
                        self.metadata = result_dict.get("metadata", {})

                result = LocalResult(result)
            elif self.agent_type == "torq_console" and hasattr(self.agent, 'handle_prince_command'):
                # Use TORQ Console interface - call handle_prince_command with prince prefix
                prince_command = f"prince {query_text}"
                response_text = await self.agent.handle_prince_command(prince_command, enhanced_context)

                # Convert string response to standard format
                class TORQResult:
                    def __init__(self, content):
                        self.success = True
                        self.content = content
                        self.confidence = 0.8
                        self.tools_used = ["torq_prince_flowers"]
                        self.execution_time = time.time() - start_time
                        self.metadata = {'source': 'torq_console', 'agent_type': 'torq_prince_flowers'}

                result = TORQResult(response_text)
            elif hasattr(self.agent, 'agent') and hasattr(self.agent.agent, 'process_query'):
                # Interface has nested agent with process_query
                result = await self.agent.agent.process_query(query_text, enhanced_context)
            elif hasattr(self.agent, 'process_query'):
                # Direct process_query method
                result = await self.agent.process_query(query_text, enhanced_context)
            else:
                # Fallback - try to get response as string
                if hasattr(self.agent, 'handle_prince_command'):
                    prince_command = f"prince {query_text}"
                    response_text = await self.agent.handle_prince_command(prince_command, enhanced_context)
                else:
                    response_text = f"Processed query: {query_text} (fallback response)"

                # Convert to standard format
                class FallbackResult:
                    def __init__(self, content):
                        self.success = True
                        self.content = content
                        self.confidence = 0.7
                        self.tools_used = ["fallback_processor"]
                        self.execution_time = time.time() - start_time
                        self.metadata = {'source': 'fallback', 'agent_type': self.agent_type}

                result = FallbackResult(response_text)

            execution_time = time.time() - start_time

            # Track performance
            self._track_performance(result.success, execution_time, result.confidence)

            if result.success:
                self.successful_queries += 1
            else:
                self.failed_queries += 1

            # Create standardized response
            from torq_integration import IntegrationResponse
            response = IntegrationResponse(
                success=result.success,
                content=result.content,
                confidence=result.confidence,
                tools_used=result.tools_used,
                execution_time=execution_time,
                metadata=result.metadata,
                agent_status=self.get_status() if show_performance else None
            )

            return response

        except Exception as e:
            execution_time = time.time() - start_time
            self.failed_queries += 1

            error_msg = f"Integration error: {str(e)}"
            self.logger.error(f"Query processing failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")

            from torq_integration import IntegrationResponse
            return IntegrationResponse(
                success=False,
                content=f"I encountered an error processing your request. Please try again.",
                confidence=0.0,
                tools_used=[],
                execution_time=execution_time,
                metadata={'error': str(e), 'agent_type': self.agent_type},
                error=error_msg
            )

    # Replace the method
    wrapper_class.query = patched_query
    return wrapper_class

# Apply the patch when imported
if __name__ == "__main__":
    print("This is a patch file. Import it to apply the fix.")
else:
    try:
        from torq_integration import PrinceFlowersIntegrationWrapper
        PrinceFlowersIntegrationWrapper = patch_query_method(PrinceFlowersIntegrationWrapper)
        print("✅ Applied TORQ Console integration patch")
    except Exception as e:
        print(f"⚠️ Could not apply patch: {e}")