from fastmcp import FastMCP, Context
from pydantic import BaseModel
import requests

# Initialize the standalone high-performance MCP Server
mcp = FastMCP("LiveMarketAnalyzer")

# =====================================================================
# 1. RESOURCE: Dynamic Market Data Stream
# =====================================================================
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
        return f"Error generating trending resource: {str(e)}"


# =====================================================================
# 2. TOOL: Live Price Fetcher
# =====================================================================
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


# =====================================================================
# 3. PROMPT: Structured Analysis Template
# =====================================================================
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


# =====================================================================
# 4. ADVANCED ORCHESTRATION: The Ultimate Protocol Pipeline
# =====================================================================

# Define a strict schema for the UI to render during Elicitation
class RiskMitigationResponse(BaseModel):
    apply_mitigation: bool

@mcp.tool()
async def advanced_crypto_quant_pipeline(coin_id: str, ctx: Context) -> str:
    """
    An enterprise-grade orchestration pipeline demonstrating Sampling, Elicitation,
    Progress reporting, Native Session State, and Structured Logging.
    """
    # 1. LOGGING TAB: Live streaming diagnostics back to the client UI
    await ctx.info(f"🚀 Initializing Ultra Pipeline for asset: {coin_id}")
    await ctx.debug("Establishing protocol handshake and verifying network sockets...")

    # 2. PROGRESS TAB: Visually update long-running step processing
    await ctx.report_progress(1, 4, "Step 1/4: Fetching underlying market depth data...")
    market_depth = f"Raw Order Book Depth for {coin_id}: High liquidity detected near historical resistance."
    await ctx.info("Market depth data successfully ingested.")

    # 3. ELICITATION TAB: Force the UI to render an interactive form natively
    await ctx.report_progress(2, 4, "Step 2/4: Awaiting interactive user feedback...")
    
    # FIX: Changed "schema=" keyword to "response_type="
    elicit_result = await ctx.elicit(
        message=f"Critical threshold reached for {coin_id}. Do you want to apply strict risk mitigation protocols?",
        response_type=RiskMitigationResponse
    )
    
    if elicit_result.action != "accept":
        await ctx.warning("Elicitation workflow aborted or declined by the user.")
        return "Pipeline execution forcefully halted: Elicitation requirements not met."
        
    risk_mitigation = elicit_result.data.apply_mitigation
    await ctx.info(f"Risk mitigation applied: {risk_mitigation}")

    # 4. SAMPLING TAB: Borrow the client LLM's brain natively using modern FastMCP APIs
    await ctx.report_progress(3, 4, "Step 3/4: Delegating synthesis to client LLM via Sampling...")
    prompt_msg = f"Analyze this market state: '{market_depth}'. Strict risk settings applied: {risk_mitigation}. Synthesize into 1 sentence."
    
    try:
        # Standalone FastMCP natively handles this seamlessly
        sampling_result = await ctx.sample(prompt_msg, max_tokens=100)
        ai_synthesis = sampling_result.text or "No text returned from model."
    except Exception as e:
        ai_synthesis = f"Sampling skipped (Inspector doesn't have an active LLM backend): {str(e)}"
        
    await ctx.info("Sampling extraction complete. Returning execution control to server.")

    # 5. NATIVE SESSION STATE: Persistent state natively built into the protocol context
    await ctx.report_progress(4, 4, "Step 4/4: Finalizing pipeline and saving session metadata...")
    
    run_count = (await ctx.get_state("pipeline_runs") or 0) + 1
    await ctx.set_state("pipeline_runs", run_count)
    
    await ctx.info(f"Pipeline complete. Total session activations: {run_count}")
    
    return (
        f"--- QUANT PIPELINE EXECUTION #{run_count} COMPLETE ---\n\n"
        f"Target Asset: {coin_id}\n"
        f"Human Elicitation Choice (Risk Mitigation): {risk_mitigation}\n\n"
        f"Client LLM Sampling Output:\n{ai_synthesis}"
    )


if __name__ == "__main__":
    mcp.run()