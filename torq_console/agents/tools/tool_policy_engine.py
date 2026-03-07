"""
Tool Policy Engine - Phase 3

Enforces tool execution policies for TORQ Console.

Policies:
- OPTIONAL: LLM may call tool (default)
- PREFERRED: System attempts tool first, fallback allowed
- REQUIRED: Tool must run before response (for realtime queries)

This ensures that queries like "What is the current temp in Austin Texas?"
always trigger a live data lookup before the model responds.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
import asyncio
import httpx

logger = logging.getLogger(__name__)


class ToolPolicy(str, Enum):
    """Tool execution policy."""
    OPTIONAL = "optional"      # LLM decides
    PREFERRED = "preferred"    # Try tool first, fallback allowed
    REQUIRED = "required"      # Must run tool before response


class ToolClass(str, Enum):
    """Tool categories."""
    WEATHER = "weather"
    FINANCE = "finance"
    NEWS = "news"
    WEB_SEARCH = "web_search"


@dataclass
class ToolResult:
    """Structured result from tool execution."""
    success: bool
    tool_class: str
    data: Dict[str, Any]
    raw_response: str = ""
    error: Optional[str] = None
    latency_ms: int = 0


@dataclass
class ToolPolicyDecision:
    """
    Tool policy decision based on routing override.

    When force_research=True, tools become REQUIRED.
    """
    policy: ToolPolicy
    tool_classes: List[ToolClass]
    reason: str

    def __bool__(self) -> bool:
        """True if tools should be executed."""
        return self.policy in (ToolPolicy.PREFERRED, ToolPolicy.REQUIRED)


# ============================================================================
# Weather Tool
# ============================================================================

class WeatherTool:
    """
    Live weather data retrieval.

    Uses wttr.in API (no API key required) for current conditions.
    """

    BASE_URL = "https://wttr.in"

    async def run(self, query: str, location: Optional[str] = None) -> ToolResult:
        """
        Execute weather lookup.

        Args:
            query: Original user query
            location: Extracted location (defaults to parsing from query)

        Returns:
            ToolResult with structured weather data
        """
        import time
        start = time.time()

        # Extract location from query if not provided
        if not location:
            location = self._extract_location(query)

        if not location:
            return ToolResult(
                success=False,
                tool_class=ToolClass.WEATHER,
                data={},
                error="Could not determine location from query"
            )

        try:
            # Use wttr.in format API (returns JSON)
            url = f"{self.BASE_URL}/{location}?format=j1"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

            if response.status_code == 200:
                data = response.json()

                # wttr.in returns current_condition as a list
                current_list = data.get("current_condition", [])
                if current_list and isinstance(current_list, list):
                    current = current_list[0]
                else:
                    current = {}

                # Safely extract values with defaults
                temp_c = current.get("temp_C")
                temp_f = current.get("temp_F")
                humidity = current.get("humidity")
                wind = current.get("windspeedMiles")

                # Handle weatherDesc which might be a dict or string
                weather_desc_obj = current.get("weatherDesc", [])
                if isinstance(weather_desc_obj, dict):
                    condition = weather_desc_obj.get("value", "Unknown")
                elif isinstance(weather_desc_obj, list) and weather_desc_obj:
                    condition = weather_desc_obj[0].get("value", "Unknown") if isinstance(weather_desc_obj[0], dict) else str(weather_desc_obj[0])
                else:
                    condition = str(weather_desc_obj) if weather_desc_obj else "Unknown"

                result = ToolResult(
                    success=True,
                    tool_class=ToolClass.WEATHER,
                    data={
                        "location": location,
                        "temperature_c": int(temp_c) if temp_c else 0,
                        "temperature_f": int(temp_f) if temp_f else 0,
                        "condition": condition,
                        "humidity": int(humidity) if humidity else 0,
                        "wind_speed_mph": wind if wind else "Unknown",
                        "source": "wttr.in"
                    },
                    raw_response=f"{location}: {temp_f}F {condition}",
                    latency_ms=int((time.time() - start) * 1000)
                )

                logger.info(
                    f"WeatherTool: {location} - "
                    f"{result.data['temperature_f']}F {result.data['condition']}"
                )

                return result
            else:
                return ToolResult(
                    success=False,
                    tool_class=ToolClass.WEATHER,
                    data={},
                    error=f"Weather API returned {response.status_code}",
                    latency_ms=int((time.time() - start) * 1000)
                )

        except Exception as e:
            logger.error(f"WeatherTool error: {e}")
            return ToolResult(
                success=False,
                tool_class=ToolClass.WEATHER,
                data={},
                error=str(e),
                latency_ms=int((time.time() - start) * 1000)
            )

    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query."""
        query_lower = query.lower()

        # Common patterns
        for pattern in ["current temp in", "temperature in", "weather in"]:
            if pattern in query_lower:
                # Get everything after the pattern
                parts = query_lower.split(pattern)
                if len(parts) > 1:
                    location = parts[1].strip().split()[0]  # First word after pattern
                    # Clean up common words
                    location = location.rstrip("?!.,;")
                    return location.capitalize()

        # Look for city names
        cities = {
            "austin": "Austin",
            "dallas": "Dallas",
            "houston": "Houston",
            "new york": "New York",
            "london": "London",
            "paris": "Paris",
            "tokyo": "Tokyo",
            "san francisco": "San Francisco",
            "seattle": "Seattle",
            "boston": "Boston",
            "chicago": "Chicago",
            "miami": "Miami",
            "denver": "Denver",
        }

        for city_key, city_name in cities.items():
            if city_key in query_lower:
                return city_name

        # Check for state abbreviations
        import re
        state_match = re.search(r'\b(TX|CA|NY|FL|IL|PA|OH|GA|NC)\b', query, re.IGNORECASE)
        if state_match:
            # Look for city before state
            before_state = query[:state_match.start()].strip().split()[-1]
            if before_state:
                return f"{before_state.capitalize()} {state_match.group(1).upper()}"

        return None


