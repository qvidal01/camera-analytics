# Examples

This directory contains runnable examples demonstrating how to use Camera Analytics.

## Basic Examples

- **[basic_camera_setup.py](basic_camera_setup.py)** - Add a camera and start detection
- **[create_alert_rule.py](create_alert_rule.py)** - Create a custom alert rule
- **[mcp_server_usage.py](mcp_server_usage.py)** - Use the MCP server

## Running Examples

```bash
# From project root
python examples/basic_camera_setup.py
```

## Prerequisites

Ensure you have:
1. Installed dependencies: `pip install -r requirements.txt`
2. Configured `.env` file (copy from `.env.example`)
3. Database running: `docker-compose up -d postgres redis`
