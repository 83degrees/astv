"""Administration state, validation, and durable draft operations."""

from __future__ import annotations

import asyncio
import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Literal, Mapping

import yaml

from .catalogue import (
    ActiveRegistry,
    CatalogueProvider,
    CatalogueValidationError,
    build_administration_candidate,
    build_registry,
    detached_record,
    is_canonical_identifier,
    load_registry_bytes,
    registry_document,
    validate_administration_record,
)
from .const import (
    ADMIN_INTERFACE_ID,
    ADMIN_INTERFACE_VERSION,
    SCHEMA_ID,
    SCHEMA_VERSION,
    SERVICE_ACTIVATE_INTENT_CATALOGUE,
    SERVICE_CREATE_INTENT_RECORD,
    SERVICE_DELETE_INTENT_RECORD,
    SERVICE_DISCARD_INTENT_CATALOGUE_DRAFT,
    SERVICE_GET_ADMINISTRATION_CAPABILITIES,
    SERVICE_GET_ADMINISTRATION_STATUS,
    SERVICE_GET_INTENT_RECORD,
    SERVICE_LIST_INTENT_RECORDS,
    SERVICE_UPDATE_INTENT_RECORD,
    SERVICE_VALIDATE_INTENT_CATALOGUE,
    SERVICE_VALIDATE_INTENT_RECORD,
)

State = Literal["absent", "valid", "invalid", "unavailable"]


@dataclass(frozen=True, slots=True)
class StoredObservation:
    """One non-mutating observation of a persisted catalogue file."""

    state: State
    revision: str | None = None
    registry: ActiveRegistry | None = None


@dataclass(frozen=True, slots=True)
class ActivationPreparation:
    """A completely parsed, validated, immutable activation candidate."""

    registry: ActiveRegistry
    references: tuple[tuple[str, str], ...]


def _common() -> dict[str, Any]:
    return {
        "interface_id": ADMIN_INTERFACE_ID,
        "interface_version": ADMIN_INTERFACE_VERSION,
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
    }


def _success(**fields: Any) -> dict[str, Any]:
    return {"ok": True, **_common(), **fields}


def _failure(
    code: str,
    refinement: str,
    message: str,
    **fields: Any,
) -> dict[str, Any]:
    return {
        "ok": False,
        **_common(),
        **fields,
        "error": {
            "code": code,
            "refinement": refinement,
            "message": message,
        },
    }


def provider_unavailable() -> dict[str, Any]:
    """Return the stable outcome for an unavailable config-entry provider."""
    return _failure(
        "dependency_unavailable",
        "provider_state_unavailable",
        "The ASTV Intent Catalogue provider is unavailable.",
    )


def _byte_revision(raw: bytes) -> str:
    from hashlib import sha256

    return f"sha256-bytes:{sha256(raw).hexdigest()}"


def _observe(path: Path, *, absent_allowed: bool) -> StoredObservation:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return StoredObservation("absent" if absent_allowed else "unavailable")
    except OSError:
        return StoredObservation("unavailable")
    try:
        registry = load_registry_bytes(raw)
    except CatalogueValidationError:
        return StoredObservation("invalid", _byte_revision(raw))
    return StoredObservation("valid", registry.active_revision, registry)


