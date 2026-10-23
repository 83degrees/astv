"""Verify the original staging fixture is active after lifecycle restart."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import aiohttp

from prepare_stage import service


async def verify() -> None:
    token = json.loads(Path("/config/staging/browser-session.json").read_text())["admin_access_token"]
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("ws://127.0.0.1:8123/api/websocket") as socket:
            await socket.receive_json()
            await socket.send_json({"type": "auth", "access_token": token})
            assert (await socket.receive_json())["type"] == "auth_ok"
            status = await service(socket, 1, "astv_intent_catalogue", "get_administration_status")
            records = await service(socket, 2, "astv_intent_catalogue", "list_intent_records", {"limit": 200})
    ids = [record["intent_id"] for record in records["records"]]
    assert status["ok"] is True and status["draft_state"] == "absent"
    assert ids == ["astv353_missing_media", "astv353_referenced", "astv353_validation"]
    evidence_path = Path("/config/staging/lifecycle-evidence.json")
    evidence = json.loads(evidence_path.read_text())
    evidence["post_restart"] = {"active_fixture_restored": True, "status": status, "intent_ids": ids}
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    asyncio.run(verify())
