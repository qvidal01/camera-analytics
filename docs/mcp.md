# MCP Server Documentation

## Overview

The Camera Analytics MCP (Model Context Protocol) server enables AI assistants like Claude to interact with the camera system through natural language.

## Setup

### 1. Start MCP Server

```bash
# Run MCP server
python -m camera_analytics.mcp_server

# Or with custom settings
python -m camera_analytics.mcp_server --config mcp_config.json
```

### 2. Configure Claude Desktop

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "camera-analytics": {
      "command": "python",
      "args": ["-m", "camera_analytics.mcp_server"],
      "cwd": "/path/to/camera-analytics"
    }
  }
}
```

### 3. Test Connection

Restart Claude Desktop and ask:
> "List all cameras"

## Available Tools

### 1. detect_objects

Analyze an image or video frame for objects.

**Example prompts**:
- "Detect people in the front door camera"
- "What objects are visible in camera 1?"
- "Show me all cars detected in the last hour"

### 2. create_monitoring_rule

Set up automated alerts.

**Example prompts**:
- "Alert me when a person is detected at night"
- "Create a rule to notify me when a car enters the driveway"
- "Set up monitoring for packages at the front door"

### 3. query_analytics

Retrieve historical analytics data.

**Example prompts**:
- "How many people visited yesterday?"
- "Show me peak activity times for this week"
- "What were the busiest hours at the entrance?"

### 4. search_recordings

Find and retrieve video recordings.

**Example prompts**:
- "Find recordings of people at the front door yesterday"
- "Show me when the delivery truck arrived"
- "Search for car activity between 2-4 PM"

### 5. get_camera_status

Check camera health.

**Example prompts**:
- "Are all cameras online?"
- "Check status of camera 1"
- "Which cameras are disconnected?"

### 6. configure_camera

Add or update cameras.

**Example prompts**:
- "Add a new camera at rtsp://192.168.1.100"
- "Update camera 1 resolution to 1080p"
- "Enable detection zones for the front door camera"

## Resources

### camera://{camera_id}

Access camera data.

**Example**: `camera://front-door`

### recording://{recording_id}

Access recordings.

**Example**: `recording://rec-12345`

### alert://{alert_id}

Access alert details.

**Example**: `alert://alert-67890`

### analytics://report/{report_type}

Access pre-generated reports.

**Example**: `analytics://report/daily-summary`

## Prompts

### analyze-security-footage

Investigate incidents.

**Example**:
> "I need to investigate a package theft. Search footage from the front door camera yesterday afternoon."

### setup-monitoring

Interactive rule creation.

**Example**:
> "Help me set up monitoring for people in the backyard"

### daily-security-report

Generate summaries.

**Example**:
> "Show me today's security report"

## Example Conversations

### Example 1: Check Camera Status

**You**: Are all my cameras working?

**Claude**: Let me check the status of your cameras using the get_camera_status tool.

[Uses: get_camera_status with camera_id="all"]

All 3 cameras are online and functioning:
- Front Door: Connected, last frame 2 seconds ago
- Backyard: Connected, last frame 1 second ago
- Driveway: Connected, last frame 3 seconds ago

### Example 2: Create Alert Rule

**You**: Alert me when someone is at the front door after 10 PM

**Claude**: I'll create a monitoring rule for nighttime person detection at your front door.

[Uses: create_monitoring_rule]

Created rule "Nighttime Front Door Alert":
- Trigger: Person detected at camera "front-door" between 22:00-06:00
- Actions: Email notification, 30-second video recording
- Status: Active

You'll receive an email whenever this rule triggers.

### Example 3: Search Footage

**You**: Did anyone visit yesterday afternoon?

**Claude**: Let me search your front door camera footage for yesterday afternoon.

[Uses: search_recordings with time range]

Found 3 visitors yesterday afternoon:
1. 2:15 PM - Person (85% confidence), stayed 45 seconds
2. 3:30 PM - Delivery person (92% confidence), package detected
3. 5:20 PM - Person (78% confidence), stayed 2 minutes

Would you like to view any of these recordings?

## Troubleshooting

### MCP Server Not Connecting

1. Check server is running: `ps aux | grep mcp_server`
2. Verify config path in Claude Desktop settings
3. Check logs: `tail -f logs/mcp_server.log`

### Tool Calls Failing

1. Ensure Camera Analytics API is running
2. Check database connectivity
3. Verify camera connections

### Resources Not Found

1. Check resource URI format
2. Ensure resource exists (e.g., camera ID is valid)
3. Check permissions

## Development

### Adding New Tools

1. Define tool schema in `server.py`
2. Implement handler method
3. Update routing in `call_tool()`
4. Add tests
5. Update documentation

### Testing

```bash
# Run MCP server tests
pytest tests/test_mcp_server.py

# Test with mock client
python examples/mcp_server_usage.py
```

## Security

- Tools respect API authentication
- Camera credentials never exposed to prompts
- Rate limiting applies to MCP calls
- Audit logs track all MCP operations
