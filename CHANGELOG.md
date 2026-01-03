# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Implemented `CameraManager` for managing various camera sources (RTSP, USB, File).
- Developed `DetectionEngine` with YOLOv8 integration for AI object detection.
- Created `TrackingEngine` using IoU-based matching for persistent object tracking.
- Implemented `AnalyticsEngine` for generating events like line crossings from tracks.
- Built `AlertManager` with rule-based evaluation and multi-channel notifications (email, webhook).
- Designed `RecordingManager` for event-triggered video recording.
- Implemented FastAPI API endpoints for camera, analytics, and alert management.
- Developed comprehensive CLI commands for camera, analytics, and alert configuration.
- Added extensive unit tests for `CameraManager`, `DetectionEngine`, `TrackingEngine`, `AnalyticsEngine`, and `AlertManager` modules.
- Created foundational documentation: `ARCHITECTURE.md`, `INSTALL.md`, `CHANGELOG.md`, `IMPLEMENTATION_NOTES.md`.
- Refactored FastAPI startup/shutdown to use `lifespan` context manager.

### Changed

- Updated core dependencies including `scipy` for tracking algorithms.
- Refined project documentation (`README.md`, `ARCHITECTURE.md`, `INSTALL.md`) to reflect current implementation.

### Fixed

- Corrected `USBCamera` device index parsing logic in `CameraManager`.
- Adjusted `TrackingEngine`'s `min_hits` confirmation logic and associated unit tests.
- Replaced deprecated `datetime.utcnow()` with `datetime.now(datetime.UTC)`.
- Resolved `NameError` and `AttributeError` issues in `cli.py` for correct command registration.
