"""Isolated ASTV-331 proof of immutable registry semantics.

This is executable design evidence only. It is not imported by Home Assistant
and is not the ASTV-333 production implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

SCHEMA_ID = "astv.intent_catalogue"
SCHEMA_VERSION = "1.0.0"
INTERFACE_ID = "astv.intent_catalogue.lookup"
INTERFACE_VERSION = "1.0.0"


class CatalogueValidationError(ValueError):
    """The complete catalogue candidate is invalid."""


class RegistryUnavailable(RuntimeError):
    """No valid active registry is available."""


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _detach(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _detach(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_detach(item) for item in value]
    return value


def _require_exact_keys(
    value: Mapping[str, Any], required: set[str], optional: set[str] = set()
) -> None:
    keys = set(value)
    if not required <= keys or not keys <= required | optional:
        raise CatalogueValidationError(
            f"expected required keys {sorted(required)} and optional keys "
            f"{sorted(optional)}; got {sorted(keys)}"
        )


def _valid_id(value: Any, *, hyphen: bool = False) -> bool:
    if not isinstance(value, str) or not value:
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if hyphen:
        allowed.add("-")
    return (
        value == value.strip().lower()
        and value[0] in set("abcdefghijklmnopqrstuvwxyz0123456789")
        and all(character in allowed for character in value)
    )


def _validate_record(record: Any) -> None:
    if not isinstance(record, Mapping):
        raise CatalogueValidationError("record must be a mapping")

    intent = record.get("intent")
    common = {"intent", "title", "params"}
    optional = {"area_override"}

    if intent == "media.play_source":
        _require_exact_keys(record, common, optional)
        params = record["params"]
        if not isinstance(params, Mapping):
            raise CatalogueValidationError("media params must be a mapping")
        _require_exact_keys(params, {"output", "catalogue_id", "item_id"})
        output = params["output"]
        if not isinstance(output, Mapping):
            raise CatalogueValidationError("output must be a mapping")
        _require_exact_keys(output, {"domain"})
        if not _valid_id(output["domain"]):
            raise CatalogueValidationError("invalid output domain")
        if not _valid_id(params["catalogue_id"], hyphen=True):
            raise CatalogueValidationError("invalid catalogue_id")
        if not _valid_id(params["item_id"], hyphen=True):
            raise CatalogueValidationError("invalid item_id")
    elif intent == "routine.run":
        _require_exact_keys(record, common | {"routine"}, optional)
        if not _valid_id(record["routine"]):
            raise CatalogueValidationError("invalid routine")
        if record["params"] != {}:
            raise CatalogueValidationError("routine params must be empty")
    else:
        raise CatalogueValidationError("unsupported intent")

    title = record["title"]
    if not isinstance(title, str) or not title.strip():
        raise CatalogueValidationError("title must be a non-blank string")

    if "area_override" in record and not _valid_id(record["area_override"]):
        raise CatalogueValidationError("invalid area_override")


@dataclass(frozen=True)
class ActiveRegistry:
    schema_id: str
    schema_version: str
    active_revision: str
    records: Mapping[str, Mapping[str, Any]]


def build_registry(candidate: Any, revision: str) -> ActiveRegistry:
    """Validate and freeze one complete candidate without touching active state."""
    if not isinstance(candidate, Mapping):
        raise CatalogueValidationError("catalogue root must be a mapping")
    _require_exact_keys(candidate, {"schema", "schema_version", "records"})
    if candidate["schema"] != SCHEMA_ID:
        raise CatalogueValidationError("unsupported schema")
    if candidate["schema_version"] != SCHEMA_VERSION:
        raise CatalogueValidationError("unsupported schema version")
    if not isinstance(revision, str) or not revision:
        raise CatalogueValidationError("revision must be opaque and non-empty")

    records = candidate["records"]
    if not isinstance(records, Mapping) or not records:
        raise CatalogueValidationError("records must be a non-empty mapping")

    validated: dict[str, Mapping[str, Any]] = {}
    for raw_id, record in records.items():
        if not _valid_id(raw_id):
            raise CatalogueValidationError("record ID is not canonical")
        normalized = raw_id.strip().lower()
        if normalized in validated:
            raise CatalogueValidationError("duplicate normalized record ID")
        _validate_record(record)
        validated[normalized] = record

    return ActiveRegistry(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        active_revision=revision,
        records=_freeze(validated),
    )


class CatalogueProvider:
    """Single-reference transactional registry holder."""

    def __init__(self) -> None:
        self._active: ActiveRegistry | None = None

    @property
    def active_revision(self) -> str | None:
        return None if self._active is None else self._active.active_revision

    @property
    def active(self) -> ActiveRegistry | None:
        return self._active

    def activate(self, candidate: Any, persisted_revision: str) -> None:
        """Build completely, then perform the one active-reference swap."""
        replacement = build_registry(candidate, persisted_revision)
        self._active = replacement

    def lookup(self, intent_id: Any) -> dict[str, Any]:
        active = self._active
        if active is None:
            raise RegistryUnavailable("no valid active catalogue")
        if intent_id is None or isinstance(intent_id, (Mapping, list, tuple, set)):
            raise TypeError("intent_id must be a non-null scalar")

        normalized = str(intent_id).strip().lower()
        stored = active.records.get(normalized)
        found = stored is not None
        return {
            "ok": True,
            "interface_id": INTERFACE_ID,
            "interface_version": INTERFACE_VERSION,
            "schema_id": active.schema_id,
            "schema_version": active.schema_version,
            "active_revision": active.active_revision,
            "normalized_intent_id": normalized,
            "found": found,
            "record": _detach(stored) if found else {},
        }
