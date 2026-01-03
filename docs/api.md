# API Documentation

## Overview

Camera Analytics provides a RESTful API built with FastAPI for managing cameras, viewing detections, and configuring alerts.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: JWT Bearer tokens (to be implemented)

## Interactive Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Core Endpoints

### Health Check

#### GET /health

Check API health status.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Cameras

#### GET /api/v1/cameras

List all cameras.

**Response**:
```json
{
  "cameras": [
    {
      "id": "cam-001",
      "name": "Front Door",
      "type": "rtsp",
      "status": "connected",
      "enabled": true
    }
  ]
}
```

#### POST /api/v1/cameras

Add a new camera.

**Request Body**:
```json
{
  "name": "Front Door",
  "source_type": "rtsp",
  "source_url": "rtsp://admin:password@192.168.1.100:554/stream1",
  "fps": 15,
  "resolution": "1920x1080"
}
```

**Response**:
```json
{
  "id": "cam-001",
  "name": "Front Door",
  "status": "connected"
}
```

#### GET /api/v1/cameras/{camera_id}

Get camera details.

#### DELETE /api/v1/cameras/{camera_id}

Remove a camera.

#### GET /api/v1/cameras/{camera_id}/snapshot

Get current frame from camera as JPEG image.

### Detections

#### GET /api/v1/detections

List recent detections (paginated).

**Query Parameters**:
- `camera_id` (optional): Filter by camera
- `class` (optional): Filter by object class
- `start_time` (optional): Start timestamp
- `end_time` (optional): End timestamp
- `limit` (default: 100): Results per page
- `offset` (default: 0): Pagination offset

**Response**:
```json
{
  "detections": [
    {
      "id": "det-12345",
      "class": "person",
      "confidence": 0.89,
      "bbox": [100, 200, 300, 500],
      "timestamp": "2024-01-15T10:30:00Z",
      "camera_id": "cam-001"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### Alerts

#### GET /api/v1/alerts

List all alerts.

#### GET /api/v1/alerts/{alert_id}

Get alert details.

#### POST /api/v1/alerts/{alert_id}/acknowledge

Mark alert as acknowledged.

### Rules

#### GET /api/v1/rules

List all alert rules.

#### POST /api/v1/rules

Create a new alert rule.

**Request Body**:
```json
{
  "name": "Nighttime Person Detection",
  "description": "Alert when person detected at night",
  "conditions": [
    {
      "field": "class",
      "operator": "eq",
      "value": "person"
    },
    {
      "field": "time",
      "operator": "between",
      "value": ["22:00", "06:00"]
    }
  ],
  "actions": [
    {
      "type": "email",
      "config": {
        "to": "user@example.com"
      }
    }
  ],
  "enabled": true
}
```

#### PUT /api/v1/rules/{rule_id}

Update an alert rule.

#### DELETE /api/v1/rules/{rule_id}

Delete an alert rule.

### Analytics

#### GET /api/v1/analytics/summary

Get dashboard summary with counts and recent activity.

#### GET /api/v1/analytics/heatmap

Generate heatmap for a camera.

**Query Parameters**:
- `camera_id` (required): Camera ID
- `start_time` (required): Start timestamp
- `end_time` (required): End timestamp

## WebSocket

### WS /api/v1/ws/events

Real-time event stream.

**Message Format**:
```json
{
  "type": "detection",
  "data": {
    "id": "det-12345",
    "class": "person",
    "confidence": 0.89,
    "camera_id": "cam-001"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### WS /api/v1/ws/cameras/{camera_id}

Live camera feed with detection overlays.

## Error Responses

All errors follow this format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Status Codes**:
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user

Rate limit headers:
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

## Examples

See [examples/](../examples/) directory for code examples.
