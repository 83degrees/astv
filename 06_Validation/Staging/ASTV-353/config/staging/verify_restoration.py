"""Verify fixture and running ASTV state after the mandatory lifecycle restart."""

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
EXPECTED_IDS = ["astv353_missing_media", "astv353_referenced", "astv353_validation"]


def load_evidence() -> dict[str, object]:
    try:
        value = json.loads(EVIDENCE.read_text())
        if isinstance(value, dict):
            return value
    except (OSError, UnicodeError, json.JSONDecodeError):
        pass
    return {"outcome": "failed", "primary_failure": {"phase": "evidence", "type": "MissingOrInvalidEvidence"}}


def write_evidence(evidence: dict[str, object]) -> None:
    EVIDENCE.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")


async def runtime_state(token: str) -> tuple[dict, dict]:
    last_error: Exception | None = None
    for _attempt in range(30):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect("ws://127.0.0.1:8123/api/websocket") as socket:
                    await socket.receive_json()
                    await socket.send_json({"type": "auth", "access_token": token})
                    assert (await socket.receive_json())["type"] == "auth_ok"
                    status = await service(socket, 1, "astv_intent_catalogue", "get_administration_status")
                    records = await service(socket, 2, "astv_intent_catalogue", "list_intent_records", {"limit": 200})
                    return status, records
        except Exception as error:
            last_error = error
            await asyncio.sleep(2)
    raise RuntimeError("restored runtime did not become verifiable") from last_error


async def verify() -> bool:
    evidence = load_evidence()
    errors: list[str] = []
    status: dict = {}
    ids: list[str] = []
    catalogue_bytes_restored = False
    draft_removed = False
    active_revision_restored = False
    active_fixture_restored = False
    baseline = evidence.get("baseline")
    if not isinstance(baseline, dict):
        errors.append("baseline_evidence_missing")
        baseline = {}

    try:
        catalogue_hash = hashlib.sha256(CATALOGUE.read_bytes()).hexdigest()
        catalogue_bytes_restored = catalogue_hash == baseline.get("catalogue_sha256")
        if not catalogue_bytes_restored:
            errors.append("catalogue_hash_mismatch")
    except OSError:
        errors.append("catalogue_unreadable")
    try:
        DRAFT.stat()
        errors.append("draft_present")
    except FileNotFoundError:
        draft_removed = True
    except OSError:
        errors.append("draft_state_unreadable")

    try:
        token = json.loads(SESSION.read_text())["admin_access_token"]
        status, records = await runtime_state(token)
        ids = [record["intent_id"] for record in records["records"]]
        if status.get("ok") is not True:
            errors.append("administration_status_failed")
        if status.get("draft_state") != "absent":
            errors.append("runtime_draft_present")
        active_revision_restored = status.get("active_revision") == baseline.get("active_revision")
        if not active_revision_restored:
            errors.append("active_revision_mismatch")
        active_fixture_restored = ids == EXPECTED_IDS
        if not active_fixture_restored:
            errors.append("active_fixture_mismatch")
    except Exception as error:  # Record only type; exception text can contain request details.
        errors.append(f"runtime_verification_{type(error).__name__}")

    evidence["restoration"] = {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "catalogue_bytes_restored": catalogue_bytes_restored,
        "draft_removed": draft_removed and "runtime_draft_present" not in errors,
        "active_revision_restored": active_revision_restored,
        "active_fixture_restored": active_fixture_restored,
        "intent_ids": ids,
    }
    try:
        write_evidence(evidence)
    except OSError:
        return False
    return not errors


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(verify()) else 1)
