"""Strict catalogue loading and immutable active-registry support."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml
from yaml.constructor import ConstructorError
from yaml.tokens import AliasToken, AnchorToken, DirectiveToken, TagToken

from .const import INTERFACE_ID, INTERFACE_VERSION, SCHEMA_ID, SCHEMA_VERSION

_CANONICAL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_REFERENCE_CHARS = _CANONICAL_CHARS | {"-"}


class CatalogueValidationError(ValueError):
    """The complete persisted catalogue candidate is invalid."""


class RegistryUnavailable(RuntimeError):
    """No immutable active registry is available."""


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects every duplicate mapping key."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    for key_node, value_node in node.value:
        if isinstance(key_node, yaml.ScalarNode) and key_node.value == "<<":
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "YAML merge keys are not supported",
                key_node.start_mark,
            )
        if (
            isinstance(key_node, yaml.ScalarNode)
            and key_node.value == "schema_version"
            and isinstance(value_node, yaml.ScalarNode)
            and value_node.style not in {"'", '"'}
        ):
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "schema_version must be a quoted YAML string",
                value_node.start_mark,
            )
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as err:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from err
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def _parse_yaml(raw: bytes) -> Any:
    """Parse exactly one UTF-8 YAML document using the schema-v1 subset."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as err:
        raise CatalogueValidationError("catalogue must be valid UTF-8") from err

    if not text.strip():
        raise CatalogueValidationError("catalogue document must not be empty")

    try:
        for token in yaml.scan(text, Loader=_UniqueKeyLoader):
            if isinstance(token, (AliasToken, AnchorToken, DirectiveToken, TagToken)):
                raise CatalogueValidationError(
                    "YAML directives, tags, anchors, and aliases are not supported"
                )
        documents = list(yaml.load_all(text, Loader=_UniqueKeyLoader))
    except CatalogueValidationError:
        raise
    except yaml.YAMLError as err:
        raise CatalogueValidationError(f"invalid catalogue YAML: {err}") from err

    if len(documents) != 1 or documents[0] is None:
        raise CatalogueValidationError(
            "catalogue must contain exactly one non-empty YAML document"
        )
    return documents[0]


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


