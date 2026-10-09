"""UI configuration flow for the ASTV Intent Catalogue."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN


class AstvIntentCatalogueConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create the integration's single empty-data config entry."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the single ASTV Intent Catalogue entry."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="ASTV Intent Catalogue", data={})
        return self.async_show_form(step_id="user")
