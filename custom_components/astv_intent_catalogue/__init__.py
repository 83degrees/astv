"""ASTV Intent Catalogue integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ConfigEntryError, ServiceValidationError
from homeassistant.helpers.typing import ConfigType

from .catalogue import (
    CatalogueProvider,
    CatalogueValidationError,
    RegistryUnavailable,
    load_registry,
)
from .const import CATALOGUE_PATH, DOMAIN, SERVICE_LOOKUP


def _lookup_value(value: Any) -> str | int | float | bool:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        raise vol.Invalid("intent_id must be a non-null scalar")
    if not isinstance(value, (str, int, float, bool)):
        raise vol.Invalid("intent_id must be a scalar")
    return value


LOOKUP_SCHEMA = vol.Schema({vol.Required("intent_id"): _lookup_value})


async def async_refresh(
    hass: HomeAssistant, provider: CatalogueProvider
) -> None:
    """Prepare a complete replacement off-loop, then publish it on-loop."""
    replacement = await hass.async_add_executor_job(load_registry, CATALOGUE_PATH)
    provider.publish(replacement)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the lookup action independently of config-entry state."""
    hass.data.setdefault(DOMAIN, {})

    async def async_lookup(call: ServiceCall) -> ServiceResponse:
        entries = hass.config_entries.async_entries(DOMAIN)
        if len(entries) != 1 or entries[0].state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                "The ASTV Intent Catalogue config entry is not loaded"
            )
        provider = hass.data[DOMAIN].get(entries[0].entry_id)
        if not isinstance(provider, CatalogueProvider) or provider.active is None:
            raise ServiceValidationError(
                "The ASTV Intent Catalogue active registry is unavailable"
            )
        try:
            return provider.lookup(call.data["intent_id"])
        except RegistryUnavailable as err:
            raise ServiceValidationError(str(err)) from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_LOOKUP,
        async_lookup,
        schema=LOOKUP_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Load and atomically publish the initial immutable registry."""
    provider = CatalogueProvider()
    try:
        await async_refresh(hass, provider)
    except (OSError, CatalogueValidationError) as err:
        raise ConfigEntryError(f"Unable to load ASTV Intent Catalogue: {err}") from err
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = provider
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Release this entry's active registry while retaining the action."""
    provider = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if isinstance(provider, CatalogueProvider):
        provider.clear()
    return True
