#!/usr/bin/env python3
"""
Create Alert Rule Example.

This example demonstrates:
1. Initializing the alert manager
2. Creating a custom alert rule
3. Evaluating rules against events
"""

import asyncio
import logging
from datetime import datetime

from camera_analytics.core.alert_manager import (
    AlertManager,
    AlertRule,
    RuleCondition,
    RuleConditionOperator,
)
from camera_analytics.utils.logging import setup_logging

# Configure logging
setup_logging(level="INFO")
logger = logging.getLogger(__name__)


async def main():
    """Run the example."""
    logger.info("=== Camera Analytics - Create Alert Rule ===")

    # Initialize alert manager
    alert_manager = AlertManager()

    # Create a rule: Alert when person detected at night
    rule = AlertRule(
        id="rule-001",
        name="Nighttime Person Detection",
        description="Alert when person detected between 10 PM and 6 AM",
        conditions=[
            RuleCondition(
                field="class",
                operator=RuleConditionOperator.EQUALS,
                value="person",
            ),
            # In production, would add time condition:
            # RuleCondition(
            #     field="time",
            #     operator=RuleConditionOperator.BETWEEN,
            #     value=["22:00", "06:00"]
            # )
        ],
        actions=[
            {
                "type": "email",
                "to": "user@example.com",
                "subject": "Person detected at night",
            },
            {"type": "record", "duration": 30},
        ],
        enabled=True,
        priority=2,
    )

    # Add rule
    alert_manager.add_rule(rule)
    logger.info(f"✓ Created rule: {rule.name}")

    # Simulate an event
    event = {
        "class": "person",
        "confidence": 0.85,
        "camera_id": "front-door",
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Evaluate event against rules
    logger.info("Evaluating event against rules...")
    triggered = await alert_manager.evaluate(event)

    if triggered:
        logger.info(f"✓ Rule triggered: {triggered}")
    else:
        logger.info("No rules triggered")

    # List all rules
    logger.info(f"Total rules: {len(alert_manager.rules)}")

    logger.info("Done!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Error: {e}")
