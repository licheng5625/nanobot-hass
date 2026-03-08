"""Config flow for Nanobot integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import DEFAULT_NAME, DOMAIN


class NanobotConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Nanobot.

    This is a simple config flow since nanobot connects to HA (not the other way around).
    No connection details needed - nanobot will use HA's WebSocket API with a long-lived token.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Only allow one instance
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title=DEFAULT_NAME, data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "docs_url": "https://github.com/unitree/nanobot",
            },
        )
