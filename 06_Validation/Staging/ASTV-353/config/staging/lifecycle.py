"""Run the synthetic ASTV lifecycle and restore fixture bytes on every outcome."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

import aiohttp

from prepare_stage import service

CATALOGUE = Path("/config/astv/astv_intent_catalogue.yaml")
DRAFT = Path("/config/astv/astv_intent_catalogue.draft.yaml")
SESSION = Path("/config/staging/private-artifact-secrets.json")
EVIDENCE = Path("/config/staging/lifecycle-evidence.json")


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_evidence(payload: dict[str, object]) -> None:
    EVIDENCE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


async def run() -> bool:
    baseline = CATALOGUE.read_bytes()
    baseline_state: dict[str, object] = {
        "catalogue_sha256": digest(baseline),
        "draft_absent": not DRAFT.exists(),
    }
    evidence: dict[str, object] = {
        "outcome": "started",
        "events": [],
        "baseline": baseline_state,
        "primary_failure": None,
        "pre_restart_restoration": "pending",
        "restoration": {"status": "not_run"},
    }
    events: list[dict[str, object]] = []
    evidence["events"] = events
    phase = "precondition"
    primary_failure: dict[str, str] | None = None
    restoration_errors: list[str] = []

    try:
        assert baseline_state["draft_absent"] is True
        token = json.loads(SESSION.read_text())["admin_access_token"]
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect("ws://127.0.0.1:8123/api/websocket") as socket:
                await socket.receive_json()
                await socket.send_json({"type": "auth", "access_token": token})
                assert (await socket.receive_json())["type"] == "auth_ok"

                phase = "baseline_status"
                status = await service(socket, 1, "astv_intent_catalogue", "get_administration_status")
                baseline_revision = status["active_revision"]
                baseline_state["active_revision"] = baseline_revision

                phase = "create_save"
                created = await service(socket, 2, "astv_intent_catalogue", "create_intent_record", {
                    "expected_revision": status["editable_revision"],
                    "intent_id": "astv353_created",
                    "record": {"intent": "routine.run", "title": "ASTV 353 created", "routine": "astv_353_inert_created", "params": {}},
                })
                assert created["ok"] is True
                staged = await service(socket, 3, "astv_intent_catalogue", "get_administration_status")
                assert staged["active_revision"] == baseline_revision and staged["activation_required"] is True
                events.append({"operation": phase, "active_unchanged": True, "result": created})

                phase = "stale_revision"
                stale = await service(socket, 4, "astv_intent_catalogue", "update_intent_record", {
                    "expected_revision": baseline_revision,
                    "intent_id": "astv353_created",
                    "record": {"intent": "routine.run", "title": "Must not apply", "routine": "astv_353_inert_created", "params": {}},
                })
                assert stale["ok"] is False and stale["error"]["code"] == "stale_revision"
                events.append({"operation": phase, "result": stale})

                phase = "validation_error"
                invalid = await service(socket, 5, "astv_intent_catalogue", "validate_intent_record", {
                    "intent_id": "INVALID-ID", "record": {"intent": "routine.run", "title": "", "routine": "", "params": {}}
                })
                assert invalid["ok"] is False
                events.append({"operation": phase, "result": invalid})

                phase = "mediacat_activation_error"
                failed_activation = await service(socket, 6, "astv_intent_catalogue", "activate_intent_catalogue", {
                    "expected_revision": staged["editable_revision"]
                })
                assert failed_activation["ok"] is False
                assert failed_activation["error"]["code"] == "activation_failed"
                assert failed_activation["error"]["refinement"] == "referenced_target_not_found"
                after_failure = await service(socket, 7, "astv_intent_catalogue", "get_administration_status")
                assert after_failure["active_revision"] == baseline_revision and after_failure["draft_state"] == "valid"
                events.append({"operation": phase, "active_unchanged": True, "result": failed_activation})

                phase = "explicit_activate"
                fixed = await service(socket, 8, "astv_intent_catalogue", "update_intent_record", {
                    "expected_revision": after_failure["editable_revision"],
                    "intent_id": "astv353_missing_media",
                    "record": {"intent": "media.play_source", "title": "ASTV 353 fixed MediaCat target", "params": {"output": {"domain": "audio"}, "catalogue_id": "astv_353_stage", "item_id": "validation_media"}},
                })
                assert fixed["ok"] is True
                activated = await service(socket, 9, "astv_intent_catalogue", "activate_intent_catalogue", {"expected_revision": fixed["draft_revision"]})
                assert activated["ok"] is True
                events.append({"operation": phase, "result": activated})

                phase = "edit_save"
                updated = await service(socket, 10, "astv_intent_catalogue", "update_intent_record", {
                    "expected_revision": activated["active_revision"],
                    "intent_id": "astv353_created",
                    "record": {"intent": "routine.run", "title": "ASTV 353 edited", "routine": "astv_353_inert_edited", "params": {}},
                })
                assert updated["ok"] is True
                events.append({"operation": phase, "result": updated})

                phase = "delete_save"
                deleted = await service(socket, 11, "astv_intent_catalogue", "delete_intent_record", {
                    "expected_revision": updated["draft_revision"], "intent_id": "astv353_created"
                })
                assert deleted["ok"] is True
                events.append({"operation": phase, "result": deleted})
    except Exception as error:  # Exception text can contain request or credential details.
        primary_failure = {"phase": phase, "type": type(error).__name__}
    finally:
        try:
            CATALOGUE.write_bytes(baseline)
        except OSError:
            restoration_errors.append("catalogue_write_failed")
        try:
            DRAFT.unlink(missing_ok=True)
        except OSError:
            restoration_errors.append("draft_removal_failed")
        try:
            bytes_restored = CATALOGUE.read_bytes() == baseline
        except OSError:
            bytes_restored = False
        draft_removed = not DRAFT.exists()
        if not bytes_restored:
            restoration_errors.append("catalogue_bytes_not_restored")
        if not draft_removed:
            restoration_errors.append("draft_not_removed")
        evidence["primary_failure"] = primary_failure
        evidence["baseline_bytes_restored"] = bytes_restored
        evidence["draft_removed"] = draft_removed
        evidence["pre_restart_restoration"] = "passed" if not restoration_errors else "failed"
        evidence["restoration_errors"] = restoration_errors
        evidence["outcome"] = "pass" if primary_failure is None and not restoration_errors else "failed"
        write_evidence(evidence)

    return evidence["outcome"] == "pass"


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(run()) else 1)
