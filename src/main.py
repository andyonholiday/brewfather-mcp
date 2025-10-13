import asyncio
import argparse
import os
import sys
from brewfather_mcp.server import mcp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brewfather MCP Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (saves API responses to files)")
    args = parser.parse_args()
    
    # Set debug environment variable if requested
    if args.debug:
        os.environ["BREWFATHER_MCP_DEBUG"] = "1"
        print("Debug mode enabled - API responses will be saved to files", file=sys.stderr)
    
    loop = asyncio.get_running_loop()
    loop.run_until_complete(mcp.run_stdio_async())
