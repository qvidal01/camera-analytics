import asyncio
import json
import logging
from typing import Any

import click

from camera_analytics.config import get_settings
from camera_analytics.core.alert_manager import (
    AlertManager,
    AlertRule,
    RuleCondition,
    RuleConditionOperator,
)
from camera_analytics.core.analytics_engine import AnalyticsEngine, Line
from camera_analytics.core.camera_manager import CameraConfig, CameraManager, CameraType
from camera_analytics.core.detection_engine import DetectionEngine
from camera_analytics.core.recording_manager import RecordingManager
from camera_analytics.core.tracking_engine import TrackingEngine
from camera_analytics.utils.logging import setup_logging

settings = get_settings()
logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def main(ctx: click.Context, debug: bool):
    """Camera Analytics CLI."""
    setup_logging(level="DEBUG" if debug else settings.log_level)
    ctx.ensure_object(dict)

    async def _ainit_components():
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

        ctx.obj["camera_manager"] = camera_manager
        ctx.obj["detection_engine"] = detection_engine
        ctx.obj["tracking_engine"] = tracking_engine
        ctx.obj["analytics_engine"] = analytics_engine
        ctx.obj["alert_manager"] = alert_manager
        ctx.obj["recording_manager"] = recording_manager

    asyncio.run(_ainit_components())


@main.command()
def version():
    """Show version information."""
    from camera_analytics import __version__

    click.echo(f"Camera Analytics v{__version__}")


@main.group()
def camera():
    """Camera management commands."""
    pass


@camera.command("list")
@click.pass_obj
def camera_list(obj: dict[str, Any]):
    """List all cameras."""
    camera_manager: CameraManager = obj["camera_manager"]

    async def _alist_cameras():
        cameras = await camera_manager.list_cameras()
        if not cameras:
            click.echo("No cameras configured.")
            return

        click.echo("Configured Cameras:")
        for cam_id, cam_info in cameras.items():
            click.echo(f"  ID: {cam_id}, Name: {cam_info['name']}, Type: {cam_info['type']}, Status: {cam_info['status']}")

    asyncio.run(_alist_cameras())


@camera.command("add")
@click.pass_obj
@click.option("--id", required=True, help="Unique ID for the camera")
@click.option("--name", required=True, help="Human-readable name for the camera")
@click.option("--source-type", type=click.Choice([ct.value for ct in CameraType]), required=True, help="Type of camera source")
@click.option("--source-url", required=True, help="Connection URL or device path")
@click.option("--fps", type=int, default=15, help="Target frames per second")
@click.option("--resolution", default="1920x1080", help="Target resolution as WIDTHxHEIGHT")
def camera_add(obj: dict[str, Any], id: str, name: str, source_type: str, source_url: str, fps: int, resolution: str):
    """Add a new camera."""
    camera_manager: CameraManager = obj["camera_manager"]

    width, height = map(int, resolution.split("x"))
    config = CameraConfig(
        id=id,
        name=name,
        source_type=CameraType(source_type),
        source_url=source_url,
        fps=fps,
        resolution=(width, height),
    )

    async def _aadd_camera():
        try:
            success = await camera_manager.add_camera(config)
            if success:
                click.echo(f"Camera '{name}' (ID: {id}) added successfully.")
            else:
                click.echo(f"Failed to add camera '{name}' (ID: {id}). Check logs for details.")
        except ValueError as e:
            click.echo(f"Error: {e}", err=True)

    asyncio.run(_aadd_camera())


@camera.command("remove")
@click.pass_obj
@click.option("--id", required=True, help="ID of the camera to remove")
def camera_remove(obj: dict[str, Any], id: str):
    """Remove a camera."""
    camera_manager: CameraManager = obj["camera_manager"]

    async def _aremove_camera():
        if id not in camera_manager.cameras:
            click.echo(f"Error: Camera with ID '{id}' not found.", err=True)
            return
        await camera_manager.remove_camera(id)
        click.echo(f"Camera '{id}' removed successfully.")

    asyncio.run(_aremove_camera())


@main.group()
def alerts():
    """Alert rule management commands."""
    pass


@alerts.command("list")
@click.pass_obj
def alert_rule_list(obj: dict[str, Any]):
    """List all configured alert rules."""
    alert_manager: AlertManager = obj["alert_manager"]

    async def _alist_rules():
        rules = list(alert_manager.rules.values())
        if not rules:
            click.echo("No alert rules configured.")
            return

        click.echo("Configured Alert Rules:")
        for rule in rules:
            click.echo(f"  ID: {rule.id}, Name: {rule.name}, Enabled: {rule.enabled}")
            click.echo("    Conditions:")
            for cond in rule.conditions:
                click.echo(f"      - Field: {cond.field}, Operator: {cond.operator.value}, Value: {cond.value}")
            click.echo("    Actions:")
            for action in rule.actions:
                click.echo(f"      - Type: {action.get('type')}, Details: {action}")

    asyncio.run(_alist_rules())


