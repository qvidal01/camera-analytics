"""
Alert management and rule evaluation engine.

This module handles alert rule creation, evaluation, and multi-channel notifications.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import aiosmtplib
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

    def evaluate(self, context: dict[str, Any]) -> bool:
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
    conditions: list[RuleCondition]
    actions: list[dict[str, Any]]
    enabled: bool = True
    priority: int = 1


class AlertManager:
    """
    Manages alert rules and executes notifications.

    Evaluates rules against detection events and triggers configured actions.
    """

    def __init__(self, settings: Settings):
        """Initialize alert manager."""
        self.rules: dict[str, AlertRule] = {}
        self.settings = settings
        self._http_client = httpx.AsyncClient()
        logger.info("AlertManager initialized")

    def add_rule(self, rule: AlertRule) -> None:
        """Add a new alert rule."""
        self.rules[rule.id] = rule
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_id: str) -> None:
        """Remove an alert rule."""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")

    async def evaluate(self, event: dict[str, Any]) -> list[str]:
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

    async def _execute_actions(self, rule: AlertRule, event: dict[str, Any]) -> None:
        """Execute actions for triggered rule."""
        for action in rule.actions:
            action_type = action.get("type")
            if action_type == "email":
                await self._send_email(action, rule, event)
            elif action_type == "webhook":
                await self._send_webhook(action, rule, event)
            # ... other actions

    async def _send_email(self, action: dict, rule: AlertRule, event: dict) -> None:
        """Send email notification."""
        if not all([
            self.settings.smtp_host,
            self.settings.smtp_user,
            self.settings.smtp_password,
        ]):
            logger.warning("SMTP settings not configured. Cannot send email alert.")
            return

        to_email = action.get("recipient", self.settings.alert_email_to)
        if not to_email:
            logger.warning("No recipient for email alert.")
            return

        subject = f"Alert: {rule.name}"
        body = f"""
        An alert has been triggered.

        Rule: {rule.name}
        Description: {rule.description}
        Timestamp: {event.get('timestamp')}

        Event Details:
        {json.dumps(event, indent=2, default=str)}
        """

        try:
            await aiosmtplib.send(
                hostname=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_user,
                password=self.settings.smtp_password,
                sender=self.settings.smtp_from,
                recipients=[to_email],
                message=f"Subject: {subject}\n\n{body}",
                start_tls=True,
            )
            logger.info(f"Sent email alert for rule '{rule.name}' to {to_email}")
        except Exception as e:
            logger.exception(f"Failed to send email alert: {e}")

    async def _send_webhook(self, action: dict, rule: AlertRule, event: dict) -> None:
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

