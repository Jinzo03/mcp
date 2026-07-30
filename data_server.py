import time
import httpx
import asyncio
import logging
from fastmcp import FastMCP
from fastmcp.telemetry import get_tracer

# Configure logging
logger = logging.getLogger(__name__)

# Instantiate the sub-server for Data Operations
data_server = FastMCP("CryptoData")

# Thread-safe cache with lock
_CACHE_LOCK = asyncio.Lock()
_CACHE = {
    "trending": {"data": None, "expiry": 0},
    "prices": {}
}
TRENDING_CACHE_TTL_SECS = 300
PRICE_CACHE_TTL_SECS = 60

@data_server.resource("data://trending")
async def get_trending_markets() -> str:
    """Exposes real-time trending cryptos with integrated telemetry tracing."""
    tracer = get_tracer()
    now = time.time()
    
    with tracer.start_as_current_span("get_trending_markets_resource") as span:
        # Thread-safe cache read
        async with _CACHE_LOCK:
            if _CACHE["trending"]["data"] and now < _CACHE["trending"]["expiry"]:
                span.set_attribute("cache.status", "HIT")
                return _CACHE["trending"]["data"]

        span.set_attribute("cache.status", "MISS")
        url = "https://api.coingecko.com/api/v3/search/trending"
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(url, timeout=5.0)
                res.raise_for_status()  # Raise exception for HTTP errors
                data = res.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"CoinGecko API returned HTTP error: {e.response.status_code}")
            span.set_attribute("error.message", f"HTTP {e.response.status_code}")
            return f"Error: CoinGecko API returned status code {e.response.status_code}"
        except httpx.RequestError as e:
            logger.error(f"CoinGecko API request failed: {e}")
            span.set_attribute("error.message", str(e))
            return f"Error: Failed to connect to CoinGecko API - {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error fetching trending markets: {e}")
            span.set_attribute("error.message", str(e))
            return f"Error: Unexpected error fetching trending data - {str(e)}"
        
        # Validate API response structure
        if not isinstance(data, dict) or 'coins' not in data:
            logger.warning(f"Unexpected CoinGecko API response structure: {data}")
            return "Error: Invalid response format from CoinGecko API"
        
        lines = ["=== TRENDING MARKETS ==="]
        for coin in data.get('coins', [])[:5]:
            item = coin.get('item', {})
            if not item:
                continue
            coin_id = item.get('id', 'unknown')
            symbol = item.get('symbol', 'N/A').upper()
            rank = item.get('market_cap_rank', 'N/A')
            lines.append(f"- {coin_id} ({symbol}) | Rank: #{rank}")
        
        formatted = "\n".join(lines)
        
        # Thread-safe cache write
        async with _CACHE_LOCK:
            _CACHE["trending"]["data"] = formatted
            _CACHE["trending"]["expiry"] = now + TRENDING_CACHE_TTL_SECS
        
        return formatted

@data_server.tool()
async def get_crypto_price(coin_id: str) -> float:
    """Fetches clean numerical value of a token price to execute high-speed calculations."""
    tracer = get_tracer()
    coin_clean = coin_id.strip().lower()
    now = time.time()
    
    with tracer.start_as_current_span("get_crypto_price_execution") as span:
        span.set_attribute("target.coin", coin_clean)
        
        # Thread-safe cache read
        async with _CACHE_LOCK:
            if coin_clean in _CACHE["prices"] and now < _CACHE["prices"][coin_clean]["expiry"]:
                span.set_attribute("cache.status", "HIT")
                return _CACHE["prices"][coin_clean]["price"]
            
        span.set_attribute("cache.status", "MISS")
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_clean}&vs_currencies=usd"
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(url, timeout=5.0)
                res.raise_for_status()  # Raise exception for HTTP errors
                data = res.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"CoinGecko API returned HTTP error for {coin_clean}: {e.response.status_code}")
            span.set_attribute("error.message", f"HTTP {e.response.status_code}")
            raise ValueError(f"CoinGecko API returned status code {e.response.status_code} for {coin_clean}")
        except httpx.RequestError as e:
            logger.error(f"CoinGecko API request failed for {coin_clean}: {e}")
            span.set_attribute("error.message", str(e))
            raise ValueError(f"Failed to connect to CoinGecko API for {coin_clean}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching price for {coin_clean}: {e}")
            span.set_attribute("error.message", str(e))
            raise ValueError(f"Unexpected error fetching price for {coin_clean}: {str(e)}")
        
        # Validate response structure
        if not isinstance(data, dict):
            logger.warning(f"Invalid response format for {coin_clean}: {data}")
            raise ValueError(f"Invalid response format from CoinGecko API for {coin_clean}")
        
        price_data = data.get(coin_clean, {})
        if not isinstance(price_data, dict) or 'usd' not in price_data:
            logger.warning(f"Price data not found for {coin_clean} in response: {data}")
            raise ValueError(f"Price data not available for {coin_clean}")
        
        try:
            price = float(price_data['usd'])
        except (TypeError, ValueError) as e:
            logger.error(f"Invalid price value for {coin_clean}: {price_data.get('usd')}")
            raise ValueError(f"Invalid price value received for {coin_clean}")
        
        # Thread-safe cache write
        async with _CACHE_LOCK:
            _CACHE["prices"][coin_clean] = {"price": price, "expiry": now + PRICE_CACHE_TTL_SECS}
        
        return price

# =====================================================================
# CODE EXECUTION FILTERING MODE (Saves LLM context window tokens)
# =====================================================================
@data_server.tool()
async def query_and_filter_market_data(coin_ids: str, threshold_price: float) -> str:
    """
    Advanced Code-API filtering module. Evaluates massive array profiles locally
    and passes only target components crossing specified pricing thresholds to the LLM.
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("code_api_data_filtering") as span:
        targets = [coin.strip().lower() for coin in coin_ids.split(",") if coin.strip()]
        span.set_attribute("filter.input_count", len(targets))
        
        filtered_results = []
        for coin in targets:
            price = await get_crypto_price(coin)
            if price >= threshold_price:
                filtered_results.append(f" {coin.upper()}: ${price:,.2f} USD (Crossed threshold of ${threshold_price:,.2f})")
        
        span.set_attribute("filter.output_count", len(filtered_results))
        return "\n".join(filtered_results) if filtered_results else "No tokens matched filtering threshold parameters."
