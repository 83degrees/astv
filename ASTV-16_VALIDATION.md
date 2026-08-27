# ASTV-16 validation evidence

Date: 2026-08-12

## Pickup and rollback baseline

- Linear issue `ASTV-16` was retrieved in `Ready`, checked against current
  production scripts, the current AdvMedia contract, and architecture, then
  moved to `In Progress` before implementation.
- No material source-of-truth conflict or ambiguity was found.
- Exact pre-cutover Media caller configuration:
  `ASTV-16_Rollback/astv_intent_engine_media.pre-cutover.json`.
- Pre-cutover `script.astv_intent_engine_media` stable hash:
  `af4f068ab94770a3`.
- Rollback snapshot SHA-256:
  `AAD35F76BDBB1A9022487FD62ABCACABF3F4D4FBCE83D162050D8DB1E3F954E5`.

## Production configuration

- Created `script.astv_select_execution_engine` with friendly name
  `ASTV - Select Execution Engine`.
- Dispatcher hash: `1daf2ae8f39f9a41`.
- Inputs are exactly `execution_method`, `request`, `target_area`, and
  `selected_endpoint`; all are required and use the specified selectors.
- Mode is `parallel`, maximum concurrent runs is `10`, and no common response
  is returned.
- Implemented methods are only `ha_mplayer` and `g_home_device`.
- `ha_mplayer` validates `selected_endpoint.media_entity` before calling
  `script.astv_ha_mplayer_engine`.
- `g_home_device` validates `selected_endpoint.phrase` before calling
  `script.astv_g_home_device_engine`.
- Blank or unsupported methods and invalid endpoints create a persistent
  notification and stop with `error: true`.
- Updated `script.astv_intent_engine_media` hash: `16606dea116a7cdc`.
- The first three Media resolution calls are unchanged. The caller now derives
  separate `execution_method` and `selected_endpoint` variables from
  `area_playback_endpoint_response`, then calls only the new dispatcher with
  all four inputs.

## Unchanged production boundaries

- `script.astv_select_media_engine` is present and unchanged at hash
  `34399947ac8297aa`.
- `script.astv_select_intent_engine` remains unchanged at hash
  `b61a25f53d8c67a2`; Routine still calls
  `script.astv_g_automation_engine` directly.
- `script.astv_g_automation_engine` remains unchanged at hash
  `3b7f13a2f76bc49f`.
- Downstream Media engines remain unchanged:
  - `script.astv_ha_mplayer_engine`: `d4d5039b2ba6dc0b`
  - `script.astv_g_home_device_engine`: `32dba34e015c9156`
- A post-cutover Home Assistant configuration search found the old selector
  only as its retained script definition. The new dispatcher was found only as
  its own definition and the active Media caller. The connector reported that
  three YAML-defined automations/scripts could not be fetched through the
  per-item configuration endpoint; no unexpected consumer was present in the
  searchable live configuration, active traces, contracts, or current ASTV
  artefacts.

## Kitchen-only validation baseline

- `sensor.pi_nfc_99_last_uid` and `media_player.kitchen_speaker` both resolved
  live to area ID `5fa17a3cccaf4af0a5daef18141375fd`, area name `Kitchen`.
- Current retained production traces established controlled accepted cases
  before new invocation:
  - UID `7AB06354E000` / `classic_fm` -> `ha_mplayer` ->
    `media_player.kitchen_speaker`.
  - UID `DEADLBC` / `lbc` -> `g_home_device` -> endpoint phrase
    `Kitchen Speaker`.
- No executing test targeted any other area.

## Kitchen end-to-end results

### HA Media Player

- UID Gateway trace: `ceb3e64c18a21af33feb342d739df88b`.
- Intent Gateway trace: `5cef40c5215ad4091004cec865a2705e`.
- Media Intent Engine trace: `7c45f0081d55b6642426e837854bd611`.
- Execution dispatcher trace: `023cccde0dd6ce2a74030b9f4581dde0`.
- HA Media Player Engine trace: `c85618b7da239934165178a9d45ba31a`.
- Dispatcher received `ha_mplayer`, the complete Classic FM request, Kitchen
  area ID, and `media_player.kitchen_speaker`, then called only the HA Media
  Player Engine.
- The downstream trace retained the accepted Radio Browser request and called
  `media_player.play_media` on `media_player.kitchen_speaker` with Classic FM.
- All traces finished successfully.

### Google Home Device

- UID Gateway trace: `91c739c025b1f2742a1615e8bf93f8ea`.
- Intent Gateway trace: `fd74b3cfbcc2e80b701d1aae0c1e0f17`.
- Media Intent Engine trace: `3ef76d0a90ad0fc029c35b43646df5da`.
- Execution dispatcher trace: `06db211e4c847ec2d975e88b5b07c4e3`.
- Google Home Device Engine trace: `316926060eb3ba69b2039d66a49f003c`.
- Dispatcher received `g_home_device`, the complete LBC request, Kitchen area
  ID, and endpoint phrase `Kitchen Speaker`, then called only the Google Home
  Device Engine.
- The downstream trace retained the accepted request and called
  `google_assistant_sdk.send_text_command` with
  `play LBC Radio on Global Player on Kitchen Speaker`.
- All traces finished successfully.

## Failure-path validation

All failure tests used only the Kitchen area ID and synthetic non-executing
request data.

| Case | Dispatcher trace | Result |
| --- | --- | --- |
| Unsupported method | `35bf859b06574bf39360f6f98075a46a` | Visible notification; `error: true`; aborted before downstream selection. |
| Blank method | `61e0900ee9c2a58de635d420458fa79f` | Visible notification; `error: true`; aborted before downstream selection. |
| Empty HA Media Player endpoint | `96d032ab241634dd487debb2ae28f071` | Visible branch-specific notification; `error: true`; HA engine not called. |
| Empty Google Home Device endpoint | `32aea8f3ad881711c0385c25599e2ab2` | Visible branch-specific notification; `error: true`; Google Home engine not called. |

## Contracts and architecture

- Created `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` for the exact
  transitional dispatcher boundary.
- Contract SHA-256:
  `3781043E954A108B314FE82C04BE910AC0C73D550C823851A7F1BA0C8FEDEDE8`.
- Updated `01_Architecture/ASTV_ARCHITECTURE.md` to document the active Media
  dispatcher, unchanged direct Routine path, open Phase 2 intent split, and
  retained caller-free rollback selector.
- Narrative SHA-256:
  `C716593A0D6B6FD53B5A6952F6CB167C362C18AB354ABC6519424F50F8C194E7`.
- The user confirmed the active draw.io file was closed before Codex read and
  edited the latest file from disk.
- Updated `01_Architecture/ASTV_Architecture.drawio` with the new dispatcher,
  four separate native connector labels, `Execution Method?` split, the two
  current Media outcomes, and a disconnected dashed rollback representation of
  the old selector. The Routine connector and components were unchanged.
- Diagram SHA-256:
  `FB267E32393D1259B3A4D55283D78E3FE1894B0CFD58C3AD993DC11A229CBC78`.
- XML validation found 188 cells, zero duplicate IDs, zero dangling parent,
  source, or target references, and no overlap between the retained selector
  box and another Phase 3 vertex.
- No PNG or PDF export was created.
