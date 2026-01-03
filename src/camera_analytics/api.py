import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from camera_analytics.config import get_settings
from camera_analytics.core.alert_manager import AlertManager
from camera_analytics.core.analytics_engine import AnalyticsEngine
from camera_analytics.core.camera_manager import CameraManager
from camera_analytics.core.detection_engine import DetectionEngine
from camera_analytics.core.pipeline import main_pipeline
from camera_analytics.core.recording_manager import RecordingManager
from camera_analytics.core.tracking_engine import TrackingEngine

logger = logging.getLogger(__name__)
settings = get_settings()

# This dictionary will hold the application's core components
# and will be accessible from the API routers.
app_state = {
    "settings": settings,
    "camera_manager": None,
    "detection_engine": None,
    "tracking_engine": None,
    "analytics_engine": None,
    "alert_manager": None,
    "recording_manager": None,
    "pipeline_task": None,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.
    Initializes core components and starts the main processing pipeline.
    """
    logger.info("Camera Analytics API starting up")

    # Attach the state to the app instance
    app.state.core_components = app_state

    # Instantiate core components
    camera_manager = CameraManager()
    detection_engine = DetectionEngine(
        model_name=settings.default_detection_model,
        device=settings.detection_device,
        confidence_threshold=settings.detection_confidence_threshold,
    )
    tracking_engine = TrackingEngine()
    analytics_engine = AnalyticsEngine()
    alert_manager = AlertManager(settings)
    recording_manager = RecordingManager(settings, camera_manager)

    # Load the detection model
    await detection_engine.load_model()

    # Store components in app state
    app.state.core_components["camera_manager"] = camera_manager
    app.state.core_components["detection_engine"] = detection_engine
    app.state.core_components["tracking_engine"] = tracking_engine
    app.state.core_components["analytics_engine"] = analytics_engine
    app.state.core_components["alert_manager"] = alert_manager
    app.state.core_components["recording_manager"] = recording_manager

    # Start the main processing pipeline in the background
    pipeline_task = asyncio.create_task(main_pipeline(app.state.core_components))
    app.state.core_components["pipeline_task"] = pipeline_task
    logger.info("Main processing pipeline started.")

    yield # Application starts here

    logger.info("Camera Analytics API shutting down")

    # Stop the pipeline
    if app.state.core_components["pipeline_task"]:
        app.state.core_components["pipeline_task"].cancel()
        await app.state.core_components["pipeline_task"]

    # Shutdown core components
    if app.state.core_components["camera_manager"]:
        await app.state.core_components["camera_manager"].shutdown()
    if app.state.core_components["alert_manager"]:
        await app.state.core_components["alert_manager"].shutdown()
    if app.state.core_components["recording_manager"]:
        await app.state.core_components["recording_manager"].stop_all_recordings()


def create_app() -> FastAPI:
    app_instance = FastAPI(
        title="Camera Analytics API",
        description="AI-powered security camera analytics",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Attach the state to the app instance
    app_instance.state.core_components = app_state

    # CORS middleware
    app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    from camera_analytics.routers import alerts, analytics, cameras

    app_instance.include_router(cameras.router, prefix="/api", tags=["Cameras"])
    app_instance.include_router(analytics.router, prefix="/api", tags=["Analytics"])
    app_instance.include_router(alerts.router, prefix="/api", tags=["Alerts"])

    # Temporarily print registered routes for debugging
    logger.info("Registered routes:")
    for route in app_instance.routes:
        logger.info(f"  {route.path} - {route.name}")

    return app_instance


app = create_app() # This line must be removed or handled differently
