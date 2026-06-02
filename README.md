#  Enterprise Crypto MCP Gateway

---

##  About

Enterprise Crypto MCP Gateway is a dual-server MCP system that gives any MCP-compatible AI client (Claude Desktop, Cursor, etc.) direct, structured access to live crypto market data and quantitative signals. A master gateway composes two specialized sub-servers — one handling raw data retrieval and local filtering, the other running a full AI-backed quant pipeline with structured Pydantic output and a rich rendered UI — all wired with OpenTelemetry spans for end-to-end observability.

---

##  System Architecture

```
MCP Client (Claude Desktop / Cursor / etc.)
            │
            ▼
┌───────────────────────────────────┐
│    EnterpriseMasterGateway        │  ← server.py
│    FastMCP Router                 │
│                                   │
│   namespace: "market"             │   namespace: "quant"
│   ┌───────────────────────┐       │   ┌───────────────────────┐
│   │  CryptoData Server    │       │   │  CryptoQuant Server   │
│   │  data_server.py       │       │   │  quant_server.py      │
│   │                       │       │   │                       │
│   │  Resource:            │       │   │  Tool (app=True):     │
│   │  data://trending      │       │   │  quant_pipeline       │
│   │                       │       │   │  → Gemini 2.5 Flash   │
│   │  Tools:               │       │   │  → MarketSignal       │
│   │  get_crypto_price     │       │   │    (Pydantic)         │
│   │  query_and_filter     │       │   │  → PrefabApp UI       │
│   └───────────────────────┘       │   └───────────────────────┘
└───────────────────────────────────┘
            │
            ▼
    otel_launcher.py
    OpenTelemetry Auto-Instrumentation
    (OTLP export if configured, silent otherwise)
```

All tools and resources under the `market` namespace are accessible as `market_*` and those under `quant` as `quant_*` from the client's perspective.

---

##  Project Structure

```
enterprise-crypto-mcp/
│
├── server.py           # Master gateway — mounts both sub-servers with namespacing
├── data_server.py      # CryptoData sub-server — prices, trending, filtering
├── quant_server.py     # CryptoQuant sub-server — AI quant pipeline + UI rendering
├── otel_launcher.py    # OpenTelemetry configuration and auto-instrumentation launcher
│
├── .env                # Environment variables (gitignored)
├── .gitignore
└── requirements.txt    # (add your own if not present)
```

---

## Sub-Servers — Detailed Breakdown

### `CryptoData` — `data_server.py`

Handles all raw market data retrieval from the CoinGecko public API. Exposes one MCP Resource and two Tools.

---

####  Resource — `data://trending`

```
market_get_trending_markets()
```

Returns a formatted snapshot of the top 5 trending cryptocurrencies on CoinGecko, including coin ID, ticker symbol, and market cap rank.

| Property      | Value              |
|---------------|--------------------|
| Source API    | CoinGecko `/search/trending` |
| Cache TTL     | **300 seconds** (5 minutes) |
| Cache strategy| In-memory dict with expiry timestamp |
| OTel span     | `get_trending_markets_resource` with `cache.status` attribute |

---

####  Tool — `get_crypto_price`

```
market_get_crypto_price(coin_id: str) → float
```

Fetches the current USD price of a single token by CoinGecko coin ID (e.g. `bitcoin`, `ethereum`). Returns a clean `float` value optimized for downstream arithmetic operations without any formatting overhead.

| Property      | Value              |
|---------------|--------------------|
| Source API    | CoinGecko `/simple/price` |
| Cache TTL     | **60 seconds** (1 minute) |
| OTel span     | `get_crypto_price_execution` with `target.coin` and `cache.status` attributes |

---

####  Tool — `query_and_filter_market_data`

```
market_query_and_filter_market_data(coin_ids: str, threshold_price: float) → str
```

Accepts a comma-separated list of coin IDs and a USD threshold. Evaluates all price lookups **locally in code** and passes only coins that cross the specified threshold back to the LLM — discarding the rest entirely.

This is a deliberate **context window optimization pattern**: for large watchlists, sending every token's price to the LLM is wasteful. By filtering on the server side, only the signal-bearing subset reaches the model.

| Property         | Value |
|------------------|-------|
| Input            | `"bitcoin,ethereum,solana,cardano"`, threshold `50.0` |
| Output           | Only coins with price ≥ threshold, formatted as `COIN: $price USD` |
| OTel span        | `code_api_data_filtering` with `filter.input_count` and `filter.output_count` attributes |

---

### `CryptoQuant` — `quant_server.py`

Runs a full AI-backed quantitative analysis pipeline on a set of target tokens. Returns a structured `PrefabApp` UI object rendered directly in the MCP client.

---

#### 🔧 Tool (UI) — `advanced_crypto_quant_pipeline`

```
quant_advanced_crypto_quant_pipeline(coin_ids: str, apply_mitigation: bool = False) → PrefabApp
```

**Pipeline stages:**

| Stage | Action |
|-------|--------|
| 1 | Fetches live prices for all target coins via `get_crypto_price` (reuses CryptoData tool directly, preserving its internal telemetry spans) |
| 2 | Assembles a price matrix string and applies optional risk mitigation flag |
| 3 | Calls **Gemini 2.5 Flash** with `responseMimeType: application/json` to generate a structured market signal |
| 4 | Validates the raw JSON response against the `MarketSignal` Pydantic model |
| 5 | Builds and returns a `PrefabApp` UI layout using `prefab_ui` components |

Progress is reported at each stage via `ctx.report_progress(current, total, message)`, giving MCP clients real-time execution feedback.

**`MarketSignal` Schema (Pydantic):**

