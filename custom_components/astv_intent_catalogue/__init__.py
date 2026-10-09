"""ASTV Intent Catalogue integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ConfigEntryError, ServiceValidationError
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.typing import ConfigType

from .administration import AdministrationManager, provider_unavailable
from .catalogue import (
    CatalogueProvider,
    CatalogueValidationError,
    RegistryUnavailable,
    load_registry,
)
from .const import (
    CATALOGUE_PATH,
    DOMAIN,
    DRAFT_PATH,
    SERVICE_CREATE_INTENT_RECORD,
    SERVICE_DELETE_INTENT_RECORD,
    SERVICE_DISCARD_INTENT_CATALOGUE_DRAFT,
    SERVICE_GET_ADMINISTRATION_CAPABILITIES,
    SERVICE_GET_ADMINISTRATION_STATUS,
    SERVICE_GET_INTENT_RECORD,
    SERVICE_LIST_INTENT_RECORDS,
    SERVICE_LOOKUP,
    SERVICE_UPDATE_INTENT_RECORD,
    SERVICE_VALIDATE_INTENT_CATALOGUE,
    SERVICE_VALIDATE_INTENT_RECORD,
)


def _lookup_value(value: Any) -> str | int | float | bool:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        raise vol.Invalid("intent_id must be a non-null scalar")
    if not isinstance(value, (str, int, float, bool)):
        raise vol.Invalid("intent_id must be a scalar")
    return value


LOOKUP_SCHEMA = vol.Schema({vol.Required("intent_id"): _lookup_value})
EMPTY_SCHEMA = vol.Schema({})
LIST_SCHEMA = vol.Schema(
    {
        vol.Optional("limit", default=100): object,
        vol.Optional("cursor", default=None): object,
    }
)
GET_SCHEMA = vol.Schema({vol.Required("intent_id"): _lookup_value})
VALIDATE_RECORD_SCHEMA = vol.Schema(
    {
        vol.Required("intent_id"): str,
        vol.Required("record"): dict,
    }
)
VALIDATE_CANDIDATE_SCHEMA = vol.Schema({vol.Required("candidate"): dict})
MUTATE_RECORD_SCHEMA = vol.Schema(
    {
        vol.Required("expected_revision"): str,
        vol.Required("intent_id"): str,
        vol.Required("record"): dict,
    }
)
DELETE_RECORD_SCHEMA = vol.Schema(
    {
        vol.Required("expected_revision"): str,
        vol.Required("intent_id"): str,
    }
)
DISCARD_SCHEMA = vol.Schema({vol.Required("expected_revision"): str})


async def async_refresh(
    hass: HomeAssistant, provider: CatalogueProvider
) -> None:
    """Prepare a complete replacement off-loop, then publish it on-loop."""
    replacement = await hass.async_add_executor_job(load_registry, CATALOGUE_PATH)
    provider.publish(replacement)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register runtime and administration actions independently of entry state."""
    hass.data.setdefault(DOMAIN, {})

    def loaded_administration() -> AdministrationManager | None:
        entries = hass.config_entries.async_entries(DOMAIN)
        if len(entries) != 1 or entries[0].state is not ConfigEntryState.LOADED:
            return None
        provider = hass.data[DOMAIN].get(entries[0].entry_id)
        if not isinstance(provider, CatalogueProvider):
            return None
        manager = provider.administration
        return manager if isinstance(manager, AdministrationManager) else None

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

    async def async_capabilities(call: ServiceCall) -> ServiceResponse:
        return AdministrationManager.capabilities()

    async def async_status(call: ServiceCall) -> ServiceResponse:
        manager = loaded_administration()
        if manager is None:
            return provider_unavailable()
        return await hass.async_add_executor_job(manager.status)

    async def async_list(call: ServiceCall) -> ServiceResponse:
        manager = loaded_administration()
        if manager is None:
            return provider_unavailable()
        return manager.list_records(call.data.get("limit", 100), call.data.get("cursor"))

    async def async_get(call: ServiceCall) -> ServiceResponse:
        manager = loaded_administration()
        if manager is None:
            return provider_unavailable()
        return manager.get_record(call.data["intent_id"])

    async def async_validate_record(call: ServiceCall) -> ServiceResponse:
        manager = loaded_administration()
        if manager is None:
            return provider_unavailable()
        return manager.validate_record(call.data["intent_id"], call.data["record"])

    async def async_validate_candidate(call: ServiceCall) -> ServiceResponse:
        manager = loaded_administration()
        if manager is None:
            return provider_unavailable()
        return manager.validate_candidate(call.data["candidate"])

    async def async_mutate(
        call: ServiceCall, operation: str
    ) -> ServiceResponse:
        manager = loaded_administration()
        if manager is None:
            return provider_unavailable()
        async with manager.lock:
            return await hass.async_add_executor_job(
                manager.mutate,
                operation,
                call.data["expected_revision"],
                call.data["intent_id"],
                call.data.get("record"),
            )

    async def async_create(call: ServiceCall) -> ServiceResponse:
        return await async_mutate(call, "create")

    async def async_update(call: ServiceCall) -> ServiceResponse:
        return await async_mutate(call, "update")

    async def async_delete(call: ServiceCall) -> ServiceResponse:
        return await async_mutate(call, "delete")

    async def async_discard(call: ServiceCall) -> ServiceResponse:
        manager = loaded_administration()
        if manager is None:
            return provider_unavailable()
        async with manager.lock:
            return await hass.async_add_executor_job(
                manager.discard, call.data["expected_revision"]
            )

    read_actions = (
        (SERVICE_GET_ADMINISTRATION_CAPABILITIES, async_capabilities, EMPTY_SCHEMA),
        (SERVICE_GET_ADMINISTRATION_STATUS, async_status, EMPTY_SCHEMA),
        (SERVICE_LIST_INTENT_RECORDS, async_list, LIST_SCHEMA),
        (SERVICE_GET_INTENT_RECORD, async_get, GET_SCHEMA),
    )
    for service, handler, schema in read_actions:
        hass.services.async_register(
            DOMAIN,
            service,
            handler,
            schema=schema,
            supports_response=SupportsResponse.ONLY,
        )

    manage_actions = (
        (SERVICE_VALIDATE_INTENT_RECORD, async_validate_record, VALIDATE_RECORD_SCHEMA),
        (
            SERVICE_VALIDATE_INTENT_CATALOGUE,
            async_validate_candidate,
            VALIDATE_CANDIDATE_SCHEMA,
        ),
        (SERVICE_CREATE_INTENT_RECORD, async_create, MUTATE_RECORD_SCHEMA),
        (SERVICE_UPDATE_INTENT_RECORD, async_update, MUTATE_RECORD_SCHEMA),
        (SERVICE_DELETE_INTENT_RECORD, async_delete, DELETE_RECORD_SCHEMA),
        (SERVICE_DISCARD_INTENT_CATALOGUE_DRAFT, async_discard, DISCARD_SCHEMA),
    )
    for service, handler, schema in manage_actions:
        async_register_admin_service(
            hass,
            DOMAIN,
            service,
            handler,
            schema=schema,
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
    provider.administration = AdministrationManager(
        provider, CATALOGUE_PATH, DRAFT_PATH
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = provider
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Release this entry's active registry while retaining the action."""
    provider = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if isinstance(provider, CatalogueProvider):
        provider.clear()
    return True
