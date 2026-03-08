"""Constants for the Nanobot integration."""

import logging

DOMAIN = "nanobot"
LOGGER = logging.getLogger(__package__)

# Events for communication with nanobot
EVENT_CONVERSATION_REQUEST = "nanobot_conversation_request"
EVENT_CONVERSATION_RESPONSE = "nanobot_conversation_response"

DEFAULT_TIMEOUT = 60  # Longer timeout for LLM processing
DEFAULT_NAME = "Nanobot"