def _atomic_write(path: Path, registry: ActiveRegistry) -> None:
    """Persist a complete draft using one same-directory atomic replacement."""
    text = yaml.safe_dump(
        registry_document(registry),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    )
    text = text.replace(
        f"schema_version: {SCHEMA_VERSION}\n",
        f'schema_version: "{SCHEMA_VERSION}"\n',
        1,
    )
    serialized = text.encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def _encode_cursor(revision: str, last_id: str) -> str:
    raw = json.dumps(
        {"revision": revision, "last_id": last_id},
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_cursor(cursor: Any) -> tuple[str, str]:
    if not isinstance(cursor, str) or not cursor:
        raise ValueError("cursor must be a non-empty string")
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        value = json.loads(base64.b64decode(padded, altchars=b"-_", validate=True))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as err:
        raise ValueError("cursor is invalid") from err
    if (
        not isinstance(value, dict)
        or set(value) != {"revision", "last_id"}
        or not isinstance(value["revision"], str)
        or not isinstance(value["last_id"], str)
    ):
        raise ValueError("cursor is invalid")
    return value["revision"], value["last_id"]


class AdministrationManager:
    """Own normalized administration over one active provider and durable draft."""

    def __init__(
        self,
        provider: CatalogueProvider,
        catalogue_path: Path,
        draft_path: Path,
    ) -> None:
        self.provider = provider
        self.catalogue_path = catalogue_path
        self.draft_path = draft_path
        self.lock = asyncio.Lock()
        self._last_activation_error: dict[str, str] | None = None

    @staticmethod
    def capabilities() -> dict[str, Any]:
        """Describe only the operations callable in the current implementation."""
        return _success(
            mode="managed",
            mutation_supported=True,
            activation_applicable=True,
            authorization={
                "read": "home_assistant_service_call",
                "manage": "home_assistant_admin_service",
            },
            capabilities=[
                "discovery",
                "status",
                "active.list",
                "active.get",
                "validation.record",
                "validation.candidate",
                "draft.create",
                "draft.update",
                "draft.delete",
                "draft.discard",
                "concurrency.expected_revision",
                "activation.explicit",
                "references.mediacat.activation_check",
            ],
            operations={
                "discovery": SERVICE_GET_ADMINISTRATION_CAPABILITIES,
                "status": SERVICE_GET_ADMINISTRATION_STATUS,
                "active_list": SERVICE_LIST_INTENT_RECORDS,
                "active_get": SERVICE_GET_INTENT_RECORD,
                "validate_record": SERVICE_VALIDATE_INTENT_RECORD,
                "validate_candidate": SERVICE_VALIDATE_INTENT_CATALOGUE,
                "create": SERVICE_CREATE_INTENT_RECORD,
                "update": SERVICE_UPDATE_INTENT_RECORD,
                "delete": SERVICE_DELETE_INTENT_RECORD,
                "discard": SERVICE_DISCARD_INTENT_CATALOGUE_DRAFT,
                "activate": SERVICE_ACTIVATE_INTENT_CATALOGUE,
            },
            limits={"list_default": 100, "list_maximum": 200},
        )

    def status(self) -> dict[str, Any]:
        persisted = _observe(self.catalogue_path, absent_allowed=False)
        draft = _observe(self.draft_path, absent_allowed=True)
        active = self.provider.active
        draft_registry = draft.registry
        editable_revision = (
            draft.revision if draft.state != "absent" else (
                active.active_revision if active is not None else None
            )
        )
        activation_required = bool(
            draft_registry is not None
            and active is not None
            and draft_registry.active_revision != active.active_revision
        )
        return _success(
            provider_state="available",
            active_state="available" if active is not None else "unavailable",
            persisted_state=persisted.state,
            draft_state=draft.state,
            active_revision=active.active_revision if active is not None else None,
            persisted_revision=persisted.revision,
            draft_revision=draft.revision,
            editable_revision=editable_revision,
            activation_required=activation_required,
            active_count=len(active.records) if active is not None else None,
            persisted_count=(
                len(persisted.registry.records) if persisted.registry is not None else None
            ),
            draft_count=(
                len(draft_registry.records) if draft_registry is not None else None
            ),
            last_activation_error=(
                dict(self._last_activation_error)
                if self._last_activation_error is not None
                else None
            ),
        )

    def list_records(self, limit: Any = 100, cursor: Any = None) -> dict[str, Any]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
            return _failure(
                "invalid_request",
                "invalid_limit",
                "limit must be an integer from 1 through 200.",
            )
        active = self.provider.active
        if active is None:
            return _failure(
                "dependency_unavailable",
                "active_state_unavailable",
                "No valid active catalogue is available.",
            )
        start = 0
        if cursor is not None:
            try:
                cursor_revision, last_id = _decode_cursor(cursor)
            except ValueError:
                return _failure(
                    "invalid_request", "invalid_cursor", "The cursor is invalid."
                )
            if cursor_revision != active.active_revision:
                return _failure(
                    "stale_revision",
                    "stale_cursor",
                    "The active catalogue changed; restart pagination.",
                    active_revision=active.active_revision,
                )
            ordered_ids = sorted(active.records)
            try:
                start = ordered_ids.index(last_id) + 1
            except ValueError:
                return _failure(
                    "invalid_request", "invalid_cursor", "The cursor is invalid."
                )
        else:
            ordered_ids = sorted(active.records)
        selected = ordered_ids[start : start + limit]
        next_cursor = (
            _encode_cursor(active.active_revision, selected[-1])
            if selected and start + len(selected) < len(ordered_ids)
            else None
        )
        return _success(
            active_revision=active.active_revision,
            count=len(selected),
            total_count=len(ordered_ids),
            records=[
                {"intent_id": intent_id, "record": detached_record(active.records[intent_id])}
                for intent_id in selected
            ],
            next_cursor=next_cursor,
        )

    def get_record(self, intent_id: Any) -> dict[str, Any]:
        if intent_id is None or isinstance(intent_id, (Mapping, list, tuple, set)):
            return _failure(
                "invalid_request", "invalid_intent_id", "intent_id must be a scalar."
            )
        normalized = str(intent_id).strip().lower()
        if not normalized:
            return _failure(
                "invalid_request",
                "invalid_intent_id",
                "intent_id must not be blank.",
            )
        active = self.provider.active
        if active is None:
            return _failure(
                "dependency_unavailable",
                "active_state_unavailable",
                "No valid active catalogue is available.",
            )
        record = active.records.get(normalized)
        if record is None:
            return _failure(
                "not_found",
                "intent_not_found",
                "The requested intent record does not exist.",
                normalized_intent_id=normalized,
                active_revision=active.active_revision,
            )
        return _success(
            normalized_intent_id=normalized,
            active_revision=active.active_revision,
            record=detached_record(record),
        )

    @staticmethod
    def validate_record(intent_id: Any, record: Any) -> dict[str, Any]:
        try:
            validate_administration_record(intent_id, record)
        except CatalogueValidationError as err:
            return _failure(
                "invalid_request",
                "invalid_record",
                "The intent record is invalid.",
                valid=False,
                errors=[
                    {
                        "path": (
                            f"records.{intent_id}"
                            if isinstance(intent_id, str)
                            else "records"
                        ),
                        "code": "schema_validation_failed",
                        "message": str(err),
                    }
                ],
            )
        return _success(valid=True, intent_id=intent_id, errors=[])

    @staticmethod
    def validate_candidate(candidate: Any) -> dict[str, Any]:
        try:
            registry = build_administration_candidate(candidate)
        except CatalogueValidationError as err:
            return _failure(
                "invalid_request",
                "invalid_candidate",
                "The catalogue candidate is invalid.",
                valid=False,
                errors=[
                    {
                        "path": "candidate",
                        "code": "schema_validation_failed",
                        "message": str(err),
                    }
                ],
            )
        return _success(
            valid=True,
            record_count=len(registry.records),
            candidate_revision=registry.active_revision,
            errors=[],
        )

    def mutate(
        self,
        operation: Literal["create", "update", "delete"],
        expected_revision: Any,
        intent_id: Any,
        record: Any = None,
    ) -> dict[str, Any]:
        active = self.provider.active
        draft = _observe(self.draft_path, absent_allowed=True)
        if draft.state in {"invalid", "unavailable"}:
            return _failure(
                "dependency_unavailable",
                "persistence_unavailable",
                "The durable draft is unavailable or invalid; discard or recover it first.",
                active_revision=active.active_revision if active is not None else None,
                draft_revision=draft.revision,
            )
        if active is None:
            return _failure(
                "dependency_unavailable",
                "active_state_unavailable",
                "No valid active catalogue is available.",
            )
        base = draft.registry or active
        editable_revision = base.active_revision
        if expected_revision != editable_revision:
            return _failure(
                "stale_revision",
                "stale_edit_revision",
                "The candidate changed; refresh status before retrying.",
                active_revision=active.active_revision,
                draft_revision=draft.revision,
                editable_revision=editable_revision,
            )
        if not is_canonical_identifier(intent_id):
            return _failure(
                "invalid_request",
                "invalid_candidate",
                "intent_id must be a canonical schema-v1 identifier.",
            )
        records = registry_document(base)["records"]
        exists = intent_id in records
        if operation == "create" and exists:
            return _failure(
                "invalid_request",
                "already_exists",
                "The intent record already exists.",
            )
        if operation in {"update", "delete"} and not exists:
            return _failure(
                "not_found",
                "intent_not_found",
                "The requested intent record does not exist.",
            )
        if operation == "delete":
            del records[intent_id]
        else:
            records[intent_id] = record
        try:
            replacement = build_registry(
                {
                    "schema": SCHEMA_ID,
                    "schema_version": SCHEMA_VERSION,
                    "records": records,
                }
            )
        except CatalogueValidationError as err:
            return _failure(
                "invalid_request",
                "invalid_candidate",
                "The resulting catalogue candidate is invalid.",
                errors=[
                    {
                        "path": f"records.{intent_id}",
                        "code": "schema_validation_failed",
                        "message": str(err),
                    }
                ],
            )
        try:
            _atomic_write(self.draft_path, replacement)
        except OSError:
            return _failure(
                "dependency_unavailable",
                "persistence_unavailable",
                "The draft could not be persisted atomically.",
                active_revision=active.active_revision,
                draft_revision=draft.revision,
                editable_revision=editable_revision,
            )
        return _success(
            operation=operation,
            intent_id=intent_id,
            prior_revision=editable_revision,
            draft_revision=replacement.active_revision,
            draft_count=len(replacement.records),
            active_revision=active.active_revision,
            activation_required=replacement.active_revision != active.active_revision,
        )

    def discard(self, expected_revision: Any) -> dict[str, Any]:
        active = self.provider.active
        draft = _observe(self.draft_path, absent_allowed=True)
        if draft.state == "absent":
            return _failure(
                "not_found",
                "draft_not_found",
                "No durable draft exists.",
                active_revision=active.active_revision if active is not None else None,
            )
        if draft.state == "unavailable" or draft.revision is None:
            return _failure(
                "dependency_unavailable",
                "persistence_unavailable",
                "The durable draft cannot be inspected.",
                active_revision=active.active_revision if active is not None else None,
            )
        if expected_revision != draft.revision:
            return _failure(
                "stale_revision",
                "stale_draft_revision",
                "The draft changed; refresh status before retrying.",
                active_revision=active.active_revision if active is not None else None,
                draft_revision=draft.revision,
                editable_revision=draft.revision,
            )
        try:
            self.draft_path.unlink()
        except FileNotFoundError:
            return _failure(
                "stale_revision",
                "stale_draft_revision",
                "The draft changed; refresh status before retrying.",
                active_revision=active.active_revision if active is not None else None,
                draft_revision=None,
                editable_revision=(
                    active.active_revision if active is not None else None
                ),
            )
        except OSError:
            return _failure(
                "dependency_unavailable",
                "persistence_unavailable",
                "The durable draft could not be discarded.",
                active_revision=active.active_revision if active is not None else None,
                draft_revision=draft.revision,
            )
        self._last_activation_error = None
        return _success(
            operation="discard",
            prior_revision=draft.revision,
            draft_revision=None,
            editable_revision=active.active_revision if active is not None else None,
            active_revision=active.active_revision if active is not None else None,
            activation_required=False,
        )

    def prepare_activation(
        self, expected_revision: Any
    ) -> tuple[ActivationPreparation | None, dict[str, Any] | None]:
        """Re-read and fully validate the exact guarded durable draft."""
        active = self.provider.active
        draft = _observe(self.draft_path, absent_allowed=True)
        if draft.state == "absent":
            return None, _failure(
                "not_found",
                "draft_not_found",
                "No durable draft exists.",
                active_revision=active.active_revision if active is not None else None,
            )
        if draft.state == "unavailable" or draft.revision is None:
            return None, self.activation_failure(
                "dependency_unavailable",
                "persistence_unavailable",
                "The durable draft cannot be inspected.",
                draft_revision=draft.revision,
            )
        if expected_revision != draft.revision:
            return None, _failure(
                "stale_revision",
                "stale_draft_revision",
                "The draft changed; refresh status before retrying.",
                active_revision=active.active_revision if active is not None else None,
                draft_revision=draft.revision,
                editable_revision=draft.revision,
            )
        if active is None:
            return None, self.activation_failure(
                "dependency_unavailable",
                "active_state_unavailable",
                "No valid active catalogue is available.",
                draft_revision=draft.revision,
            )
        if draft.state == "invalid" or draft.registry is None:
            return None, self.activation_failure(
                "activation_failed",
                "candidate_invalid",
                "The durable draft is not a valid schema-v1 catalogue.",
                draft_revision=draft.revision,
            )
        references = tuple(
            sorted(
                {
                    (record["params"]["catalogue_id"], record["params"]["item_id"])
                    for record in draft.registry.records.values()
                    if record["intent"] == "media.play_source"
                }
            )
        )
        return ActivationPreparation(draft.registry, references), None

    def activation_failure(
        self,
        code: str,
        refinement: str,
        message: str,
        *,
        draft_revision: str | None = None,
        errors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Record and return one expected pre-commit activation failure."""
        active = self.provider.active
        persisted = _observe(self.catalogue_path, absent_allowed=False)
        draft = _observe(self.draft_path, absent_allowed=True)
        observed_draft_revision = (
            draft_revision if draft_revision is not None else draft.revision
        )
        self._last_activation_error = {
            "code": code,
            "refinement": refinement,
            "message": message,
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        fields: dict[str, Any] = {
            "active_revision": active.active_revision if active is not None else None,
            "persisted_revision": persisted.revision,
            "draft_revision": observed_draft_revision,
            "activation_required": bool(
                draft.registry is not None
                and active is not None
                and draft.registry.active_revision != active.active_revision
            ),
        }
        if errors is not None:
            fields["errors"] = errors
        return _failure(code, refinement, message, **fields)

    def commit_activation(
        self, expected_revision: str, preparation: ActivationPreparation
    ) -> dict[str, Any] | None:
        """Perform the single persisted-state commit point by consuming the draft."""
        current = _observe(self.draft_path, absent_allowed=True)
        if current.revision != expected_revision:
            return _failure(
                "stale_revision",
                "stale_draft_revision",
                "The draft changed; refresh status before retrying.",
                active_revision=(
                    self.provider.active.active_revision
                    if self.provider.active is not None
                    else None
                ),
                draft_revision=current.revision,
                editable_revision=current.revision,
            )
        if (
            current.state != "valid"
            or current.registry is None
            or current.registry.active_revision != preparation.registry.active_revision
        ):
            return self.activation_failure(
                "activation_failed",
                "candidate_invalid",
                "The durable draft changed or became invalid before activation.",
                draft_revision=current.revision,
            )
        try:
            os.replace(self.draft_path, self.catalogue_path)
        except OSError:
            return self.activation_failure(
                "activation_failed",
                "persisted_replace_failed",
                "The persisted catalogue could not be replaced atomically.",
                draft_revision=current.revision,
            )
        return None

    def publish_activation(
        self, preparation: ActivationPreparation
    ) -> dict[str, Any]:
        """Publish the prepared immutable registry without further awaiting or I/O."""
        replacement = preparation.registry
        self.provider.publish(replacement)
        self._last_activation_error = None
        return _success(
            operation="activate",
            active_revision=replacement.active_revision,
            persisted_revision=replacement.active_revision,
            draft_revision=None,
            active_count=len(replacement.records),
            activation_required=False,
        )
