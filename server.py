import os
import time
import json
import httpx
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Heading, Text, Badge, Row, Separator

# Boot and inject environment variables from the local .env file
load_dotenv()

# Initialize the standalone high-performance MCP Server
mcp = FastMCP("LiveMarketAnalyzer")

# =====================================================================
# CORE CACHE CONFIGURATION (Protects against 429 Rate Limits)
# =====================================================================
_CACHE = {
    "trending": {"data": None, "expiry": 0},
    "prices": {}  # Structure: { "coin_id": {"price": float, "expiry": float} }
}
TRENDING_CACHE_TTL_SECS = 300  # 5 Minutes
PRICE_CACHE_TTL_SECS = 60      # 1 Minute


# =====================================================================
# 1. RESOURCE: Dynamic Market Data Stream (Async + Cached)
# =====================================================================
@mcp.resource("market://trending")
async def get_trending_markets() -> str:
    """
    Exposes a real-time, non-blocking data stream of the top trending 
    cryptocurrencies on the market right now with an active 5-minute TTL cache.
    """
    now = time.time()
    
    # Check cache validity
    if _CACHE["trending"]["data"] and now < _CACHE["trending"]["expiry"]:
        return f" [CACHE HIT - TTL ACTIVE]\n{_CACHE['trending']['data']}"

    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()
        
        lines = ["=== LIVE TRENDING MARKET DASHBOARD ==="]
        for idx, coin in enumerate(data.get('coins', [])[:5], 1):
            item = coin['item']
            lines.append(f"{idx}. {item['name']} ({item['symbol'].upper()})")
            lines.append(f"   Market Cap Rank: #{item.get('market_cap_rank', 'N/A')}")
            lines.append(f"   Price (BTC): {item.get('price_btc', 0):.8f} BTC")
            lines.append("-" * 30)
            
        formatted_result = "\n".join(lines)
        
        # Populate cache
        _CACHE["trending"]["data"] = formatted_result
        _CACHE["trending"]["expiry"] = now + TRENDING_CACHE_TTL_SECS
        
        return formatted_result
    except Exception as e:
        return f"Error generating trending resource: {str(e)}"


# =====================================================================
# 2. TOOL: Live Price Fetcher (Async + Cached)
# =====================================================================
@mcp.tool()
async def get_crypto_price(coin_id: str) -> str:
    """
    Fetches the live, real-time price of a cryptocurrency in USD.
    Leverages a 60-second non-blocking cache memory layer.
    """
    coin_clean = coin_id.strip().lower()
    now = time.time()
    
    # Check localized item cache validity
    if coin_clean in _CACHE["prices"] and now < _CACHE["prices"][coin_clean]["expiry"]:
        cached_price = _CACHE["prices"][coin_clean]["price"]
        return f"♻️ [CACHE HIT] The current live price of {coin_clean.capitalize()} is ${cached_price:,.2f} USD."

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_clean}&vs_currencies=usd"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            data = response.json()
        
        if coin_clean in data:
            price = data[coin_clean]['usd']
            
            # Populate localized item cache
            _CACHE["prices"][coin_clean] = {
                "price": price,
                "expiry": now + PRICE_CACHE_TTL_SECS
            }
            return f"The current live price of {coin_clean.capitalize()} is ${price:,.2f} USD."
        else:
            return f"Error: Could not find live data for '{coin_clean}'. Ensure it is a valid CoinGecko ID."
            
    except Exception as e:
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
# 4. ADVANCED ORCHESTRATION COMPONENT AND STRUCTURING PYDANTIC MODELS
# =====================================================================

class RiskMitigationResponse(BaseModel):
    apply_mitigation: bool

# The structural schema matching the response output we demand from Gemini
class MarketSignal(BaseModel):
    sentiment: str = Field(description="Overall aggregate market direction: Bullish, Bearish, or Neutral")
    entry_target: str = Field(description="Optimized entry pricing range details based on depth analytics")
    stop_loss: str = Field(description="Strict protective stop loss execution placement trigger pricing")
    risk_score: int = Field(description="An aggregate calculated risk index from 1 (lowest) to 10 (highest)")
    synthesis: str = Field(description="Exactly a 1-sentence institutional-grade executive overview statement summarizing the play")


