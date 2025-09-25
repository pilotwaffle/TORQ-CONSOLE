"""
Response Agent for Swarm Intelligence System.
Formats and delivers final responses to users with proper formatting and context.
"""

import asyncio
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime


class ResponseAgent:
    """Specialized agent for formatting and delivering final responses."""

    def __init__(self, llm_provider=None):
        self.llm_provider = llm_provider
        self.logger = logging.getLogger(__name__)
        self.agent_id = "response_agent"
        self.capabilities = ["response_formatting", "user_communication", "context_presentation", "source_citation"]

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process response task and create final user response."""
        query = task.get('query', '')
        synthesized_info = task.get('synthesized_info', {})
        context = task.get('context', {})

        self.logger.info(f"ResponseAgent formatting final response for: {query}")

        # Create the final formatted response
        final_response = await self._format_final_response(synthesized_info, query, context)

        return {
            'agent_id': self.agent_id,
            'query': query,
            'final_response': final_response,
            'context': context,
            'next_agent': None,  # End of chain
            'timestamp': datetime.now().isoformat(),
            'handoff_reason': 'task_complete'
        }

    async def _format_final_response(self, synthesized_info: Dict[str, Any], query: str, context: Dict[str, Any]) -> str:
        """Format the final response for the user."""
        summary = synthesized_info.get('summary', '')
        key_insights = synthesized_info.get('key_insights', [])
        sources = synthesized_info.get('sources', [])
        sources_count = synthesized_info.get('sources_count', 0)

        # Build the response
        response_parts = []

        # Main summary
        if summary:
            response_parts.append(summary)
        else:
            response_parts.append(f"I searched for information about '{query}' but encountered some limitations in finding current results.")

        # Add insights if available
        if key_insights and len(key_insights) > 0:
            response_parts.append("\n📋 **Key Information:**")
            for insight in key_insights[:3]:  # Top 3 insights
                source_title = insight.get('source', 'Unknown Source')
                content = insight.get('content', '')
                if content:
                    response_parts.append(f"• **{source_title}:** {content}")

        # Add source information if available
        if sources and sources_count > 0:
            response_parts.append(f"\n🔍 **Sources:** {sources_count} source{'s' if sources_count != 1 else ''} analyzed")

            # Show top sources
            for i, source in enumerate(sources[:3], 1):
                title = source.get('title', 'Unknown Title')
                url = source.get('url', '')
                if url and url != '':
                    response_parts.append(f"{i}. [{title}]({url})")
                else:
                    response_parts.append(f"{i}. {title}")

        # Add helpful context
        response_parts.append(await self._add_helpful_context(query, context))

        # Add timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response_parts.append(f"\n*Search completed at {current_time}*")

        return "\n".join(response_parts)

    async def _add_helpful_context(self, query: str, context: Dict[str, Any]) -> str:
        """Add helpful context and recommendations based on the query type."""
        query_lower = query.lower()

        if any(term in query_lower for term in ['ai news', 'artificial intelligence news', 'ai developments']):
            return self._ai_news_context()
        elif any(term in query_lower for term in ['latest', 'recent', 'current', 'today']):
            return self._recent_info_context()
        elif any(term in query_lower for term in ['research', 'study', 'academic']):
            return self._research_context()
        else:
            return self._general_context()

    def _ai_news_context(self) -> str:
        """Context for AI news queries."""
        return ("\n💡 **For the latest AI news:**\n"
                "• Visit TechCrunch AI, MIT Technology Review, or VentureBeat AI\n"
                "• Check official blogs: OpenAI, Google AI, Anthropic, DeepMind\n"
                "• Follow AI research conferences and paper releases\n"
                "• Monitor AI company announcements and product launches")

    def _recent_info_context(self) -> str:
        """Context for recent information queries."""
        return ("\n💡 **For the most current information:**\n"
                "• Check official news websites and press releases\n"
                "• Look at company blogs and announcements\n"
                "• Search recent academic publications\n"
                "• Use real-time search engines and news aggregators")

    def _research_context(self) -> str:
        """Context for research queries."""
        return ("\n💡 **For research and academic information:**\n"
                "• Search Google Scholar, arXiv, or PubMed\n"
                "• Check university research publications\n"
                "• Look for peer-reviewed journals and conferences\n"
                "• Review official research institution websites")

    def _general_context(self) -> str:
        """General context and recommendations."""
        return ("\n💡 **For more comprehensive information:**\n"
                "• Cross-reference multiple reliable sources\n"
                "• Check for recent updates on official websites\n"
                "• Consider both academic and industry perspectives\n"
                "• Verify information currency and accuracy")

    async def enhance_with_llm(self, response: str, query: str) -> str:
        """Enhance response using LLM if available."""
        if not self.llm_provider:
            return response

        try:
            enhancement_prompt = f"""Please improve this response to make it more helpful and engaging while keeping it accurate:

Original Query: {query}
Current Response: {response}

Please:
1. Keep all factual information intact
2. Improve readability and flow
3. Make it more conversational and helpful
4. Maintain all sources and citations
5. Keep the same general structure"""

            enhanced = await self.llm_provider.query(enhancement_prompt)
            if enhanced and len(enhanced) > len(response) * 0.5:  # Sanity check
                return enhanced
        except Exception as e:
            self.logger.warning(f"LLM enhancement failed: {e}")

        return response

    async def get_capabilities(self) -> List[str]:
        return self.capabilities

    async def get_status(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'capabilities': self.capabilities,
            'llm_provider_available': self.llm_provider is not None
        }