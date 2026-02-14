"""
Cryptocurrency Price API Module for TORQ Console

Provides live BTC/USD price fetching using CoinGecko API
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp as aiohttp

class CryptoPriceAPI:
    """Cryptocurrency price API handler"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.coingecko_base = "https://api.coingecko.com/api/v3"

    async def get_btc_price(self) -> Dict[str, Any]:
        """
        Fetch current Bitcoin (BTC) price in USD

        Returns:
            {
                "bitcoin": {
                    "usd": float_price,
                    "usd_24h_change": float_change_24h,
                    "last_updated": str
                }
            }

        Raises:
            Exception: If API request fails
        """
        url = f"{self.coingecko_base}/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"

        self.logger.info(f"Fetching BTC price from {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()

                        if "bitcoin" in data and "usd" in data["bitcoin"]:
                            btc_data = data["bitcoin"]
                            result = {
                                "bitcoin": {
                                    "usd": btc_data["usd"],
                                    "usd_24h_change": btc_data.get("usd_24h_change", 0)
                                },
                                "last_updated": btc_data.get("last_updated_at", "Unknown")
                            }
                            self.logger.info(f"BTC Price: ${btc_data['usd']:.2f}")
                            return result
                        else:
                            self.logger.warning(f"Unexpected response format: {data}")
                            return {"error": "Invalid response format", "raw": data}
                    else:
                        error_text = await response.text()
                        self.logger.error(f"CoinGecko API error: {response.status} - {error_text}")
                        return {"error": f"API error: {response.status}", "details": error_text}
        except asyncio.TimeoutError:
            self.logger.error("CoinGecko API timeout")
            return {"error": "Request timeout", "details": "API took too long to respond"}
        except Exception as e:
            self.logger.error(f"Error fetching BTC price: {e}")
            return {"error": str(e), "details": str(e)}

    async def get_multiple_prices(self, symbols: list) -> Dict[str, Any]:
        """
        Fetch prices for multiple cryptocurrencies

        Args:
            symbols: List of cryptocurrency symbols (e.g., ['bitcoin', 'ethereum'])

        Returns:
            Dict mapping symbols to price data
        """
        ids = ",".join(symbols)
        url = f"{self.coingecko_base}/simple/price?ids={ids}&vs_currencies=usd"

        self.logger.info(f"Fetching prices for: {symbols}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {"error": f"API error: {response.status}", "details": error_text}
        except asyncio.TimeoutError:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": str(e), "details": str(e)}


# Global instance for easy access
_crypto_api: Optional[CryptoPriceAPI] = None

def get_crypto_api() -> CryptoPriceAPI:
    """Get or create the crypto price API instance"""
    global _crypto_api
    if _crypto_api is None:
        _crypto_api = CryptoPriceAPI()
    return _crypto_api

async def get_btc_price() -> Dict[str, Any]:
    """Convenience function to get BTC price"""
    api = get_crypto_api()
    return await api.get_btc_price()