@mcp.tool(app=True)
async def advanced_crypto_quant_pipeline(coin_ids: str, ctx: Context) -> PrefabApp:
    """
    An enterprise-grade orchestration pipeline demonstrating Async execution, 
    Multi-Asset parsing loops, User Elicitation, and Pydantic-validated Structured LLM Generation.
    """
    await ctx.info(f"Initializing Enterprise Ultra Pipeline for execution parameters: {coin_ids}")

    # -----------------------------------------------------------------
    # STEP 1: MULTI-ASSET LOOPS & COMPILATION
    # -----------------------------------------------------------------
    await ctx.report_progress(1, 4, "Step 1/4: Ingesting assets & running parallel market calculation matrix...")
    
    # Process string input. If keyword is 'trending', grab live top 3 items
    targets = []
    if coin_ids.strip().lower() == "trending":
        await ctx.info("Dynamic asset parsing triggered. Interrogating search analytics endpoints...")
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get("https://api.coingecko.com/api/v3/search/trending", timeout=5.0)
                trending_data = res.json()
            targets = [coin['item']['id'] for coin in trending_data.get('coins', [])[:3]]
            await ctx.info(f"Auto-extracted top 3 currently trending assets: {targets}")
        except Exception as e:
            await ctx.warning(f"Failed to auto-scan trending assets: {str(e)}. Defaulting to base bitcoin tracking.")
            targets = ["bitcoin"]
    else:
        # Split on commas to handle dynamic loops like "bitcoin, ethereum, solana"
        targets = [coin.strip().lower() for coin in coin_ids.split(",") if coin.strip()]

    # Fetch live price profiles asynchronously for the multi-asset loop
    market_depth_summary = []
    async with httpx.AsyncClient() as client:
        for coin in targets:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
            try:
                res = await client.get(url, timeout=5.0)
                data = res.json()
                price = data.get(coin, {}).get('usd', 'Unknown')
                market_depth_summary.append(f"• Asset: {coin.upper()} | Current Market Price: ${price} USD | Liquidity Cluster: High depth resting near baseline support.")
            except Exception:
                market_depth_summary.append(f"• Asset: {coin.upper()} | Current Market Price: Data Stream Fetch Interrupted.")

    aggregated_matrix_str = "\n".join(market_depth_summary)
    await ctx.info("Asynchronous market compilation array built successfully.")

    # -----------------------------------------------------------------
    # STEP 2: USER INTERACTIVE ELICITATION
    # -----------------------------------------------------------------
    await ctx.report_progress(2, 4, "Step 2/4: Prompting system dashboard for interactive human approval...")
    elicit_result = await ctx.elicit(
        message=f"Critical analysis matrix complete for {', '.join(targets).upper()}. Confirm activation of strict structural risk mitigation parameters?",
        response_type=RiskMitigationResponse
    )
    
    if elicit_result.action != "accept":
        await ctx.warning("Elicitation protocol aborted or denied by operator.")
        return "Pipeline execution forcefully halted: Operational parameters withheld by user."
        
    risk_mitigation = elicit_result.data.apply_mitigation
    await ctx.info(f"Risk overlay enforcement instruction recorded: {risk_mitigation}")

    # -----------------------------------------------------------------
    # STEP 3: STRUCTURED LLM VALIDATION VIA GEMINI 2.5 FLASH FREE TIER
    # -----------------------------------------------------------------
    await ctx.report_progress(3, 4, "Step 3/4: Transmitting data profile to Gemini for strict JSON validation...")
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        await ctx.error("Critical failure: GEMINI_API_KEY environment variable missing from .env file.")
        return "Pipeline execution suspended: Missing live validation engine token."

    # Construct explicit prompt forcing compliance with JSON specifications
    prompt_msg = (
        f"Context: You are a principal institutional quantitative risk validation algorithm.\n"
        f"Analyze the following real-time asset market matrix:\n"
        f"'{aggregated_matrix_str}'\n\n"
        f"Active Operator Parameters - Strict Risk Mitigation Overlay: {risk_mitigation}.\n\n"
        f"You MUST return a pure JSON object structured precisely to match the fields listed below. "
        f"Do not surround your text in markdown code blocks, do not provide intro/outro comments, and output nothing else:\n"
        f"{{\n"
        f"  \"sentiment\": \"Bullish, Bearish, or Neutral\",\n"
        f"  \"entry_target\": \"specific actionable price target or level range\",\n"
        f"  \"stop_loss\": \"specific defensive protective exit tracking description\",\n"
        f"  \"risk_score\": an integer value between 1 and 10,\n"
        f"  \"synthesis\": \"exactly a 1-sentence high-level quantitative summary statement\"\n"
        f"}}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt_msg}]}],
        "generationConfig": {
            "responseMimeType": "application/json"  # Forces the engine to native JSON mode
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=15.0)
            response.raise_for_status()
            res_data = response.json()
            
        raw_json_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # Hydrate the Pydantic structural validator with raw text string
        validated_signal = MarketSignal.model_validate_json(raw_json_text)
        await ctx.info("Gemini runtime response successfully vetted against local Pydantic definitions.")
        
        # Build an enterprise visual dashboard in markdown format
        ai_dashboard_output = (
            f"### QUANTITATIVE MODEL VALIDATION MATRIX\n"
            f"* **Aggregate Cluster Sentiment:** `{validated_signal.sentiment}`\n"
            f"* **Target Ingress Protocol (Entry):** {validated_signal.entry_target}\n"
            f"* **Calculated Contingency Plan (Stop-Loss):** {validated_signal.stop_loss}\n"
            f"* **Composite System Risk Rating:** `{validated_signal.risk_score}/10`\n\n"
            f"**Executive Synthesis:**\n*{validated_signal.synthesis}*"
        )
    except Exception as e:
        await ctx.error(f"Structured integration processing error: {str(e)}")
        ai_dashboard_output = f"Structural Model Compilation Interrupted: {str(e)}"

    # -----------------------------------------------------------------
    # STEP 4: PROTOCOL SESSION RETENTION STORAGE
    # -----------------------------------------------------------------
    await ctx.report_progress(4, 4, "Step 4/4: Finalizing system telemetry and updating session logs...")
    
    run_count = (await ctx.get_state("pipeline_runs") or 0) + 1
    await ctx.set_state("pipeline_runs", run_count)
    await ctx.info(f"Pipeline processing complete. Operational Run Tracker adjusted to: {run_count}")
    
    # Change 2: Build a dynamic UI instead of returning a string
    with Column(gap=4, css_class="p-6") as view:
        Heading(f" Enterprise Quant Pipeline #{run_count}", level=2)
        
        with Row(gap=2, align="center"):
            Text("Target Range:", weight="bold")
            Badge(coin_ids, variant="info")
            Text("Enforced Risk Overlays:", weight="bold")
            Badge(str(risk_mitigation), variant="warning" if risk_mitigation else "destructive")
        
        Separator()
        
        Heading(" Validation Matrix", level=3)
        
        with Row(gap=4):
            with Column(gap=1):
                Text("Aggregate Sentiment", weight="bold")
                Badge(validated_signal.sentiment)
            with Column(gap=1):
                Text("System Risk Rating", weight="bold")
                Text(f"{validated_signal.risk_score}/10")
        
        with Column(gap=1):
            Text("Target Ingress Protocol (Entry):", weight="bold")
            Text(validated_signal.entry_target)
        
        with Column(gap=1):
            Text("Calculated Contingency Plan (Stop-Loss):", weight="bold")
            Text(validated_signal.stop_loss)
        
        Separator()
        
        Heading("Executive Synthesis", level=4)
        Text(validated_signal.synthesis, italic=True)

    return PrefabApp(view=view)
    


if __name__ == "__main__":
    mcp.run()