@alerts.command("add")
@click.pass_obj
@click.option("--id", required=True, help="Unique ID for the alert rule")
@click.option("--name", required=True, help="Human-readable name for the rule")
@click.option("--description", default="", help="Description of the rule")
@click.option("--conditions-json", required=True, help="JSON string of conditions for the rule")
@click.option("--actions-json", required=True, help="JSON string of actions for the rule")
@click.option("--enabled/--disabled", default=True, help="Enable or disable the rule")
@click.option("--priority", type=int, default=1, help="Priority of the rule")
def alert_rule_add(
    obj: dict[str, Any],
    id: str,
    name: str,
    description: str,
    conditions_json: str,
    actions_json: str,
    enabled: bool,
    priority: int,
):
    """Add a new alert rule."""
    alert_manager: AlertManager = obj["alert_manager"]

    try:
        conditions_data = json.loads(conditions_json)
        actions_data = json.loads(actions_json)

        conditions = []
        for cond_data in conditions_data:
            conditions.append(
                RuleCondition(
                    field=cond_data["field"],
                    operator=RuleConditionOperator(cond_data["operator"]),
                    value=cond_data["value"],
                )
            )

        rule = AlertRule(
            id=id,
            name=name,
            description=description,
            conditions=conditions,
            actions=actions_data,
            enabled=enabled,
            priority=priority,
        )
        alert_manager.add_rule(rule)
        click.echo(f"Alert rule '{name}' (ID: {id}) added successfully.")

    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON for conditions or actions: {e}", err=True)
    except KeyError as e:
        click.echo(f"Error: Missing key in condition data: {e}", err=True)
    except ValueError as e:
        click.echo(f"Error: Invalid value in condition data: {e}", err=True)


@alerts.command("remove")


@click.pass_obj


@click.option("--id", required=True, help="ID of the alert rule to remove")


def alert_rule_remove(obj: dict[str, Any], id: str):


    """Remove an alert rule."""


    alert_manager: AlertManager = obj["alert_manager"]





    if id not in alert_manager.rules:


        click.echo(f"Error: Alert rule with ID '{id}' not found.", err=True)


        return





    alert_manager.remove_rule(id)


    click.echo(f"Alert rule '{id}' removed successfully.")








@main.group()


def analytics():


    """Analytics configuration commands."""


    pass








@analytics.command("list-lines")


@click.pass_obj


def analytics_list_lines(obj: dict[str, Any]):


    """List all configured analytics lines."""


    analytics_engine: AnalyticsEngine = obj["analytics_engine"]





    lines = analytics_engine._lines.values()


    if not lines:


        click.echo("No analytics lines configured.")


        return





    click.echo("Configured Analytics Lines:")


    for line in lines:


        click.echo(f"  ID: {line.id}, P1: ({line.x1}, {line.y1}), P2: ({line.x2}, {line.y2})")








@analytics.command("add-line")


@click.pass_obj


@click.option("--id", required=True, help="Unique ID for the line")


@click.option("--x1", type=int, required=True, help="X-coordinate of the first point")


@click.option("--y1", type=int, required=True, help="Y-coordinate of the first point")


@click.option("--x2", type=int, required=True, help="X-coordinate of the second point")


@click.option("--y2", type=int, required=True, help="Y-coordinate of the second point")


def analytics_add_line(obj: dict[str, Any], id: str, x1: int, y1: int, x2: int, y2: int):


    """Add a new line for line-crossing detection."""


    analytics_engine: AnalyticsEngine = obj["analytics_engine"]





    line = Line(id=id, x1=x1, y1=y1, x2=x2, y2=y2)


    try:


        analytics_engine.add_line(line)


        click.echo(f"Analytics line '{id}' added successfully.")


    except ValueError as e:


        click.echo(f"Error: {e}", err=True)








@analytics.command("remove-line")


@click.pass_obj


@click.option("--id", required=True, help="ID of the line to remove")


def analytics_remove_line(obj: dict[str, Any], id: str):


    """Remove an analytics line."""


    analytics_engine: AnalyticsEngine = obj["analytics_engine"]





    if id not in analytics_engine._lines:


        click.echo(f"Error: Analytics line with ID '{id}' not found.", err=True)


        return





    analytics_engine.remove_line(id)


    click.echo(f"Analytics line '{id}' removed successfully.")








if __name__ == "__main__":


    main()
