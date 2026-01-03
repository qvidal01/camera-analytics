"""
API router for alert management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from camera_analytics.core.alert_manager import AlertManager, AlertRule

router = APIRouter()


def get_alert_manager(request: Request) -> AlertManager:
    """Dependency to get the AlertManager instance."""
    return request.app.state.core_components["alert_manager"]


@router.post("/alerts/rules", status_code=201)
async def add_alert_rule(
    rule: AlertRule,
    alert_manager: AlertManager = Depends(get_alert_manager),
):
    """Add a new alert rule."""
    if rule.id in alert_manager.rules:
        raise HTTPException(status_code=409, detail=f"Rule with ID {rule.id} already exists.")
    alert_manager.add_rule(rule)
    return {"message": "Alert rule added successfully."}


@router.delete("/alerts/rules/{rule_id}", status_code=204)
async def remove_alert_rule(
    rule_id: str,
    alert_manager: AlertManager = Depends(get_alert_manager),
):
    """Remove an alert rule."""
    if rule_id not in alert_manager.rules:
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    alert_manager.remove_rule(rule_id)
    return


@router.get("/alerts/rules", response_model=list[AlertRule])
async def list_alert_rules(alert_manager: AlertManager = Depends(get_alert_manager)):
    """List all defined alert rules."""
    return list(alert_manager.rules.values())


@router.get("/alerts/rules/{rule_id}", response_model=AlertRule)
async def get_alert_rule(
    rule_id: str,
    alert_manager: AlertManager = Depends(get_alert_manager),
):
    """Get a specific alert rule by ID."""
    rule = alert_manager.rules.get(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    return rule


@router.patch("/alerts/rules/{rule_id}/enable", response_model=AlertRule)
async def enable_alert_rule(
    rule_id: str,
    alert_manager: AlertManager = Depends(get_alert_manager),
):
    """Enable an alert rule."""
    rule = alert_manager.rules.get(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    rule.enabled = True
    return rule


@router.patch("/alerts/rules/{rule_id}/disable", response_model=AlertRule)
async def disable_alert_rule(
    rule_id: str,
    alert_manager: AlertManager = Depends(get_alert_manager),
):
    """Disable an alert rule."""
    rule = alert_manager.rules.get(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Alert rule not found.")
    rule.enabled = False
    return rule
