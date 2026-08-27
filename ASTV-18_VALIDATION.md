# ASTV-18 validation evidence

Date: 2026-08-12

## Pickup and dependency gate

- Linear issue `ASTV-18` was retrieved in `Ready` in a separate Codex
  implementation task.
- Dependency `ASTV-17` was `Done` after its accepted Kitchen validation, and
  `ASTV-18` had subsequently been explicitly placed in `Ready`.
- The accepted ASTV-17 production starting state was re-read from Home
  Assistant and checked against the current execution-dispatch contract and
  architecture narrative before implementation.
- Accepted starting hashes were confirmed exactly:
  - Select Intent Engine: `325c73773e53f0ab`;
  - Media Intent Engine: `16606dea116a7cdc`;
  - Routine Intent Engine: `26a9cd9cc3f31ce0`;
  - Select Execution Engine: `7ddd59fd391617dd`;
  - retained Media selector: `34399947ac8297aa`.
- No material source-of-truth conflict or ambiguity was found.
- `ASTV-18` was moved from `Ready` to `In Progress` before any implementation
  change.

## Rollback baseline

Exact accepted ASTV-17 configurations were captured before cutover under
`ASTV-18_Rollback/`:

| Script | Home Assistant hash | Snapshot SHA-256 |
| --- | --- | --- |
| Select Intent Engine | `325c73773e53f0ab` | `5A8E705F10C16C2FB9F671F21D021B5DDB91CD47667B1A6B6BA7252E7830462A` |
| Media Intent Engine | `16606dea116a7cdc` | `BD792CBE8E4BE38AF473A6B73D5044A9AAE60F46D3C06947B33BA5095D6D3F58` |
| Routine Intent Engine | `26a9cd9cc3f31ce0` | `6066A0823FE91883B104BB9F4D596D3C0C812DE4A356EB26CC9BB0B645363173` |

## Production configuration

### Media Intent Engine

- Updated stable hash: `b36661a38e022b4b`.
- Retains the accepted three Media-specific resolution calls in order:
  Find Area Domain Endpoints, Resolve Playback Method, and Select Area
  Playback Endpoint.
- Removed its internal dispatcher call.
- Returns a native response mapping with four separate top-level fields:
  unchanged `request`, unchanged `target_area`, resolved `execution_method`,
  and resolved `selected_endpoint`.
- Does not invoke a dispatcher or execution engine.

### Select Intent Engine

- Updated stable hash: `e9759f8b814b63df`.
- Each exclusive outcome invokes exactly one intent engine and captures the
  complete response as `intent_response`.
- The `choose` finishes before a single shared call to
  `script.astv_select_execution_engine` passes the four values separately.
- The unknown-intent default now creates the existing visible notification and
  stops with `error: true` before the post-choice dispatcher call.

### Preserved boundaries

- Routine Intent Engine remains unchanged at `26a9cd9cc3f31ce0`.
- Select Execution Engine remains unchanged at `7ddd59fd391617dd`.
- Retained Media selector remains unchanged at `34399947ac8297aa`.
- No downstream execution engine, provider, routine resolver, or external
  action configuration was changed.

## Kitchen-only test inputs

Current production records were re-resolved before live execution:

| UID | Intent record | Expected method and action |
| --- | --- | --- |
| `7AB06354E000` | `classic_fm` / Play Classic FM | `ha_mplayer` to `media_player.kitchen_speaker` |
| `DEADLBC` | `lbc_radio` / LBC | `g_home_device` with endpoint phrase `Kitchen Speaker` |
| `DEADMORNING` | `morning_routine` / Good Morning Routine | `g_automation`, routine `morning`, helper `input_boolean.gh_trigger_101` |

`area_id('sensor.pi_nfc_99_last_uid')` re-evaluated to the Kitchen area ID
`5fa17a3cccaf4af0a5daef18141375fd`. The helper was also re-confirmed in that
area with labels `Matter GH Trigger` and `Routine - Morning`.

## Successful normal-entry validation

All three cases were invoked through `script.astv_uid_gateway` with the
Kitchen reader entity.

### Classic FM / HA Media Player

- Select Intent Engine: `a49de051766936dcf3d420a454b1f840`.
- Media Intent Engine: `f183000bbbe3057ed8ecc974913213cd`.
- Execution dispatcher: `831e82977b1764c87ef751627e8b726b`.
- HA Media Player Engine: `3c8b838814b850be9facc59146df077f`.
- Media returned the unchanged request and Kitchen area, `ha_mplayer`, and
  `media_player.kitchen_speaker`.
- Select Intent Engine captured that complete response, exited choice path 0,
  then invoked one dispatcher at sequence step 2.
- The dispatcher invoked exactly one HA Media Player Engine, and the Kitchen
  speaker loaded Classic FM.

### LBC / Google Home Device

