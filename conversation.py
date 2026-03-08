"""Conversation support for Nanobot."""

from __future__ import annotations

import uuid
from typing import Literal

from homeassistant.components import conversation
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, intent
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import NanobotConfigEntry, async_send_request
from .const import DOMAIN, LOGGER


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: NanobotConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up conversation entities."""
    async_add_entities([NanobotConversationEntity(config_entry)])


class NanobotConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """Nanobot conversation agent.

    This entity receives conversation requests from HA and forwards them
    to nanobot via events. Nanobot must be connected to HA's WebSocket API
    and subscribed to 'nanobot_conversation_request' events.
    """

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: NanobotConfigEntry) -> None:
        """Initialize the agent."""
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Nanobot",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Handle a conversation message.

        Fires an event for nanobot to receive, waits for response event.
        """
        request_id = str(uuid.uuid4())

        try:
            response_data = await async_send_request(
                self.hass,
                self.entry,
                request_id=request_id,
                message=user_input.text,
                conversation_id=user_input.conversation_id,
                language=user_input.language,
            )

            response_text = response_data.get("response", "")
            new_conversation_id = response_data.get(
                "conversation_id", user_input.conversation_id
            )

        except TimeoutError:
            LOGGER.error(
                "Nanobot did not respond in time. "
                "Make sure nanobot is connected and subscribed to events."
            )
            intent_response = intent.IntentResponse(language=user_input.language)
            intent_response.async_set_error(
                intent.IntentResponseErrorCode.UNKNOWN,
                "Nanobot is not responding. Please check the connection.",
            )
            return conversation.ConversationResult(
                response=intent_response,
                conversation_id=user_input.conversation_id,
            )

        # Add response to chat log
        chat_log.async_add_assistant_content(
            conversation.AssistantContent(
                agent_id=self.entity_id,
                content=response_text,
            )
        )

        intent_response = intent.IntentResponse(language=user_input.language)
        intent_response.async_set_speech(response_text)

        return conversation.ConversationResult(
            response=intent_response,
            conversation_id=new_conversation_id,
        )
