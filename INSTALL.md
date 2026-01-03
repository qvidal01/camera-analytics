# Installation

This document provides instructions on how to install and run the Camera Analytics system.

## Prerequisites

- Python 3.10 or later
- (Optional) Docker and Docker Compose for containerized deployment
- (Optional) NVIDIA GPU with CUDA 11.8+ for acceleration

## Local Installation and Execution

For local development or direct Python execution:

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/qvidal01/camera-analytics.git
    cd camera-analytics
    ```

2.  **Create and activate a Python virtual environment:**

    ```bash
    python3.10 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    venv/bin/pip install -r requirements.txt -r requirements-dev.txt
    ```
    (Note: `requirements-dev.txt` is recommended for local development as it includes testing and linting tools).

4.  **Configure environment variables:**

    Copy the example environment file:
    ```bash
    cp .env.example .env
    ```
    Modify the `.env` file with your desired settings (e.g., SMTP, Webhook URLs).

5.  **Run the FastAPI API server:**

    ```bash
    venv/bin/uvicorn camera_analytics.api:app --host 0.0.0.0 --port 8000
    ```
    The API will be available at `http://localhost:8000`.

6.  **Use the Command-Line Interface (CLI):**

    ```bash
    venv/bin/python -m camera_analytics.cli --help
    ```

## Dockerized Deployment

For production deployments using Docker:

1.  **Prerequisites:** Ensure Docker and Docker Compose are installed.
2.  **Clone the repository** (if you haven't already).
3.  **Set up environment variables:**
    ```bash
    cp .env.example .env
    ```
    Modify the `.env` file with your desired settings.
4.  **Build and run the application:**

    ```bash
    docker-compose up --build -d
    ```
    This will build the Docker image and start the application in detached mode. The API will be available at `http://localhost:8000`.

5.  **Stop the application:**

    ```bash
    docker-compose down
    ```
