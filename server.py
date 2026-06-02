from mcp.server.fastmcp import FastMCP
import requests

# Initialize the MCP Server
mcp = FastMCP("LiveMarketAnalyzer")

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

# The server runs over standard input/output (stdio), which is the MCP standard
if __name__ == "__main__":
    mcp.run()