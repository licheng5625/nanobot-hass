"""The Nanobot integration.

This integration allows nanobot to act as a conversation agent for Home Assistant.
Nanobot connects to HA via WebSocket and receives conversation requests via events.

Flow:
1. User speaks to HA Assist
2. HA fires event: nanobot_conversation_request
3. Nanobot (connected via WebSocket) receives the event
4. Nanobot processes with LLM
5. Nanobot fires event: nanobot_conversation_response
6. HA receives response and returns to user

Async notifications:
- Nanobot can also fire nanobot_notification events
- These create persistent notifications in HA
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import config_validation as cv

from .const import (
    DEFAULT_TIMEOUT,
    DOMAIN,
    EVENT_CONVERSATION_REQUEST,
    EVENT_CONVERSATION_RESPONSE,
    EVENT_NOTIFICATION,
    LOGGER,
)

PLATFORMS = (Platform.CONVERSATION,)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass
class NanobotData:
    """Runtime data for Nanobot integration."""

    pending_requests: dict[str, asyncio.Future[dict[str, Any]]] = field(
        default_factory=dict
    )


type NanobotConfigEntry = ConfigEntry[NanobotData]


async def async_setup_entry(hass: HomeAssistant, entry: NanobotConfigEntry) -> bool:
    """Set up Nanobot from a config entry."""
    entry.runtime_data = NanobotData()

    @callback
    def handle_response(event: Event) -> None:
        """Handle response from nanobot."""
        request_id = event.data.get("request_id")
        if not request_id:
            LOGGER.warning("Received response without request_id")
            return

        future = entry.runtime_data.pending_requests.get(request_id)
        if future and not future.done():
            # First response: return to conversation agent
            future.set_result(event.data)
        else:
            # Subsequent response (same request_id): convert to notification
            response = event.data.get("response", "")
            if response:
                LOGGER.info("Converting follow-up response to notification: %s", request_id)
                hass.async_create_task(
                    hass.services.async_call(
                        "persistent_notification",
                        "create",
                        {
                            "title": "Nanobot",
                            "message": response,
                            "notification_id": f"nanobot_{request_id[:8]}",
                        },
                    )
                )
                LOGGER.debug("Created notification for request: %s", request_id)

    @callback
    def handle_notification(event: Event) -> None:
        """Handle async notification from nanobot via WebSocket."""
        title = event.data.get("title", "Nanobot")
        message = event.data.get("message", "")
        notification_id = event.data.get("notification_id")

        LOGGER.info("Received notification from nanobot: %s", title)

        # Create persistent notification in HA
        hass.async_create_task(
            hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": title,
                    "message": message,
                    "notification_id": notification_id or f"nanobot_{id(event)}",
                },
            )
        )

    # Listen for responses from nanobot
    entry.async_on_unload(
        hass.bus.async_listen(EVENT_CONVERSATION_RESPONSE, handle_response)
    )

    # Listen for async notifications from nanobot
    entry.async_on_unload(
        hass.bus.async_listen(EVENT_NOTIFICATION, handle_notification)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    LOGGER.info(
        "Nanobot integration ready. Waiting for nanobot to connect via WebSocket "
        "and subscribe to '%s' events",
        EVENT_CONVERSATION_REQUEST,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: NanobotConfigEntry) -> bool:
    """Unload Nanobot."""
    # Cancel any pending requests
    for future in entry.runtime_data.pending_requests.values():
        if not future.done():
            future.cancel()

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_send_request(
    hass: HomeAssistant,
    entry: NanobotConfigEntry,
    request_id: str,
    message: str,
    conversation_id: str | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """Send a conversation request and wait for response.

    Args:
        hass: Home Assistant instance
        entry: Config entry
        request_id: Unique request ID
        message: User message
        conversation_id: Optional conversation ID for context
        language: Optional language code

    Returns:
        Response data from nanobot

    Raises:
        TimeoutError: If no response within timeout
    """
    future: asyncio.Future[dict[str, Any]] = asyncio.Future()
    entry.runtime_data.pending_requests[request_id] = future

    try:
        # Fire request event for nanobot to receive
        hass.bus.async_fire(
            EVENT_CONVERSATION_REQUEST,
            {
                "request_id": request_id,
                "message": message,
                "conversation_id": conversation_id,
                "language": language,
            },
        )

        # Wait for response
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            return await future

    finally:
        entry.runtime_data.pending_requests.pop(request_id, None)
