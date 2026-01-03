# Architecture

This document outlines the architecture of the Camera Analytics system.

## Overview

The system is designed as a modular, service-oriented application for real-time video analysis. It processes video streams through a robust pipeline of detection, tracking, and analytics, generating actionable insights and alerts. It is composed of a core analytics engine, a web API for interaction, and a command-line interface for administration. The application is containerized using Docker for portability and ease of deployment.

## Components

The system is divided into the following main components:

- **FastAPI Web Server (`src/camera_analytics/api.py`):** The main entry point for the application. It hosts RESTful API endpoints for managing cameras, configuring analytics rules, defining alert rules, and accessing real-time event data.

- **Real-time Processing Pipeline (`src/camera_analytics/core/pipeline.py`):** This orchestrates the flow of data and logic between the core components, processing frames from cameras in near real-time.

- **Core Analytics Modules (`src/camera_analytics/core/`):** These modules form the heart of the system, responsible for processing video streams.
    - **`CameraManager`**: Manages the lifecycle of camera connections (RTSP, USB, File).
    - **`DetectionEngine`**: Performs AI-powered object detection on video frames using YOLOv8 models.
    - **`TrackingEngine`**: Tracks detected objects across frames using IoU-based matching.
    - **`AnalyticsEngine`**: Generates higher-level events and insights from tracked objects, such as line-crossing events.
    - **`AlertManager`**: Manages and triggers alerts based on evaluated rules, supporting multi-channel notifications (e.g., email, webhooks).
    - **`RecordingManager`**: Handles event-triggered video recording and storage.

- **Configuration (`src/camera_analytics/config/`):** Manages application settings using a Pydantic-based configuration model, with support for environment variables.

- **Command-Line Interface (`src/camera_analytics/cli.py`):** Provides administrative tools for interacting with the system from the command line, including camera management, rule configuration, and status checks.

## Technology Stack

- **Backend:** Python 3, FastAPI
- **AI/ML:** Ultralytics (YOLOv8) for detection, SciPy for tracking
- **Dependencies:** Pydantic (for configuration), OpenCV (for video processing), and others listed in `requirements.txt`.
- **Containerization:** Docker, Docker Compose
- **Testing:** Pytest
- **CLI:** Click

## Data Flow

The processing pipeline operates as follows:

1.  **Frame Acquisition:** The `CameraManager` continuously acquires video frames from configured camera sources.
2.  **Object Detection:** Frames are passed to the `DetectionEngine`, which uses YOLOv8 models to identify objects (e.g., people, cars) within each frame.
3.  **Object Tracking:** Detections from the `DetectionEngine` are fed into the `TrackingEngine`, which associates detections across consecutive frames to maintain persistent object tracks.
4.  **Analytics Generation:** The `AnalyticsEngine` analyzes these tracks to generate higher-level events, such as line-crossing events or zone intrusions.
5.  **Alert Evaluation:** Generated events are passed to the `AlertManager`, which evaluates them against predefined rules.
6.  **Action Execution:** If an event triggers a rule, the `AlertManager` executes configured actions, such as sending email notifications or triggering webhooks.
7.  **Video Recording:** The `RecordingManager` can be triggered by alert actions to save relevant video clips.
8.  **API/CLI Interaction:** The FastAPI server exposes endpoints to configure cameras, rules, view real-time data, while the CLI provides administrative access.
