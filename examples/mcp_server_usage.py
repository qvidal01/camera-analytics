#!/usr/bin/env python3
"""
MCP Server Usage Example.

This example demonstrates:
1. Initializing the MCP server
2. Listing available tools, resources, and prompts
3. Calling MCP tools
4. Getting MCP resources
"""

import asyncio
import json
import logging

from camera_analytics.mcp_server import CameraAnalyticsMCPServer
from camera_analytics.utils.logging import setup_logging

# Configure logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


async def main():
    """Run the example."""
    logger.info("=== Camera Analytics - MCP Server Usage ===")

    # Initialize MCP server
    server = CameraAnalyticsMCPServer()

    # Get server info
    info = server.get_server_info()
    logger.info(f"\nServer: {info['name']} v{info['version']}")
    logger.info(f"Protocol: {info['protocol_version']}")
    logger.info(f"Capabilities: {info['capabilities']}")

    # List available tools
    logger.info(f"\nAvailable Tools ({len(info['tools'])}):")
    for tool_name in info['tools']:
        logger.info(f"  - {tool_name}")

    # List available resources
    logger.info(f"\nAvailable Resources ({len(info['resources'])}):")
    for resource in info['resources']:
        logger.info(f"  - {resource}")

    # List available prompts
    logger.info(f"\nAvailable Prompts ({len(info['prompts'])}):")
    for prompt_name in info['prompts']:
        logger.info(f"  - {prompt_name}")

    # Example 1: Call detect_objects tool
    logger.info("\n--- Example 1: Detect Objects ---")
    result = await server.call_tool(
        "detect_objects",
        {
            "camera_id": "front-door",
            "classes": ["person", "car"],
            "confidence_threshold": 0.5,
        },
    )
    logger.info(f"Result: {json.dumps(result, indent=2)}")

    # Example 2: Create monitoring rule
    logger.info("\n--- Example 2: Create Monitoring Rule ---")
    result = await server.call_tool(
        "create_monitoring_rule",
        {
            "name": "Package Delivery Alert",
            "description": "Alert when package detected at front door",
            "trigger": {
                "object_class": "package",
                "zone": "front_door",
                "min_confidence": 0.7,
            },
            "actions": [
                {"type": "email", "config": {"to": "user@example.com"}},
                {"type": "record", "config": {"duration": 30}},
            ],
        },
    )
    logger.info(f"Result: {json.dumps(result, indent=2)}")

    # Example 3: Get camera resource
    logger.info("\n--- Example 3: Get Camera Resource ---")
    resource = await server.get_resource("camera://front-door")
    logger.info(f"Resource: {json.dumps(resource, indent=2)}")

    # Example 4: Get prompt
    logger.info("\n--- Example 4: Get Prompt ---")
    prompt = await server.get_prompt(
        "analyze-security-footage",
        {
            "incident_description": "package theft",
            "time_range": "yesterday afternoon",
            "cameras": "front-door, driveway",
        },
    )
    logger.info(f"Prompt:\n{prompt}")

    logger.info("\nDone!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Error: {e}")
