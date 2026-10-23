"""Bootstrap and inspect the private ASTV-353 Home Assistant stage."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

import aiohttp

BASE_URL = "http://127.0.0.1:8123"
CLIENT_ID = BASE_URL + "/"
ADMIN = ("astv353-admin", "ephemeral-ASTV353-admin")
READER = ("astv353-reader", "ephemeral-ASTV353-reader")
EXPECTED_INTENTS = [
    "astv353_missing_media",
    "astv353_referenced",
    "astv353_validation",
]


def post_json(path: str, payload: dict[str, object]) -> dict:
    request = urllib.request.Request(
        BASE_URL + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def create_owner_token() -> str:
    user = post_json(
        "/api/onboarding/users",
        {
            "client_id": CLIENT_ID,
            "name": "ASTV-353 staging administrator",
            "username": ADMIN[0],
            "password": ADMIN[1],
            "language": "en",
        },
    )
    payload = urllib.parse.urlencode(
        {"grant_type": "authorization_code", "code": user["auth_code"], "client_id": CLIENT_ID}
    ).encode()
    request = urllib.request.Request(BASE_URL + "/auth/token", data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)["access_token"]


async def command(socket, command_id: int, *, allow_error: bool = False, **payload):
    await socket.send_json({"id": command_id, **payload})
    response = await socket.receive_json(timeout=20)
    if not response.get("success") and not allow_error:
        raise RuntimeError(f"WebSocket command failed: {response}")
    return response


async def service(socket, command_id: int, domain: str, name: str, data=None, *, allow_error=False):
    response = await command(
        socket,
        command_id,
        allow_error=allow_error,
        type="call_service",
        domain=domain,
        service=name,
        service_data=data or {},
        return_response=True,
    )
    if not response.get("success"):
        return response
    return response["result"]["response"]


def digest(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


async def prepare(token: str) -> dict[str, object]:
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect("ws://127.0.0.1:8123/api/websocket") as socket:
            assert (await socket.receive_json())["type"] == "auth_required"
            await socket.send_json({"type": "auth", "access_token": token})
            auth = await socket.receive_json()
            assert auth["type"] == "auth_ok", auth

            flow = await command(
                socket,
                1,
                type="config_entries/flow/init",
                handler="astv_intent_catalogue",
                context={"source": "user"},
                show_advanced_options=False,
            )
            configured = await command(
                socket,
                2,
                type="config_entries/flow/configure",
                flow_id=flow["result"]["flow_id"],
                user_input={},
            )
            assert configured["result"]["type"] == "create_entry", configured

            reader = await command(
                socket,
                3,
                type="config/auth/create",
                name="ASTV-353 staging reader",
                group_ids=["system-users"],
                local_only=False,
            )
            reader_id = reader["result"]["user"]["id"]
            await command(
                socket,
                4,
                type="config/auth_provider/homeassistant/create",
                user_id=reader_id,
                username=READER[0],
                password=READER[1],
            )

            status = None
            for attempt in range(30):
                status = await service(socket, 10 + attempt, "astv_intent_catalogue", "get_administration_status")
                if status.get("ok"):
                    break
                await asyncio.sleep(1)
            assert status and status.get("ok") is True, status
            capabilities = await service(socket, 50, "astv_intent_catalogue", "get_administration_capabilities")
            records = await service(socket, 51, "astv_intent_catalogue", "list_intent_records", {"limit": 200})
            advnfc = await service(socket, 52, "advnfc", "query_tag_mappings", {"action_type": "astv_intent", "intent_id": "astv353_referenced"})
            config = (await command(socket, 53, type="get_config"))["result"]

    observed = [entry["intent_id"] for entry in records["records"]]
    assert observed == EXPECTED_INTENTS, observed
    assert capabilities["interface_id"] == "astv.intent_catalogue.administration"
    assert capabilities["interface_version"] == "1.1.0"
    assert advnfc["ok"] is True and [m["uid"] for m in advnfc["mappings"]] == ["A3530001"]

    evidence = {
        "observed_at": datetime.now(UTC).isoformat(),
        "home_assistant_version": auth["ha_version"],
        "health": {"state": config["state"], "version": config["version"]},
        "astv": {"capabilities": capabilities, "status": status, "intent_ids": observed},
        "advnfc": {"reverse_query": advnfc},
        "fixtures": {
            "catalogue_sha256": digest("/config/astv/astv_intent_catalogue.yaml"),
            "mapping_sha256": digest("/config/AdvNFC/advnfc_tag_mapping.yaml"),
        },
        "authentication": {"admin_created": True, "non_admin_created": True, "secrets_retained": False},
    }
    Path("/config/staging/stage-evidence.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    Path("/config/staging/browser-session.json").write_text(
        json.dumps({"base_url": "http://home-assistant:8123", "admin": ADMIN, "reader": READER, "admin_access_token": token})
    )
    return evidence


if __name__ == "__main__":
    asyncio.run(prepare(create_owner_token()))
