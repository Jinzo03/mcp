import os
import httpx
import logging
from fastmcp import FastMCP, Context
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Heading, Text, Badge, Row, Separator
from pydantic import BaseModel, Field
from fastmcp.telemetry import get_tracer

# Configure logging
logger = logging.getLogger(__name__)

# Import the functional tool directly to preserve internal Telemetry Spans safely
from data_server import get_crypto_price

quant_server = FastMCP("CryptoQuant")

class MarketSignal(BaseModel):
    sentiment: str = Field(description="Aggregate market direction: Bullish, Bearish, or Neutral")
    entry_target: str = Field(description="Optimized ingress entry target zones")
    stop_loss: str = Field(description="Defensive protective tracking stop conditions")
    risk_score: int = Field(description="System risk rating integer between 1 and 10")
    synthesis: str = Field(description="Exactly a 1-sentence analytical overview summary")

@quant_server.tool(app=True)
async def advanced_crypto_quant_pipeline(coin_ids: str, ctx: Context, apply_mitigation: bool = False) -> PrefabApp:
    """
    Runs data processing arrays and extracts strict Pydantic UI layout objects.
    
    Args:
        coin_ids: Comma-separated list of tokens (e.g. bitcoin, ethereum)
        apply_mitigation: Enable structural risk tracking overlays
    """
    tracer = get_tracer()
    
    with tracer.start_as_current_span("orchestration_pipeline_root"):
        await ctx.report_progress(1, 3, "Compiling multi-server telemetry loops...")
        
        targets = [coin.strip().lower() for coin in coin_ids.split(",") if coin.strip()]
        compiled_matrix = []
        
        for coin in targets:
            price_output = await get_crypto_price(coin)
            compiled_matrix.append(f"- {coin.upper()}: ${price_output:,.2f} USD")
            
        matrix_str = "\n".join(compiled_matrix)

        await ctx.report_progress(2, 3, "Evaluating risk configurations...")
        # Replaced conversational elicit loop with the clean boolean parameter fallback
        risk_mitigation = apply_mitigation

        await ctx.report_progress(3, 3, "Executing structural evaluation arrays...")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        # Validate required API key
        if not gemini_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            raise ValueError("GEMINI_API_KEY environment variable is required but not set")
        
        prompt_msg = (
            f"Context Profile Matrix:\n{matrix_str}\n"
            f"Risk Overlays Active: {risk_mitigation}\n"
            f"Output exact JSON parsing schema containing fields matching MarketSignal specs."
        )
        
        # Use headers for API key to avoid exposing it in URL/logs
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": gemini_key
        }
        payload = {
            "contents": [{"parts": [{"text": prompt_msg}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, json=payload, headers=headers, timeout=15.0)
                res.raise_for_status()  # Raise exception for HTTP errors
                res_data = res.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API returned HTTP error: {e.response.status_code}")
            span.set_attribute("error.message", f"HTTP {e.response.status_code}")
            if e.response.status_code == 401:
                raise ValueError("Gemini API authentication failed - check your API key")
            elif e.response.status_code == 403:
                raise ValueError("Gemini API access forbidden - verify API key permissions")
            elif e.response.status_code == 429:
                raise ValueError("Gemini API rate limit exceeded - please retry later")
            else:
                raise ValueError(f"Gemini API returned status code {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Gemini API request failed: {e}")
            span.set_attribute("error.message", str(e))
            raise ValueError(f"Failed to connect to Gemini API: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {e}")
            span.set_attribute("error.message", str(e))
            raise ValueError(f"Unexpected error calling Gemini API: {str(e)}")
        
        # Validate response structure before accessing nested keys
        if not isinstance(res_data, dict):
            logger.error(f"Invalid Gemini API response format: {res_data}")
            raise ValueError("Invalid response format from Gemini API")
        
        candidates = res_data.get('candidates', [])
        if not candidates or not isinstance(candidates, list) or len(candidates) == 0:
            logger.error(f"No candidates in Gemini API response: {res_data}")
            raise ValueError("No candidates returned from Gemini API")
        
        content = candidates[0].get('content', {})
        if not isinstance(content, dict):
            logger.error(f"Invalid content structure in Gemini API response: {content}")
            raise ValueError("Invalid content structure from Gemini API")
        
        parts = content.get('parts', [])
        if not parts or not isinstance(parts, list) or len(parts) == 0:
            logger.error(f"No parts in Gemini API response content: {content}")
            raise ValueError("No parts returned in Gemini API response")
        
        raw_json = parts[0].get('text', '').strip()
        if not raw_json:
            logger.error("Empty text in Gemini API response")
            raise ValueError("Empty response text from Gemini API")
        
        try:
            validated_signal = MarketSignal.model_validate_json(raw_json)
        except Exception as e:
            logger.error(f"Failed to validate Gemini API response as MarketSignal: {e}")
            raise ValueError(f"Invalid JSON response from Gemini API: {str(e)}")

        # Assemble the UI View object
        with Column(gap=4, css_class="p-6") as view:
            Heading(" Quant Dashboard Matrix Gateway", level=2)
            with Row(gap=2):
                Text("Targets:")
                Badge(coin_ids, variant="info")
            Separator()
            with Row(gap=4):
                Text(f"Sentiment: {validated_signal.sentiment}", weight="bold")
                Text(f"Risk Profile: {validated_signal.risk_score}/10", weight="bold")
            Text(f"Target Entry: {validated_signal.entry_target}")
            Text(f"Defensive Guard: {validated_signal.stop_loss}")
            Separator()
            Text(validated_signal.synthesis, italic=True)

        return PrefabApp(view=view)
