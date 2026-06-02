import time
import httpx
from fastmcp import FastMCP
from fastmcp.telemetry import get_tracer

# Instantiate the sub-server for Data Operations
data_server = FastMCP("CryptoData")

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
        if _CACHE["trending"]["data"] and now < _CACHE["trending"]["expiry"]:
            span.set_attribute("cache.status", "HIT")
            return _CACHE["trending"]["data"]

        span.set_attribute("cache.status", "MISS")
        url = "https://api.coingecko.com/api/v3/search/trending"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=5.0)
            data = res.json()
        
        lines = ["=== TRENDING MARKETS ==="]
        for coin in data.get('coins', [])[:5]:
            item = coin['item']
            lines.append(f"- {item['id']} ({item['symbol'].upper()}) | Rank: #{item.get('market_cap_rank', 'N/A')}")
        
        formatted = "\n".join(lines)
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
        
        if coin_clean in _CACHE["prices"] and now < _CACHE["prices"][coin_clean]["expiry"]:
            span.set_attribute("cache.status", "HIT")
            return _CACHE["prices"][coin_clean]["price"]
            
        span.set_attribute("cache.status", "MISS")
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_clean}&vs_currencies=usd"
        async with httpx.AsyncClient() as client:
            res = await client.get(url, timeout=5.0)
            data = res.json()
            
        price = float(data.get(coin_clean, {}).get('usd', 0.0))
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
