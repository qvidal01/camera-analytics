"""
Unit tests for the AlertManager module.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from camera_analytics.config.settings import get_settings
from camera_analytics.core.alert_manager import (
    AlertManager,
    AlertRule,
    RuleCondition,
    RuleConditionOperator,
)


@pytest.fixture
def settings():
    """Fixture to provide application settings."""
    s = get_settings()
    s.smtp_host = "smtp.test.com"
    s.smtp_user = "user"
    s.smtp_password = "password"
    s.alert_email_to = "test@example.com"
    s.webhook_url = "https://test.webhook.url"
    return s


@pytest.fixture
def alert_manager(settings):
    """Fixture to create an AlertManager instance."""
    return AlertManager(settings)


def test_add_and_remove_rule(alert_manager):
    """Test adding and removing an alert rule."""
    rule = AlertRule(
        id="rule1",
        name="Test Rule",
        description="A test rule",
        conditions=[],
        actions=[],
    )
    alert_manager.add_rule(rule)
    assert "rule1" in alert_manager.rules

    alert_manager.remove_rule("rule1")
    assert "rule1" not in alert_manager.rules


@pytest.mark.asyncio
async def test_rule_evaluation_success(alert_manager):
    """Test successful evaluation of a rule."""
    rule = AlertRule(
        id="rule1",
        name="Person Detected",
        description="Alert when a person is detected",
        conditions=[
            RuleCondition(
                field="class_name",
                operator=RuleConditionOperator.EQUALS,
                value="person",
            ),
            RuleCondition(
                field="confidence",
                operator=RuleConditionOperator.GREATER_THAN,
                value=0.8,
            ),
        ],
        actions=[],
    )
    alert_manager.add_rule(rule)

    event = {"class_name": "person", "confidence": 0.9}
    triggered = await alert_manager.evaluate(event)
    assert "rule1" in triggered


@pytest.mark.asyncio
async def test_rule_evaluation_failure(alert_manager):
    """Test failed evaluation of a rule."""
    rule = AlertRule(
        id="rule1",
        name="Car Detected",
        description="Alert when a car is detected",
        conditions=[
            RuleCondition(
                field="class_name",
                operator=RuleConditionOperator.EQUALS,
                value="car",
            )
        ],
        actions=[],
    )
    alert_manager.add_rule(rule)

    event = {"class_name": "person", "confidence": 0.9}
    triggered = await alert_manager.evaluate(event)
    assert "rule1" not in triggered


@pytest.mark.asyncio
async def test_disabled_rule_not_evaluated(alert_manager):
    """Test that a disabled rule is not evaluated."""
    rule = AlertRule(
        id="rule1",
        name="Disabled Rule",
        description="This rule should not be triggered",
        conditions=[
            RuleCondition(
                field="class_name",
                operator=RuleConditionOperator.EQUALS,
                value="person",
            )
        ],
        actions=[],
        enabled=False,
    )
    alert_manager.add_rule(rule)

    event = {"class_name": "person", "confidence": 0.9}
    triggered = await alert_manager.evaluate(event)
    assert "rule1" not in triggered


@pytest.mark.asyncio
@patch("aiosmtplib.send", new_callable=AsyncMock)
async def test_email_action_triggered(mock_send, alert_manager):
    """Test that an email action is triggered on rule match."""
    rule = AlertRule(
        id="rule1",
        name="Email Rule",
        description="Sends an email",
        conditions=[],
        actions=[{"type": "email", "recipient": "override@example.com"}],
    )
    alert_manager.add_rule(rule)

    await alert_manager.evaluate({"any_event": True})
    mock_send.assert_called_once()

    # Check that the recipient was the override from the action
    _, kwargs = mock_send.call_args
    assert "override@example.com" in kwargs["recipients"]


@pytest.mark.asyncio
async def test_webhook_action_triggered(alert_manager):
    """Test that a webhook action is triggered on rule match."""
    rule = AlertRule(
        id="rule1",
        name="Webhook Rule",
        description="Sends a webhook",
        conditions=[],
        actions=[{"type": "webhook", "url": "https://override.webhook.url"}],
    )
    alert_manager.add_rule(rule)

    async def mock_post(*args, **kwargs):
        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    with patch.object(alert_manager._http_client, "post", side_effect=mock_post) as mock_post_patched:
        await alert_manager.evaluate({"any_event": True})

        mock_post_patched.assert_called_once()

        # Check that the URL was the override from the action
        called_url = mock_post_patched.call_args[0][0]
        assert called_url == "https://override.webhook.url"

    await alert_manager.shutdown()
