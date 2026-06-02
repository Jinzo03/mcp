import os
import httpx
from fastmcp import FastMCP, Context
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Heading, Text, Badge, Row, Separator
from pydantic import BaseModel, Field
from fastmcp.telemetry import get_tracer

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
        
        prompt_msg = (
            f"Context Profile Matrix:\n{matrix_str}\n"
            f"Risk Overlays Active: {risk_mitigation}\n"
            f"Output exact JSON parsing schema containing fields matching MarketSignal specs."
        )
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt_msg}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, timeout=15.0)
            res_data = res.json()
            
        raw_json = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        validated_signal = MarketSignal.model_validate_json(raw_json)

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
