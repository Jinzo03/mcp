from fastmcp import FastMCP
from dotenv import load_dotenv

# Import both operational sub-servers
from data_server import data_server
from quant_server import quant_server

load_dotenv()

# Instantiate the Master Router Gateway
mcp = FastMCP("EnterpriseMasterGateway")

# Server Composition: Updated from prefix to namespace
mcp.mount(data_server, namespace="market")
mcp.mount(quant_server, namespace="quant")

if __name__ == "__main__":
    mcp.run()