import os
from fastmcp import FastMCP, Context
from pydantic import BaseModel
import requests
from dotenv import load_dotenv 

# 2. Boot up and inject variables from your .env file into os.environ
load_dotenv()

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

class RiskMitigationResponse(BaseModel):
    apply_mitigation: bool

@mcp.tool()
async def advanced_crypto_quant_pipeline(coin_id: str, ctx: Context) -> str:
    """
    An enterprise-grade orchestration pipeline demonstrating Sampling, Elicitation,
    Progress reporting, Native Session State, and Structured Logging wired to a free LLM.
    """
    # 1. LOGGING TAB
    await ctx.info(f" Initializing Ultra Pipeline for asset: {coin_id}")

    # 2. PROGRESS TAB
    await ctx.report_progress(1, 4, "Step 1/4: Fetching underlying market depth data...")
    market_depth = f"Raw Order Book Depth for {coin_id}: High liquidity detected near historical resistance."

    # 3. ELICITATION TAB
    await ctx.report_progress(2, 4, "Step 2/4: Awaiting interactive user feedback...")
    elicit_result = await ctx.elicit(
        message=f"Critical threshold reached for {coin_id}. Do you want to apply strict risk mitigation protocols?",
        response_type=RiskMitigationResponse
    )
    
    if elicit_result.action != "accept":
        await ctx.warning("Elicitation workflow aborted or declined by the user.")
        return "Pipeline execution forcefully halted: Elicitation requirements not met."
        
    risk_mitigation = elicit_result.data.apply_mitigation

    # 4. FREE LIVE LLM INTEGRATION (Google AI Studio Free Tier)
    await ctx.report_progress(3, 4, "Step 3/4: Delegating synthesis to free live Gemini API...")
    prompt_msg = (
        f"Context: You are an elite quantitative crypto analyst. "
        f"Analyze this market state: '{market_depth}'. "
        f"Strict risk settings applied: {risk_mitigation}. "
        f"Provide an institutional executive risk scenario statement summarized into exactly one sentence."
    )
    
    # Retrieve the key you generated from Google AI Studio
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not gemini_key:
        await ctx.warning("GEMINI_API_KEY environment variable missing. Using fallback response.")
        ai_synthesis = "[Key Missing Setup Fallback] Please export your GEMINI_API_KEY to see live responses."
    else:
        # Construct the direct REST API execution payload for the free Gemini 2.5 Flash model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [{
                "parts": [{"text": prompt_msg}]
            }]
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            res_data = response.json()
            
            # Extract out the text string safely from the JSON response object
            ai_synthesis = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
            await ctx.info("Free Live Gemini API synthesis successfully retrieved.")
        except Exception as e:
            ai_synthesis = f"Free API Call Failed: {str(e)}"

    # 5. NATIVE SESSION STATE
    await ctx.report_progress(4, 4, "Step 4/4: Finalizing pipeline and saving session metadata...")
    run_count = (await ctx.get_state("pipeline_runs") or 0) + 1
    await ctx.set_state("pipeline_runs", run_count)
    
    return (
        f"--- QUANT PIPELINE EXECUTION #{run_count} COMPLETE ---\n\n"
        f"Target Asset: {coin_id}\n"
        f"Human Elicitation Choice (Risk Mitigation): {risk_mitigation}\n\n"
        f"Live Free LLM (Gemini 2.5 Flash) Output:\n{ai_synthesis}"
    )


if __name__ == "__main__":
    mcp.run()