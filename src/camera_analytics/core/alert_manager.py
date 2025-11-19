"""
Alert management and rule evaluation engine.

This module handles alert rule creation, evaluation, and multi-channel notifications.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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

        if self.operator == RuleConditionOperator.EQUALS:
            return field_value == self.value
        elif self.operator == RuleConditionOperator.IN:
            return field_value in self.value
        # ... other operators

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

    Evaluates rules against detection events and triggers configured actions.
    """

    def __init__(self):
        """Initialize alert manager."""
        self.rules: Dict[str, AlertRule] = {}
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
            if action_type == "email":
                await self._send_email(action, event)
            elif action_type == "webhook":
                await self._send_webhook(action, event)
            # ... other actions

    async def _send_email(self, action: Dict, event: Dict) -> None:
        """Send email notification (stub)."""
        logger.info(f"Sending email alert: {event}")

    async def _send_webhook(self, action: Dict, event: Dict) -> None:
        """Send webhook notification (stub)."""
        logger.info(f"Sending webhook alert: {event}")
