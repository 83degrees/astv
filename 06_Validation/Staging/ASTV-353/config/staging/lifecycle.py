"""Fail-closed synthetic ASTV lifecycle for a separately authorised G2 run."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import aiohttp

from prepare_stage import command, service

CATALOGUE = Path("/config/astv/astv_intent_catalogue.yaml")
DRAFT = Path("/config/astv/astv_intent_catalogue.draft.yaml")
SESSION = Path("/config/staging/private-artifact-secrets.json")


async def run() -> None:
    baseline = CATALOGUE.read_bytes()
    token = json.loads(SESSION.read_text())["admin_access_token"]
    events: list[dict] = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect("ws://127.0.0.1:8123/api/websocket") as socket:
                await socket.receive_json()
                await socket.send_json({"type": "auth", "access_token": token})
                assert (await socket.receive_json())["type"] == "auth_ok"
                status = await service(socket, 1, "astv_intent_catalogue", "get_administration_status")
                baseline_revision = status["active_revision"]
                created = await service(socket, 2, "astv_intent_catalogue", "create_intent_record", {
                    "expected_revision": status["editable_revision"],
                    "intent_id": "astv353_created",
                    "record": {"intent": "routine.run", "title": "ASTV 353 created", "routine": "astv_353_inert_created", "params": {}},
                })
                assert created["ok"] is True
                staged = await service(socket, 3, "astv_intent_catalogue", "get_administration_status")
                assert staged["active_revision"] == baseline_revision and staged["activation_required"] is True
                events.append({"operation": "create_save", "active_unchanged": True, "result": created})

                stale = await service(socket, 4, "astv_intent_catalogue", "update_intent_record", {
                    "expected_revision": baseline_revision,
                    "intent_id": "astv353_created",
                    "record": {"intent": "routine.run", "title": "Must not apply", "routine": "astv_353_inert_created", "params": {}},
                })
                assert stale["ok"] is False and stale["error"]["code"] == "stale_revision"
                events.append({"operation": "stale_revision", "result": stale})

                invalid = await service(socket, 5, "astv_intent_catalogue", "validate_intent_record", {
                    "intent_id": "INVALID-ID", "record": {"intent": "routine.run", "title": "", "routine": "", "params": {}}
                })
                assert invalid["ok"] is False
                events.append({"operation": "validation_error", "result": invalid})

                failed_activation = await service(socket, 6, "astv_intent_catalogue", "activate_intent_catalogue", {
                    "expected_revision": staged["editable_revision"]
                })
                assert failed_activation["ok"] is False
                assert failed_activation["error"]["code"] == "activation_failed"
                assert failed_activation["error"]["refinement"] == "referenced_target_not_found"
                after_failure = await service(socket, 7, "astv_intent_catalogue", "get_administration_status")
                assert after_failure["active_revision"] == baseline_revision and after_failure["draft_state"] == "valid"
                events.append({"operation": "mediacat_activation_error", "active_unchanged": True, "result": failed_activation})

                fixed = await service(socket, 8, "astv_intent_catalogue", "update_intent_record", {
                    "expected_revision": after_failure["editable_revision"],
                    "intent_id": "astv353_missing_media",
                    "record": {"intent": "media.play_source", "title": "ASTV 353 fixed MediaCat target", "params": {"output": {"domain": "audio"}, "catalogue_id": "astv_353_stage", "item_id": "validation_media"}},
                })
                assert fixed["ok"] is True
                activated = await service(socket, 9, "astv_intent_catalogue", "activate_intent_catalogue", {"expected_revision": fixed["draft_revision"]})
                assert activated["ok"] is True
                events.append({"operation": "explicit_activate", "result": activated})

                updated = await service(socket, 10, "astv_intent_catalogue", "update_intent_record", {
                    "expected_revision": activated["active_revision"],
                    "intent_id": "astv353_created",
                    "record": {"intent": "routine.run", "title": "ASTV 353 edited", "routine": "astv_353_inert_edited", "params": {}},
                })
                assert updated["ok"] is True
                deleted = await service(socket, 11, "astv_intent_catalogue", "delete_intent_record", {
                    "expected_revision": updated["draft_revision"], "intent_id": "astv353_created"
                })
                assert deleted["ok"] is True
                events.extend([{"operation": "edit_save", "result": updated}, {"operation": "delete_save", "result": deleted}])
    finally:
        CATALOGUE.write_bytes(baseline)
        DRAFT.unlink(missing_ok=True)

    Path("/config/staging/lifecycle-evidence.json").write_text(
        json.dumps({"outcome": "pass", "events": events, "baseline_bytes_restored": CATALOGUE.read_bytes() == baseline}, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    asyncio.run(run())