# ============================================================================
# Finance Tool
# ============================================================================

class FinanceTool:
    """
    Live finance/crypto data retrieval.

    Uses public APIs for stock/crypto prices.
    """

    async def run(self, query: str) -> ToolResult:
        """
        Execute finance lookup.

        Args:
            query: Original user query

        Returns:
            ToolResult with structured finance data
        """
        import time
        start = time.time()

        # Detect what type of finance query
        query_lower = query.lower()

        # Crypto symbols
        crypto_map = {
            "bitcoin": "BTC",
            "btc": "BTC",
            "ethereum": "ETH",
            "eth": "ETH",
        }

        # Stock symbols (simple mapping for common stocks)
        stock_map = {
            "nvda": "NVDA",
            "nvidia": "NVDA",
            "aapl": "AAPL",
            "apple": "AAPL",
            "msft": "MSFT",
            "microsoft": "MSFT",
            "googl": "GOOGL",
            "google": "GOOGL",
            "amzn": "AMZN",
            "amazon": "AMZN",
            "tsla": "TSLA",
            "tesla": "TSLA",
            "meta": "META",
        }

        symbol = None
        asset_type = None

        # Check for crypto
        for key, sym in crypto_map.items():
            if key in query_lower:
                symbol = sym
                asset_type = "crypto"
                break

        # Check for stocks
        if not symbol:
            for key, sym in stock_map.items():
                if key in query_lower:
                    symbol = sym
                    asset_type = "stock"
                    break

        # Check for treasury
        if "treasury" in query_lower or ("10-year" in query_lower or "10 year" in query_lower):
            return await self._get_treasury_yield(query)

        if not symbol:
            # Generic finance query - use web search result format
            return ToolResult(
                success=False,
                tool_class=ToolClass.FINANCE,
                data={},
                error="Could not identify specific asset. Try specifying symbol (e.g., BTC, AAPL).",
                latency_ms=int((time.time() - start) * 1000)
            )

        if asset_type == "crypto":
            return await self._get_crypto_price(symbol, query, start)
        else:
            return await self._get_stock_price(symbol, query, start)

    async def _get_crypto_price(self, symbol: str, query: str, start_time: float) -> ToolResult:
        """Get crypto price from public API."""
        try:
            # Use CoinGecko API (free, no key)
            symbol_map = {"BTC": "bitcoin", "ETH": "ethereum"}
            coin_id = symbol_map.get(symbol, symbol.lower())

            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"

            import time
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers={"User-Agent": "TORQ-Console/1.0"})

            if response.status_code == 200:
                data = response.json()

                if coin_id in data:
                    price_data = data[coin_id]
                    price = price_data.get("usd", 0)
                    change_24h = price_data.get("usd_24h_change", 0)

                    return ToolResult(
                        success=True,
                        tool_class=ToolClass.FINANCE,
                        data={
                            "symbol": symbol,
                            "asset_type": "crypto",
                            "price_usd": price,
                            "change_24h_percent": round(change_24h, 2),
                            "source": "CoinGecko"
                        },
                        raw_response=f"{symbol} is trading at ${price:,.2f} ({change_24h:+.2f}%)",
                        latency_ms=int((time.time() - start_time) * 1000)
                    )

            return ToolResult(
                success=False,
                tool_class=ToolClass.FINANCE,
                data={},
                error=f"Could not fetch price for {symbol} (API returned {response.status_code})",
                latency_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            logger.error(f"FinanceTool crypto error: {e}")
            import time
            return ToolResult(
                success=False,
                tool_class=ToolClass.FINANCE,
                data={},
                error=str(e),
                latency_ms=int((time.time() - start_time) * 1000)
            )

    async def _get_stock_price(self, symbol: str, query: str, start_time: float) -> ToolResult:
        """Get stock price (simplified - uses Yahoo Finance via scraping)."""
        # For now, return a structured response indicating stock lookup
        # Real implementation would use Alpha Vantage or similar
        return ToolResult(
            success=False,
            tool_class=ToolClass.FINANCE,
            data={"symbol": symbol, "asset_type": "stock"},
            error=f"Stock price lookup for {symbol} requires API key. Use crypto queries for live data.",
            latency_ms=int((asyncio.get_event_loop().time() - start_time) * 1000)
        )

    async def _get_treasury_yield(self, query: str) -> ToolResult:
        """Get treasury yield data."""
        import time
        start = time.time()

        try:
            # Use FRED API or treasury.gov for real data
            # For now, use a web search fallback approach
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use DuckDuckGo for instant answer
                url = "https://api.duckduckgo.com/"
                params = {
                    "q": "10 year treasury yield current",
                    "format": "json"
                }

                response = await client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    abstract = data.get("AbstractText", "")

                    # Try to extract percentage from response
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*%', abstract)
                    if match:
                        yield_value = float(match.group(1))

                        return ToolResult(
                            success=True,
                            tool_class=ToolClass.FINANCE,
                            data={
                                "security": "10-Year Treasury",
                                "yield_percent": yield_value,
                                "source": "DuckDuckGo"
                            },
                            raw_response=abstract,
                            latency_ms=int((time.time() - start) * 1000)
                        )

            return ToolResult(
                success=False,
                tool_class=ToolClass.FINANCE,
                data={},
                error="Could not fetch current treasury yield",
                latency_ms=int((time.time() - start) * 1000)
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool_class=ToolClass.FINANCE,
                data={},
                error=str(e),
                latency_ms=int((time.time() - start) * 1000)
            )


# ============================================================================
# News Tool
# ============================================================================

class NewsTool:
    """
    Live news retrieval.

    Uses web search APIs to get latest news.
    """

    async def run(self, query: str, topic: Optional[str] = None) -> ToolResult:
        """
        Execute news lookup.

        Args:
            query: Original user query
            topic: Specific news topic (extracted from query)

        Returns:
            ToolResult with news headlines
        """
        import time
        start = time.time()

        if not topic:
            topic = self._extract_topic(query)

        try:
            # Use web search for news
            # This would integrate with Tavily or similar in production
            search_query = f"latest news {topic}" if topic else query

            # For now, return structured placeholder
            # Real implementation calls web search API
            return ToolResult(
                success=False,
                tool_class=ToolClass.NEWS,
                data={"topic": topic, "query": search_query},
                error="News tool requires web search integration (Tavily/Brave)",
                latency_ms=int((time.time() - start) * 1000)
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool_class=ToolClass.NEWS,
                data={},
                error=str(e),
                latency_ms=int((time.time() - start) * 1000)
            )

    def _extract_topic(self, query: str) -> Optional[str]:
        """Extract news topic from query."""
        query_lower = query.lower()

        # Remove common news query patterns
        patterns = [
            "latest news",
            "latest",
            "news about",
            "what happened with",
            "what's happening with",
        ]

        topic = query_lower
        for pattern in patterns:
            topic = topic.replace(pattern, "")

        topic = topic.strip()
        return topic if topic else None


# ============================================================================
# Tool Policy Engine
# ============================================================================

class ToolPolicyEngine:
    """
    Enforces tool execution policies.

    This is the Phase 3 core - it ensures that when routing override
    forces research, tools are ACTUALLY executed before LLM response.
    """

    def __init__(self):
        self.weather_tool = WeatherTool()
        self.finance_tool = FinanceTool()
        self.news_tool = NewsTool()

    def decide_policy(
        self,
        routing_override_reason: Optional[str],
        query: str
    ) -> ToolPolicyDecision:
        """
        Determine tool policy based on routing override.

        Args:
            routing_override_reason: Reason from Phase 2 routing
            query: Original user query

        Returns:
            ToolPolicyDecision with policy and tool classes
        """
        query_lower = query.lower()

        # Map routing reasons to tool policies
        if routing_override_reason == "realtime_finance":
            # Check for weather patterns
            if any(w in query_lower for w in ["temp", "temperature", "weather", "forecast"]):
                return ToolPolicyDecision(
                    policy=ToolPolicy.REQUIRED,
                    tool_classes=[ToolClass.WEATHER],
                    reason="Weather query detected"
                )

            # Finance queries
            return ToolPolicyDecision(
                policy=ToolPolicy.REQUIRED,
                tool_classes=[ToolClass.FINANCE],
                reason="Finance query detected"
            )

        elif routing_override_reason == "current_lookup":
            # Check for weather
            if any(w in query_lower for w in ["temp", "temperature", "weather", "forecast"]):
                return ToolPolicyDecision(
                    policy=ToolPolicy.REQUIRED,
                    tool_classes=[ToolClass.WEATHER],
                    reason="Weather lookup"
                )

            # Default to web search for other lookups
            return ToolPolicyDecision(
                policy=ToolPolicy.REQUIRED,
                tool_classes=[ToolClass.WEB_SEARCH],
                reason="Current lookup requires search"
            )

        elif routing_override_reason == "current_news":
            return ToolPolicyDecision(
                policy=ToolPolicy.REQUIRED,
                tool_classes=[ToolClass.NEWS, ToolClass.WEB_SEARCH],
                reason="News query detected"
            )

        elif routing_override_reason == "latest_ai":
            return ToolPolicyDecision(
                policy=ToolPolicy.REQUIRED,
                tool_classes=[ToolClass.NEWS, ToolClass.WEB_SEARCH],
                reason="AI news query"
            )

        # Default: no specific policy
        return ToolPolicyDecision(
            policy=ToolPolicy.OPTIONAL,
            tool_classes=[],
            reason="No tool requirement"
        )

    async def execute_tool_chain(
        self,
        decision: ToolPolicyDecision,
        query: str
    ) -> List[ToolResult]:
        """
        Execute the tool chain based on policy decision.

        Args:
            decision: Tool policy decision
            query: Original user query

        Returns:
            List of ToolResult from executed tools
        """
        if decision.policy == ToolPolicy.OPTIONAL:
            return []

        results = []

        for tool_class in decision.tool_classes:
            try:
                if tool_class == ToolClass.WEATHER:
                    result = await self.weather_tool.run(query)
                    results.append(result)

                elif tool_class == ToolClass.FINANCE:
                    result = await self.finance_tool.run(query)
                    results.append(result)

                elif tool_class == ToolClass.NEWS:
                    result = await self.news_tool.run(query)
                    results.append(result)

                elif tool_class == ToolClass.WEB_SEARCH:
                    # Web search would be handled by Tavily integration
                    # For now, return placeholder
                    results.append(ToolResult(
                        success=False,
                        tool_class=ToolClass.WEB_SEARCH,
                        data={},
                        error="Web search requires Tavily API key",
                        latency_ms=0
                    ))

            except Exception as e:
                logger.error(f"Tool execution error for {tool_class}: {e}")
                results.append(ToolResult(
                    success=False,
                    tool_class=tool_class,
                    data={},
                    error=str(e),
                    latency_ms=0
                ))

        return results

    def format_tool_results_for_llm(self, results: List[ToolResult], query: str) -> str:
        """
        Format tool results for LLM context.

        Args:
            results: List of tool execution results
            query: Original user query

        Returns:
            Formatted string for LLM prompt
        """
        if not results:
            return ""

        successful = [r for r in results if r.success]

        if not successful:
            return (
                "I attempted to retrieve live data but encountered errors. "
                "Please try again or provide more specific information."
            )

        context_parts = []
        for result in successful:
            if result.tool_class == ToolClass.WEATHER:
                data = result.data
                context_parts.append(
                    f"WEATHER DATA for {data.get('location', 'Unknown')}: "
                    f"Temperature: {data.get('temperature_f')}°F ({data.get('temperature_c')}°C), "
                    f"Condition: {data.get('condition')}, "
                    f"Humidity: {data.get('humidity')}%, "
                    f"Wind: {data.get('wind_speed_mph')} mph"
                )

            elif result.tool_class == ToolClass.FINANCE:
                data = result.data
                if data.get('asset_type') == 'crypto':
                    context_parts.append(
                        f"FINANCE DATA: {data.get('symbol')} is trading at "
                        f"${data.get('price_usd'):,.2f} "
                        f"({data.get('change_24h_change_percent', 0):+.2f}% 24h)"
                    )
                else:
                    context_parts.append(f"FINANCE DATA: {result.raw_response}")

            elif result.tool_class == ToolClass.NEWS:
                context_parts.append(f"NEWS DATA: {result.raw_response}")

            else:
                context_parts.append(f"DATA: {result.raw_response}")

        return "\n\n".join(context_parts)


# ============================================================================
# Standalone Test
# ============================================================================

if __name__ == "__main__":
    import sys
    import io

    # Ensure UTF-8 output for Windows
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    async def test_tool_engine():
        """Test the tool policy engine."""
        engine = ToolPolicyEngine()

        test_queries = [
            ("What is the current temp in Austin Texas", "current_lookup"),
            ("Bitcoin price today", "realtime_finance"),
            ("Latest AI news", "current_news"),
            ("Explain quantum computing", None),
        ]

        print("=" * 60)
        print("Tool Policy Engine Test")
        print("=" * 60)

        for query, override_reason in test_queries:
            print(f"\nQuery: {query}")
            print(f"Override: {override_reason}")

            decision = engine.decide_policy(override_reason, query)
            print(f"Policy: {decision.policy}")
            print(f"Tool classes: {decision.tool_classes}")

            if decision:
                results = await engine.execute_tool_chain(decision, query)

                for result in results:
                    if result.success:
                        print(f"  [OK] {result.tool_class}: {result.data}")
                    else:
                        print(f"  [FAIL] {result.tool_class}: {result.error}")

    # Run test
    asyncio.run(test_tool_engine())