```python
class MarketSignal(BaseModel):
    sentiment: str        # "Bullish" | "Bearish" | "Neutral"
    entry_target: str     # Optimized entry zone description
    stop_loss: str        # Defensive stop condition description
    risk_score: int       # 1–10 integer risk rating
    synthesis: str        # Exactly one sentence of analytical summary
```

**Rendered UI Components:**
- `Heading` — Dashboard title
- `Badge` — Active coin targets
- `Row` / `Column` — Layout grid
- `Text` — Sentiment, risk profile, entry/stop targets
- `Separator` — Visual section dividers

| Property      | Value |
|---------------|-------|
| LLM           | Gemini 2.5 Flash (`generativelanguage.googleapis.com`) |
| Output format | `application/json` via `generationConfig` |
| OTel span     | `orchestration_pipeline_root` (root orchestration span) |

---

##  Getting Started

### Prerequisites

- Python 3.10+
- A [Google AI Studio](https://aistudio.google.com/) API key (Gemini 2.5 Flash)
- An MCP-compatible client (Claude Desktop, Cursor, or any MCP host)
- *(Optional)* An OpenTelemetry OTLP-compatible collector (Jaeger, Grafana Tempo, etc.)

### 1. Clone and Install

```bash
git clone https://github.com/your-username/enterprise-crypto-mcp.git
cd enterprise-crypto-mcp

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install fastmcp httpx python-dotenv opentelemetry-distro prefab-ui pydantic
```

### 2. Configure Environment

Create a `.env` file at the project root:

```env
# Required
GEMINI_API_KEY=your_google_ai_studio_key_here

# Optional — OpenTelemetry export (omit to disable silently)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=EnterpriseMasterGateway
```

> If `OTEL_EXPORTER_OTLP_ENDPOINT` is not set, the launcher defaults all exporters to `none`, keeping MCP's stdio transport completely clean.

### 3. Run the Server

**Standard mode (direct stdio):**

```bash
python server.py
```

**With OpenTelemetry auto-instrumentation:**

```bash
python otel_launcher.py
```

Use `otel_launcher.py` when you have an OTLP collector running and want full distributed tracing. Both entry points expose the same MCP interface.

### 4. Connect to an MCP Client

**Claude Desktop** — add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "enterprise-crypto": {
      "command": "python",
      "args": ["/absolute/path/to/otel_launcher.py"],
      "env": {
        "GEMINI_API_KEY": "your_key_here"
      }
    }
  }
}
```

---

## 📡 Available MCP Capabilities (Client View)

Once connected, the following capabilities are exposed to the MCP client:

| Type     | Name                                    | Description |
|----------|-----------------------------------------|-------------|
| Resource | `data://trending`                       | Live top-5 trending crypto markets |
| Tool     | `market_get_crypto_price`               | Fetch USD price for a single token |
| Tool     | `market_query_and_filter_market_data`   | Batch filter tokens by price threshold |
| Tool     | `quant_advanced_crypto_quant_pipeline`  | Full AI quant analysis with rendered UI |

---

##  Observability — OpenTelemetry Integration

Every significant operation is instrumented with named spans:

| Span Name                         | Location              | Key Attributes |
|-----------------------------------|-----------------------|----------------|
| `get_trending_markets_resource`   | `data_server.py`      | `cache.status` |
| `get_crypto_price_execution`      | `data_server.py`      | `target.coin`, `cache.status` |
| `code_api_data_filtering`         | `data_server.py`      | `filter.input_count`, `filter.output_count` |
| `orchestration_pipeline_root`     | `quant_server.py`     | (root span) |

`otel_launcher.py` applies `opentelemetry-instrumentation` auto-instrumentation on top, covering `httpx` client calls and any other auto-instrumented libraries without manual decoration.

When no OTLP endpoint is configured, all exporters are silently set to `none` — there is no console noise that would pollute the MCP stdio transport.

---

##  Caching Strategy

The `CryptoData` server uses a simple but effective two-tier in-memory cache:

| Data Type       | TTL         | Rationale |
|-----------------|-------------|-----------|
| Trending markets| 5 minutes   | Changes infrequently; reduces CoinGecko rate limit pressure |
| Token prices    | 1 minute    | Balance between freshness and API call volume |

Each cache entry stores both the value and an expiry timestamp. Cache hits and misses are both recorded as OTel span attributes for monitoring.

> **Note:** The cache is process-scoped. Restarting the server clears it. For persistent caching across restarts, replace the `_CACHE` dict with Redis.

---

## Limitations & Known Constraints

- **CoinGecko free tier** — The public API has rate limits (~30 calls/min). Heavy concurrent usage may result in 429 errors. Consider using the paid API for production.
- **In-process cache** — Cache does not survive restarts and is not shared across multiple server instances.
- **Gemini dependency** — The quant pipeline is tightly coupled to Gemini's REST API. Gemini outages will cause `advanced_crypto_quant_pipeline` to fail.
- **No input validation on coin IDs** — Invalid CoinGecko coin IDs silently return `0.0` from `get_crypto_price`.

---

##  Potential Extensions

- **WebSocket price streaming** — Replace polling with CoinGecko or Binance WebSocket feeds for sub-second price updates
- **Redis cache layer** — Swap the in-memory `_CACHE` dict for Redis to support multi-instance deployments and cache persistence
- **Model-agnostic quant backend** — Abstract the Gemini call behind an LLM provider interface to support OpenAI, Groq, or Anthropic interchangeably
- **Historical data resource** — Add OHLCV (Open/High/Low/Close/Volume) endpoints for backtesting context
- **Portfolio tool** — Extend the quant server with a multi-asset portfolio risk calculator using the existing price tools

---

##  License

This project is released for academic and educational purposes.