- Select Intent Engine: `d7a30e6163eda23f184bd566c2894725`.
- Media Intent Engine: `aac09ab0e8c75337ceb9e3010a1c21d5`.
- Execution dispatcher: `fd197354437a4f174eee36846c126095`.
- Google Home Device Engine: `6e17eb511816bfa2ca434236f42766bc`.
- Media returned the unchanged request and Kitchen area, `g_home_device`, and
  endpoint phrase `Kitchen Speaker`.
- Select Intent Engine captured that complete response, exited choice path 0,
  then invoked one dispatcher at sequence step 2.
- The dispatcher invoked exactly one Google Home Device Engine with the
  accepted LBC request and endpoint.

### Morning / Google Automation

- Select Intent Engine: `3c0df4dafd76ff7d54c612a4fc4208d3`.
- Routine Intent Engine: `c8ad25974c9af3af2f6e047250e81a61`.
- Execution dispatcher: `aa13651b0b00f55073bc79c5a66eae80`.
- Google Automation Engine: `73c4456ba715ec5833c03213808e7151`.
- Routine returned the unchanged request and Kitchen area, `g_automation`,
  and an empty endpoint.
- Select Intent Engine captured that complete response, exited choice path 1,
  then invoked one dispatcher at sequence step 2.
- The dispatcher invoked exactly one Google Automation Engine with routine
  `morning` and the Kitchen area. The unchanged resolver selected and turned on
  `input_boolean.gh_trigger_101`; the existing Google Home automation later
  returned it to `off`.

## Failure-path validation

| Case | Trace | Result |
| --- | --- | --- |
| Unknown intent | `484ced7e023fd99e310e363c73d0fc23` | Visible notification; `error: true`; aborted inside the choice with no sequence step 2 dispatcher call. |
| Unknown method | `80eea5f600e9cdd497f3510109dc78ba` | Visible notification; `error: true`; no downstream engine. |
| Missing Media endpoint | `7528a487d43dd1cdc98458f896ab32d4` | Visible notification; `error: true`; no HA Media Player call. |
| Blank routine | `d6ab6f0d0dd95d032af93b2f0f7cfcf7` | Visible notification; `error: true`; no Google Automation call. |
| Blank target area | `1385de2782d2eaa96361a90bfe137c52` | Visible notification; `error: true`; no Google Automation call. |

The newest downstream trace IDs remained the three successful Kitchen runs
after all negative cases, proving that none invoked an execution engine.

## Current caller search

Post-cutover Home Assistant configuration search found:

- Select Intent Engine is the sole searchable production caller of the
  dispatcher.
- Neither intent engine calls the dispatcher or an execution engine.
- The dispatcher is the sole active caller of Google Automation.
- The dispatcher is the sole active caller of both Media execution engines;
  the retained old Media selector still contains its rollback calls but has no
  caller of its own.
- `script.astv_select_media_engine` remains unchanged and caller-free.

The connector reported that three YAML-defined automations and three
YAML-defined scripts could not be fetched through its per-item configuration
endpoint, so configuration-body search is not exhaustive. No unexpected
consumer appeared in searchable live configuration, current traces, contracts,
architecture, or ASTV artefacts.

## Contracts and architecture

- Updated `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` to the final shared
  Phase 2 interface, exclusive merge, single dispatcher caller, and retained
  `g_automation` empty-endpoint semantics.
  - SHA-256:
    `CAA84BFE9CE8CC0F08FFAA477F7EE60CDD4D7545DF705B558EB03E513192A778`
- Updated `01_Architecture/ASTV_ARCHITECTURE.md` to the final active topology.
  - SHA-256:
    `4D30F09DA013178D584B88702348BC1AA9221607FD50B2F68B7FC68E43895906`
- The user confirmed the draw.io file was closed before Codex re-read and
  edited the latest file from disk. Its pre-edit SHA-256 was
  `CCA9247BEE8613C5889E5A0A3A6F93E47E03D90791DDE40DA3F30F6FAAB3EA35`.
- Updated `01_Architecture/ASTV_Architecture.drawio` by making the existing
  anonymous Phase 2 junction the explicit `gateway_merge_intent` and renaming
  its incoming and shared outgoing connector identifiers for neutral final
  topology semantics.
- Preserved the existing intent-engine positions, merge geometry, connector
  routes, and four separate native payload labels crossing into Phase 3:
  `execution_method`, `request`, `target_area`, and `selected_endpoint`.
- Diagram SHA-256:
  `1204267DDE2D6F603F2B598DA61CA56E32A1A84CA912E62198DFD597FFCC23EA`.
- XML validation: 196 cells, zero duplicate IDs, zero dangling parent/source/
  target references; the intent merge has exactly two incoming connectors and
  one outgoing connector.

Production, the execution-dispatch contract, architecture narrative, and
diagram agree on the final active topology. ASTV-18 is ready for user review
and testing.
