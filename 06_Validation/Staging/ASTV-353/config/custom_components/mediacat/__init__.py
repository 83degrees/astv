"""Deterministic, non-executing MediaCat resolver for ASTV-353 staging."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.typing import ConfigType

DOMAIN = "mediacat"
SERVICE = "resolve_media_record"
SCHEMA = vol.Schema(
    {
        vol.Required("catalogue_id"): str,
        vol.Required("item_id"): str,
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register a resolver that returns inert metadata and never dispatches."""

    async def resolve(call: ServiceCall) -> ServiceResponse:
        catalogue_id = call.data["catalogue_id"]
        item_id = call.data["item_id"]
        if (catalogue_id, item_id) == ("astv_353_stage", "deliberately_missing"):
            raise ServiceValidationError("Synthetic MediaCat target is absent")
        if catalogue_id != "astv_353_stage":
            raise ServiceValidationError("Catalogue is outside the staging fixture")
        return {
            "ok": True,
            "catalogue_id": catalogue_id,
            "item_id": item_id,
            "resolved": {"kind": "inert_stage_record", "executable": False},
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE,
        resolve,
        schema=SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    return True
