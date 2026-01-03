# Camera Analytics - Claude Reference

## Quick Overview
AI-powered video analytics platform. Object detection (YOLOv8), multi-camera tracking, intelligent alerts, and privacy-first processing.

## Tech Stack
- **Framework:** FastAPI + Uvicorn
- **Language:** Python 3.10+
- **Detection:** YOLOv8
- **ML:** PyTorch + TorchVision
- **Vision:** OpenCV
- **Database:** PostgreSQL (AsyncPG)
- **Cache:** Redis
- **AI:** MCP Server for Claude

## Project Structure
```
src/camera_analytics/
├── detection/           # YOLOv8 detection engine
├── tracking/            # Multi-camera tracking
├── recording/           # Video recording manager
├── analytics/           # Analytics & reporting
├── alerts/              # Alert system
├── api/                 # FastAPI REST endpoints
├── mcp_server/          # Claude AI integration
└── cli/                 # Command-line interface

tests/                   # Unit & integration tests
docs/                    # Documentation
examples/                # Usage examples
docker-compose.yml       # Services setup
```

## Quick Commands
```bash
# Install
pip install -e ".[dev]"

# Run API server
uvicorn src.camera_analytics.api:app --reload

# Run CLI
python -m camera_analytics.cli

# Docker
docker-compose up -d
```

## Key Features
- Object detection (people, vehicles, packages, pets)
- Multi-camera tracking across views
- Intelligent alerts (rule-based, anomaly)
- Event recording on motion/detection
- Analytics dashboard with heatmaps
- Privacy features (face blur, zone exclusions)
- GPU acceleration (CUDA/TensorRT)

## Performance
- Detection: 12-25ms/frame
- Throughput: 30-60 FPS/camera
- Max cameras: 16 (1080p @ 15 FPS)
- Memory: ~200MB/stream

## Requirements
- Python 3.10+
- PostgreSQL 15+
- Redis 7+
- (Optional) NVIDIA GPU + CUDA 11.8+

## Status: Alpha (v0.1)
- Core detection & tracking
- Basic alert system
- REST API
- Web dashboard (in progress)
- MCP server (planned)

## Documentation
- `ANALYSIS_SUMMARY.md` - Architecture
- `ISSUES_FOUND.md` - Known issues
- `IMPROVEMENT_PLAN.md` - Roadmap
