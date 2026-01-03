# Security Camera Analytics

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI](https://github.com/qvidal01/camera-analytics/workflows/CI/badge.svg)](https://github.com/qvidal01/camera-analytics/actions)

AI-powered analytics for security camera systems. Transform passive surveillance into intelligent monitoring with real-time object detection, motion tracking, and automated alerts—all processed locally for privacy.

## Features

### Core Capabilities
- **AI Object Detection** - Identify people, vehicles, packages, and pets using YOLOv8
- **Basic Object Tracking** - Follow subjects across frames within a single camera view
- **Intelligent Alerts** - Rule-based detection with email/webhook notifications
- **Event Recording** - Automatic video capture on detection events
- **FastAPI Web API** - RESTful interface for managing cameras, analytics, and alerts
- **CLI Tool** - Command-line interface for common management tasks

### Technical Highlights
- **Modern Stack** - FastAPI, async Python
- **GPU Acceleration Support** - CUDA/TensorRT for real-time processing (requires configuration)
- **Production Ready Scaffold** - Type-safe, tested, documented, containerized
- **Extensible Core** - Modular design for adding custom detectors and analytics

## Quick Start

### Prerequisites
- Python 3.10 or later
- (Optional) NVIDIA GPU with CUDA 11.8+ for acceleration

### Installation

```bash
# Clone repository
git clone https://github.com/qvidal01/camera-analytics.git
cd camera-analytics

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt # Install dev dependencies for CLI

# For GPU support (NVIDIA)
# pip install -r requirements-gpu.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (e.g., SMTP, Webhook URLs)
```

### Running the API Server

```bash
# Start the FastAPI server
uvicorn camera_analytics.api:app --host 0.0.0.0 --port 8000
```
The API will be available at `http://localhost:8000`.

### Using the CLI

```bash
# List all cameras
python -m camera_analytics.cli camera list

# Add USB webcam (replace 0 with your device index if needed)
python -m camera_analytics.cli camera add \
    --id "usb-cam-0" \
    --name "My USB Webcam" \
    --source-type usb \
    --source-url "0"

# Or add RTSP camera
python -m camera_analytics.cli camera add \
    --id "front-door" \
    --name "Front Door Cam" \
    --source-type rtsp \
    --source-url "rtsp://user:password@192.168.1.100:554/stream1"

# Add an analytics line for line crossing detection
python -m camera_analytics.cli analytics add-line \
    --id "entry-line" \
    --x1 100 --y1 200 --x2 500 --y2 200

# Add an alert rule (example: notify when person crosses 'entry-line')
python -m camera_analytics.cli alerts add \
    --id "person-crosses-entry" \
    --name "Person Crosses Entry Line" \
    --conditions-json '[{"field": "class_name", "operator": "eq", "value": "person"}, {"field": "line_id", "operator": "eq", "value": "entry-line"}]' \
    --actions-json '[{"type": "email", "recipient": "your_email@example.com"}]'

# List alert rules
python -m camera_analytics.cli alerts list

# View API documentation
open http://localhost:8000/docs


## Documentation

- **[Architecture](ARCHITECTURE.md)** - High-level system design and component overview
- **[Installation](INSTALL.md)** - Detailed setup and deployment instructions
- **[Changelog](CHANGELOG.md)** - All notable changes to the project
- **[Implementation Notes](IMPLEMENTATION_NOTES.md)** - Detailed notes on core component implementation and design decisions
- **[Contributing](CONTRIBUTING.md)** - How to contribute
- **[Examples](examples/)** - Runnable code examples

## Compatible Cameras

- **IP Cameras** - RTSP/ONVIF compatible (Hikvision, Dahua, Reolink, etc.)
- **USB Cameras** - Webcams, USB security cameras (V4L2)
- **Video Files** - MP4, AVI, MKV for testing and development

## Use Cases

- **Home Security** - Package delivery detection, visitor identification, intrusion alerts
- **Small Business** - Customer counting, employee safety, theft prevention
- **Retail Analytics** - Foot traffic patterns, dwell time analysis, occupancy monitoring
- **Access Control** - License plate recognition, restricted zone monitoring
- **Safety Monitoring** - Fall detection, PPE compliance, social distancing



## Performance (Aspirational / Reference)

On reference hardware (RTX 3060, 16GB RAM):
- Detection latency: 12-25ms per frame
- Throughput: 30-60 FPS per camera
- Max cameras: 16 simultaneous (1080p @ 15 FPS)
- Memory: ~200MB per camera stream

## Development

```bash
# Install dev dependencies (if not already installed during quick start)
pip install -r requirements-dev.txt

# Run tests
venv/bin/pytest tests/unit

# Run tests with coverage
venv/bin/pytest --cov=src/camera_analytics --cov-report=html tests/unit

# Format code
venv/bin/black src/ tests/
venv/bin/ruff format src/ tests/

# Linting
venv/bin/ruff check src/ tests/

# Type checking
venv/bin/mypy src/

# Pre-commit hooks
# (Requires pre-commit to be installed via requirements-dev.txt)
venv/bin/pre-commit install
venv/bin/pre-commit run --all-files
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Good First Issues
- Add support for new camera brands
- Implement additional object classes (e.g., animals, bicycles)
- Create custom notification channels (Slack, Discord)
- Write documentation and tutorials
- Improve test coverage

## Roadmap

### v0.1 (Current) - Alpha
- [x] Core detection and tracking
- [x] Basic alert system
- [x] REST API
- [ ] Web dashboard
- [ ] Unit tests (80%+ coverage)

### v0.2 - Beta
- [ ] MCP server implementation
- [ ] Multi-user authentication
- [ ] Recording playback UI
- [ ] Production deployment guides

### v1.0 - GA
- [ ] Mobile app (iOS/Android)
- [ ] Advanced analytics (heatmaps, reports)
- [ ] License plate recognition
- [ ] Edge TPU support

See [IMPROVEMENT_PLAN.md](IMPROVEMENT_PLAN.md) for detailed roadmap.

## Security

### Reporting Vulnerabilities
Please report security vulnerabilities to security@aiqso.io. Do not open public issues for security concerns.

### Best Practices
- Change default credentials immediately
- Use HTTPS in production
- Keep dependencies updated
- Review camera access logs regularly
- Enable encryption for stored credentials

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Ultralytics YOLOv8** - Object detection models
- **FastAPI** - Modern Python web framework
- **OpenCV** - Computer vision library
- **PyTorch** - Deep learning framework

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/qvidal01/camera-analytics/issues)
- **Discussions**: [GitHub Discussions](https://github.com/qvidal01/camera-analytics/discussions)

---

**Made with ❤️ by [AIQSO](https://aiqso.io)**

[⭐ Star this repo](https://github.com/qvidal01/camera-analytics) if you find it useful!
