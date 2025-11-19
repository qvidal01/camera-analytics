"""Main entry point for MCP server."""

import asyncio
import logging

from camera_analytics.config import get_settings
from camera_analytics.mcp_server.server import CameraAnalyticsMCPServer
from camera_analytics.utils.logging import setup_logging

settings = get_settings()
logger = logging.getLogger(__name__)


async def main():
    """Run MCP server."""
    setup_logging(level=settings.log_level)
    logger.info("Starting Camera Analytics MCP Server")

    server = CameraAnalyticsMCPServer()
    info = server.get_server_info()

    logger.info(f"Server: {info['name']} v{info['version']}")
    logger.info(f"Protocol: {info['protocol_version']}")
    logger.info(f"Tools: {info['tools']}")
    logger.info(f"Resources: {info['resources']}")
    logger.info(f"Prompts: {info['prompts']}")

    # In a real implementation, this would start the MCP server
    # listening on stdio or HTTP, depending on transport
    logger.info("MCP Server running (stub implementation)")

    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server")


if __name__ == "__main__":
    asyncio.run(main())
