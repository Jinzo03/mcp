from mcp.server.fastmcp import FastMCP
import requests

# Initialize the MCP Server
mcp = FastMCP("LiveMarketAnalyzer")

# ==========================================
# 1. RESOURCE: Dynamic Market Data
# ==========================================
@mcp.resource("market://trending")
def get_trending_markets() -> str:
    """
    Exposes a real-time, read-only data stream of the top trending 
    cryptocurrencies on the market right now.
    """
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        lines = ["=== LIVE TRENDING MARKET DASHBOARD ==="]
        for idx, coin in enumerate(data.get('coins', [])[:5], 1):
            item = coin['item']
            lines.append(f"{idx}. {item['name']} ({item['symbol'].upper()})")
            lines.append(f"   Market Cap Rank: #{item.get('market_cap_rank', 'N/A')}")
            lines.append(f"   Price (BTC): {item.get('price_btc', 0):.8f} BTC")
            lines.append("-" * 30)
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error generation trending resource: {str(e)}"


# ==========================================
# 2. TOOL: Live Price Fetcher (Unchanged)
# ==========================================
@mcp.tool()
def get_crypto_price(coin_id: str) -> str:
    """
    Fetches the live, real-time price of a cryptocurrency in USD.
    Use common coin IDs like 'bitcoin', 'ethereum', or 'solana'.
    """
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if coin_id in data:
            price = data[coin_id]['usd']
            return f"The current live price of {coin_id.capitalize()} is ${price:,.2f} USD."
        else:
            return f"Error: Could not find live data for '{coin_id}'. Ensure it is a valid CoinGecko ID."
            
    except requests.exceptions.RequestException as e:
        return f"API Error while fetching data: {str(e)}"

# ==========================================
# 3. PROMPT: Structured Analysis Template
# ==========================================
@mcp.prompt()
def crypto_analyst_persona(strategy_type: str = "aggressive") -> str:
    """
    Provides a standardized system prompt blueprint for an AI agent 
    to conduct professional cryptocurrency market assessments.
    """
    return f"""
You are a world-class Quantitative Crypto Asset Analyst specializing in a {strategy_type} market strategy.

Your workflow MUST be as follows:
1. First, inspect the live market context by reading the 'market://trending' resource.
2. Identify the most relevant asset from that data or ask the user for a specific coin.
3. Call the 'get_crypto_price' tool to fetch the absolute latest price metrics for that asset.
4. Synthesize the raw data into an executive risk report detailing entry targets and trailing stop-losses.

Maintain a highly analytical, non-emotional, data-driven tone. Do not give direct financial advice, but provide institutional-grade scenarios.
"""

if __name__ == "__main__":
    mcp.run()