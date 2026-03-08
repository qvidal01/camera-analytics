"""
Alert management and rule evaluation engine.

This module handles alert rule creation, evaluation, and multi-channel notifications
including Slack integration.
"""

import logging
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx

from camera_analytics.config.settings import Settings

logger = logging.getLogger(__name__)


class RuleConditionOperator(Enum):
    """Operators for rule conditions."""

    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    BETWEEN = "between"


class AlertAction(Enum):
    """Types of alert actions."""

    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    RECORD = "record"
    NOTIFICATION = "notification"


@dataclass
class RuleCondition:
    """A single condition in an alert rule."""

    field: str  # e.g., "class", "time", "zone", "confidence"
    operator: RuleConditionOperator
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context."""
        if self.field not in context:
            return False

        field_value = context[self.field]

        try:
            if self.operator == RuleConditionOperator.EQUALS:
                return field_value == self.value
            elif self.operator == RuleConditionOperator.NOT_EQUALS:
                return field_value != self.value
            elif self.operator == RuleConditionOperator.GREATER_THAN:
                return field_value > self.value
            elif self.operator == RuleConditionOperator.LESS_THAN:
                return field_value < self.value
            elif self.operator == RuleConditionOperator.IN:
                return field_value in self.value
            elif self.operator == RuleConditionOperator.NOT_IN:
                return field_value not in self.value
            elif self.operator == RuleConditionOperator.CONTAINS:
                if not isinstance(field_value, (str, list, tuple)):
                    return False
                return self.value in field_value
            elif self.operator == RuleConditionOperator.BETWEEN:
                if not isinstance(self.value, (list, tuple)) or len(self.value) != 2:
                    return False
                return self.value[0] <= field_value <= self.value[1]
        except (TypeError, ValueError) as e:
            logger.warning(f"Could not evaluate rule condition: {e}")
            return False

        return False


@dataclass
class AlertRule:
    """
    An alert rule with conditions and actions.

    Attributes:
        id: Unique rule identifier
        name: Human-readable rule name
        description: Rule description
        conditions: List of conditions (AND logic)
        actions: List of actions to execute when triggered
        enabled: Whether rule is active
        priority: Rule priority (higher = more important)
    """

    id: str
    name: str
    description: str
    conditions: List[RuleCondition]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    priority: int = 1


class AlertManager:
    """
    Manages alert rules and executes notifications.

    Evaluates rules against detection events and triggers configured actions
    including Slack notifications.
    """

    def __init__(self, settings: Settings):
        """Initialize alert manager."""
        self.rules: Dict[str, AlertRule] = {}
        self.settings = settings
        self._http_client = httpx.AsyncClient()
        self._slack_cooldowns: Dict[str, float] = {}  # camera_id -> last_alert_time
        logger.info("AlertManager initialized")
        if settings.slack_bot_token:
            logger.info(f"Slack alerts enabled -> {settings.slack_channel}")

    def add_rule(self, rule: AlertRule) -> None:
        """Add a new alert rule."""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> None:
        """Remove an alert rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")

    async def evaluate(self, event: Dict[str, Any]) -> List[str]:
        """
        Evaluate event against all rules.

        Args:
            event: Event data (detections, timestamp, camera, etc.)

        Returns:
            List[str]: List of triggered rule IDs
        """
        triggered = []

        for rule in self.rules.values():
            if not rule.enabled:
                continue

            # Check if all conditions are met
            if all(cond.evaluate(event) for cond in rule.conditions):
                triggered.append(rule.id)
                await self._execute_actions(rule, event)

        return triggered

    async def _execute_actions(self, rule: AlertRule, event: Dict[str, Any]) -> None:
        """Execute actions for triggered rule."""
        for action in rule.actions:
            action_type = action.get("type")
            if action_type == "webhook":
                await self._send_webhook(action, rule, event)
            elif action_type == "slack":
                await self.send_slack_alert(
                    camera_name=event.get("camera_id", "unknown"),
                    detections=event.get("detections", []),
                    scene_description=event.get("scene_description"),
                )

    async def send_slack_alert(
        self,
        camera_name: str,
        detections: List[str],
        scene_description: Optional[str] = None,
        camera_id: Optional[str] = None,
    ) -> bool:
        """
        Send a detection alert to Slack with cooldown.

        Returns True if message was sent, False if on cooldown or failed.
        """
        token = self.settings.slack_bot_token
        if not token:
            return False

        # Check cooldown per camera
        cooldown_key = camera_id or camera_name
        now = time.time()
        last_alert = self._slack_cooldowns.get(cooldown_key, 0)
        if now - last_alert < self.settings.slack_cooldown_seconds:
            return False

        # Build the message
        det_summary = ", ".join(detections) if detections else "motion detected"
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"Camera Alert: {camera_name}"},
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Detected:*\n{det_summary}"},
                    {"type": "mrkdwn", "text": f"*Time:*\n{datetime.now().strftime('%I:%M:%S %p')}"},
                ],
            },
        ]

        if scene_description:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Scene:* {scene_description[:300]}"},
            })

        try:
            resp = await self._http_client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "channel": self.settings.slack_channel,
                    "text": f"Alert: {det_summary} at {camera_name}",
                    "blocks": blocks,
                },
                timeout=10.0,
            )
            data = resp.json()
            if data.get("ok"):
                self._slack_cooldowns[cooldown_key] = now
                logger.info(f"Slack alert sent for {camera_name}: {det_summary}")
                return True
            else:
                logger.warning(f"Slack API error: {data.get('error')}")
                return False
        except Exception as e:
            logger.warning(f"Failed to send Slack alert: {e}")
            return False

    async def _send_webhook(self, action: Dict, rule: AlertRule, event: Dict) -> None:
        """Send webhook notification."""
        url = action.get("url", self.settings.webhook_url)
        if not url:
            logger.warning("No URL for webhook alert.")
            return

        payload = {
            "rule_id": rule.id,
            "rule_name": rule.name,
            "event": event,
        }

        try:
            response = await self._http_client.post(url, json=payload, timeout=5.0)
            response.raise_for_status()
            logger.info(f"Sent webhook alert for rule '{rule.name}' to {url}")
        except httpx.HTTPError as e:
            logger.exception(f"Failed to send webhook alert: {e}")

    async def shutdown(self):
        """Close the HTTP client."""
        await self._http_client.aclose()
        logger.info("AlertManager shutdown complete.")

