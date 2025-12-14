#!/usr/bin/env python3
"""
Prince Flowers Integration Wrapper for TORQ Console
Provides compatibility layer between console and Prince Flowers agent
"""

import asyncio
import sys
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

# Add TORQ to path for proper imports
sys.path.insert(0, "E:/TORQ-CONSOLE")

class PrinceFlowersIntegrationWrapper:
    """Wrapper for Prince Flowers agent with query interface compatibility"""

    def __init__(self):
        self.agent_name = "prince_flowers"
        self.agent_display_name = "Prince Flowers v2.0"
        self.agent_description = "Enhanced AI assistant with memory and meta-learning"
        self.conversation_history = []
        self.performance_metrics = {
            "queries_processed": 0,
            "successful_responses": 0,
            "avg_response_time": 0.0,
            "memory_usage": 0
        }

        # Import Prince Flowers agent
        try:
            from torq_console.agents.marvin_prince_flowers import MarvinPrinceFlowers
            self.prince_flowers = MarvinPrinceFlowers()
            self.available = True
        except ImportError as e:
            print(f"Warning: Could not import Prince Flowers agent: {e}")
            self.prince_flowers = None
            self.available = False

    async def query(self, query: str, context: Optional[Dict[str, Any]] = None, show_performance: bool = False) -> Dict[str, Any]:
        """
        Process a query using Prince Flowers agent with console-compatible interface

        Args:
            query: The user's query
            context: Optional context information
            show_performance: Whether to include performance metrics

        Returns:
            Dictionary with response, metadata, and optional performance info
        """
        start_time = datetime.now()

        try:
            if not self.available or self.prince_flowers is None:
                return {
                    "response": "Prince Flowers agent is not available. Please check your configuration.",
                    "success": False,
                    "error": "Agent not available",
                    "agent": self.agent_display_name
                }

            # Use the chat_with_memory method if available, otherwise use regular chat
            if hasattr(self.prince_flowers, 'chat_with_memory'):
                # Call the chat_with_memory method
                result = await self.prince_flowers.chat_with_memory(query)
                response = result.get('response', str(result))
            else:
                # Fallback to a simple response
                response = f"Prince Flowers: {query}"

            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()

            # Update metrics
            self.performance_metrics["queries_processed"] += 1
            self.performance_metrics["successful_responses"] += 1
            self.performance_metrics["avg_response_time"] = (
                (self.performance_metrics["avg_response_time"] * (self.performance_metrics["queries_processed"] - 1) + response_time) /
                self.performance_metrics["queries_processed"]
            )

            # Store in conversation history
            self.conversation_history.append({
                "timestamp": start_time.isoformat(),
                "query": query,
                "response": response,
                "response_time": response_time
            })

            # Prepare result
            result = {
                "response": response,
                "success": True,
                "agent": self.agent_display_name,
                "timestamp": start_time.isoformat(),
                "query_id": len(self.conversation_history)
            }

            # Add performance metrics if requested
            if show_performance:
                result["performance"] = {
                    "response_time": f"{response_time:.2f}s",
                    "queries_processed": self.performance_metrics["queries_processed"],
                    "success_rate": f"{(self.performance_metrics['successful_responses'] / self.performance_metrics['queries_processed'] * 100):.1f}%",
                    "avg_response_time": f"{self.performance_metrics['avg_response_time']:.2f}s"
                }

            # Add context if provided
            if context:
                result["context_used"] = True
                result["context_summary"] = {
                    "keys": list(context.keys()) if isinstance(context, dict) else [],
                    "size": len(str(context))
                }

            return result

        except Exception as e:
            # Handle errors gracefully
            return {
                "response": f"Error processing query: {str(e)}",
                "success": False,
                "error": str(e),
                "agent": self.agent_display_name,
                "timestamp": start_time.isoformat()
            }

    async def chat(self, message: str) -> str:
        """Simple chat interface for compatibility"""
        result = await self.query(message)
        return result.get("response", "")

    def get_capabilities(self) -> List[str]:
        """Get list of agent capabilities"""
        if not self.available:
            return ["Basic responses (agent not fully available)"]

        return [
            "Multi-turn conversation with memory",
            "Context-aware responses",
            "Task assistance and guidance",
            "Code generation and review",
            "Debugging support",
            "Architecture design",
            "Learning from interactions",
            "Meta-cognitive reasoning",
            "Performance tracking"
        ]

    def get_status(self) -> Dict[str, Any]:
        """Get agent status information"""
        return {
            "name": self.agent_display_name,
            "available": self.available,
            "version": "2.0",
            "capabilities": self.get_capabilities(),
            "conversation_count": len(self.conversation_history),
            "performance_metrics": self.performance_metrics.copy(),
            "last_active": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }

    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history.clear()
        self.performance_metrics = {
            "queries_processed": 0,
            "successful_responses": 0,
            "avg_response_time": 0.0,
            "memory_usage": 0
        }

    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:] if self.conversation_history else []

# Singleton instance for console use
_prince_flowers_instance = None

def get_prince_flowers_agent() -> PrinceFlowersIntegrationWrapper:
    """Get singleton instance of Prince Flowers agent"""
    global _prince_flowers_instance
    if _prince_flowers_instance is None:
        _prince_flowers_instance = PrinceFlowersIntegrationWrapper()
    return _prince_flowers_instance

# Make agent available at module level for import
prince_flowers_agent = get_prince_flowers_agent()

# For backward compatibility
async def query_prince_flowers(query: str, context: Optional[Dict[str, Any]] = None, show_performance: bool = False) -> Dict[str, Any]:
    """Convenience function for querying Prince Flowers"""
    agent = get_prince_flowers_agent()
    return await agent.query(query, context, show_performance)