def _require_mapping(value: Any, subject: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CatalogueValidationError(f"{subject} must be a mapping")
    if not all(isinstance(key, str) for key in value):
        raise CatalogueValidationError(f"{subject} keys must be strings")
    return value


def _require_exact_keys(
    value: Mapping[str, Any],
    required: set[str],
    *,
    optional: set[str] | None = None,
    subject: str,
) -> None:
    optional = optional or set()
    keys = set(value)
    if not required <= keys or not keys <= required | optional:
        raise CatalogueValidationError(
            f"{subject} requires {sorted(required)}, permits {sorted(optional)}, "
            f"and received {sorted(keys)}"
        )


def _is_identifier(value: Any, *, allow_hyphen: bool = False) -> bool:
    if not isinstance(value, str) or not value or value != value.strip().lower():
        return False
    allowed = _REFERENCE_CHARS if allow_hyphen else _CANONICAL_CHARS
    return value[0].isalnum() and value[0].isascii() and all(
        character in allowed for character in value
    )


def _validate_record(record_value: Any, record_id: str) -> Mapping[str, Any]:
    record = _require_mapping(record_value, f"record {record_id!r}")
    intent = record.get("intent")
    common = {"intent", "title", "params"}
    optional = {"area_override"}

    if intent == "media.play_source":
        _require_exact_keys(record, common, optional=optional, subject=record_id)
        params = _require_mapping(record["params"], f"{record_id}.params")
        _require_exact_keys(
            params,
            {"output", "catalogue_id", "item_id"},
            subject=f"{record_id}.params",
        )
        output = _require_mapping(params["output"], f"{record_id}.params.output")
        _require_exact_keys(
            output, {"domain"}, subject=f"{record_id}.params.output"
        )
        if not _is_identifier(output["domain"]):
            raise CatalogueValidationError(f"{record_id} has invalid output domain")
        if not _is_identifier(params["catalogue_id"], allow_hyphen=True):
            raise CatalogueValidationError(f"{record_id} has invalid catalogue_id")
        if not _is_identifier(params["item_id"], allow_hyphen=True):
            raise CatalogueValidationError(f"{record_id} has invalid item_id")
    elif intent == "routine.run":
        _require_exact_keys(
            record, common | {"routine"}, optional=optional, subject=record_id
        )
        if not _is_identifier(record["routine"]):
            raise CatalogueValidationError(f"{record_id} has invalid routine")
        if not isinstance(record["params"], Mapping) or record["params"]:
            raise CatalogueValidationError(f"{record_id} params must be empty")
    else:
        raise CatalogueValidationError(f"{record_id} has unsupported intent")

    title = record["title"]
    if not isinstance(title, str) or not title.strip():
        raise CatalogueValidationError(f"{record_id} title must be non-blank")
    if "area_override" in record and not _is_identifier(record["area_override"]):
        raise CatalogueValidationError(f"{record_id} has invalid area_override")
    return record


@dataclass(frozen=True, slots=True)
class ActiveRegistry:
    """One complete deeply immutable runtime catalogue snapshot."""

    schema_id: str
    schema_version: str
    active_revision: str
    records: Mapping[str, Mapping[str, Any]]

    def lookup(self, intent_id: str | int | float | bool) -> dict[str, Any]:
        """Return a detached contract response for one normalized ID."""
        if intent_id is None or isinstance(intent_id, (Mapping, list, tuple, set)):
            raise TypeError("intent_id must be a non-null scalar")
        normalized = str(intent_id).strip().lower()
        stored = self.records.get(normalized)
        return {
            "ok": True,
            "interface_id": INTERFACE_ID,
            "interface_version": INTERFACE_VERSION,
            "schema_id": self.schema_id,
            "schema_version": self.schema_version,
            "active_revision": self.active_revision,
            "normalized_intent_id": normalized,
            "found": stored is not None,
            "record": _detach(stored) if stored is not None else {},
        }


def build_registry(candidate: Any, revision: str) -> ActiveRegistry:
    """Validate and deeply freeze a complete candidate without publishing it."""
    root = _require_mapping(candidate, "catalogue root")
    _require_exact_keys(
        root, {"schema", "schema_version", "records"}, subject="catalogue root"
    )
    if root["schema"] != SCHEMA_ID:
        raise CatalogueValidationError("unsupported schema")
    if root["schema_version"] != SCHEMA_VERSION:
        raise CatalogueValidationError("unsupported schema version")
    if not isinstance(revision, str) or not revision:
        raise CatalogueValidationError("revision must be opaque and non-empty")

    records = _require_mapping(root["records"], "records")
    if not records:
        raise CatalogueValidationError("records must not be empty")

    validated: dict[str, Mapping[str, Any]] = {}
    for raw_id, record_value in records.items():
        if not _is_identifier(raw_id):
            raise CatalogueValidationError("record ID is not canonical")
        normalized = raw_id.strip().lower()
        if normalized in validated:
            raise CatalogueValidationError("duplicate normalized record ID")
        validated[normalized] = _validate_record(record_value, raw_id)

    return ActiveRegistry(
        schema_id=SCHEMA_ID,
        schema_version=SCHEMA_VERSION,
        active_revision=revision,
        records=_freeze(validated),
    )


def load_registry(path: Path) -> ActiveRegistry:
    """Read, identify, parse, validate, and freeze one persisted candidate."""
    raw = path.read_bytes()
    revision = f"sha256:{sha256(raw).hexdigest()}"
    return build_registry(_parse_yaml(raw), revision)


class CatalogueProvider:
    """Own the single atomically replaceable active registry reference."""

    def __init__(self) -> None:
        self._active: ActiveRegistry | None = None

    @property
    def active(self) -> ActiveRegistry | None:
        return self._active

    def publish(self, replacement: ActiveRegistry) -> None:
        """Publish a fully prepared replacement with one reference assignment."""
        self._active = replacement

    def clear(self) -> None:
        """Release the active registry when the config entry unloads."""
        self._active = None

    def lookup(self, intent_id: str | int | float | bool) -> dict[str, Any]:
        active = self._active
        if active is None:
            raise RegistryUnavailable("no valid active catalogue")
        return active.lookup(intent_id)
