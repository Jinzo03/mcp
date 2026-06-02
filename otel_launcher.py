import asyncio
import os

from dotenv import load_dotenv


def _configure_otel_defaults() -> None:
    """Keep MCP stdio clean unless an OTLP collector is explicitly configured."""
    os.environ.setdefault("OTEL_SERVICE_NAME", "EnterpriseMasterGateway")

    has_otlp_endpoint = (
        os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    )
    os.environ.setdefault("OTEL_TRACES_EXPORTER", "otlp" if has_otlp_endpoint else "none")
    os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
    os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")


load_dotenv()
_configure_otel_defaults()

from opentelemetry.instrumentation.auto_instrumentation import initialize

initialize()

from server import mcp


if __name__ == "__main__":
    try:
        mcp.run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
