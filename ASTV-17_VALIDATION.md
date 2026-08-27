# ASTV-17 validation evidence

Date: 2026-08-12

## Pickup and dependency gate

- Linear issue `ASTV-17` was retrieved in `Ready` in a separate Codex
  implementation task.
- Dependency `ASTV-16` was `Done` after its accepted Kitchen validation, and
  `ASTV-17` had subsequently been explicitly placed in `Ready`.
- The accepted ASTV-16 production starting state was re-read from Home
  Assistant and checked against the current execution-dispatch contract and
  architecture before implementation.
- No material source-of-truth conflict or ambiguity was found.
- `ASTV-17` was moved from `Ready` to `In Progress` before any implementation
  change.

## Rollback baseline

Exact accepted ASTV-16 configurations were captured before cutover:

- Dispatcher:
  `ASTV-17_Rollback/astv_select_execution_engine.pre-cutover.json`
  - Stable configuration hash: `1daf2ae8f39f9a41`
  - Snapshot SHA-256:
    `AEE0344DEDE5D9CF8ADAFE508706D6E21935732662A76AA3BF989CD69E22836E`
- Select Intent Engine:
  `ASTV-17_Rollback/astv_select_intent_engine.pre-cutover.json`
  - Stable configuration hash: `b61a25f53d8c67a2`
  - Snapshot SHA-256:
    `9B0DD41048CD67415474349B04213FF8AD62A95F3F53FF0E0F0FD58167666A11`

## Production configuration

### Routine Intent Engine

- Created `script.astv_intent_engine_routine` with friendly name
  `ASTV - Intent Engine: Routine`.
- Stable configuration hash: `26a9cd9cc3f31ce0`.
- Required inputs are exactly `request` (object) and `target_area` (text).
- The native Home Assistant response mapping contains four separate top-level
  fields:
  - `request`, passed through unchanged;
  - `target_area`, passed through unchanged;
  - `execution_method: g_automation`;
  - `selected_endpoint: {}`.
- The engine has no trigger resolution or execution action.

### Global execution dispatcher

- Updated `script.astv_select_execution_engine` stable hash:
  `7ddd59fd391617dd`.
- Its four explicit inputs and the accepted `ha_mplayer` and `g_home_device`
  branches remain intact.
- Added only `g_automation`, mapping:
  - `routine: request.routine`;
  - `target_area: target_area`.
- The new branch validates non-blank routine and target area before calling
  Google Automation. It intentionally ignores the empty selected endpoint.

### Select Intent Engine

- Updated `script.astv_select_intent_engine` stable hash:
  `325c73773e53f0ab`.
- The Media outcome remains unchanged.
- The Routine outcome now calls the Routine Intent Engine, captures
  `routine_intent_response`, and passes its four returned fields separately to
  the dispatcher.
- Dispatch remains inside the selected branches. No Phase 2 merge or shared
  post-choice dispatcher call was introduced.

## Unchanged production boundaries

- Media Intent Engine: `16606dea116a7cdc`.
- Retained Media selector: `34399947ac8297aa`.
- Google Automation Engine: `3b7f13a2f76bc49f`.
- Find Routine Trigger: `cb78900af585094e`.
- HA Media Player Engine: `d4d5039b2ba6dc0b`.
- Google Home Device Engine: `32dba34e015c9156`.

The Google Automation flow still resolves the trigger in
`script.astv_find_routine_trigger` and terminates with
`input_boolean.turn_on`. No provider or execution-engine implementation was
changed.

## Kitchen-only validation baseline

Current production evidence established these controlled existing Kitchen
cases before invocation:

- Routine: `Good Morning Routine`, `routine: morning`, Kitchen area ID
  `5fa17a3cccaf4af0a5daef18141375fd`, expected helper
  `input_boolean.gh_trigger_101`.
- HA Media Player: UID `7AB06354E000`, Classic FM, expected endpoint
  `media_player.kitchen_speaker`.
- Google Home Device: UID `DEADLBC`, LBC, expected endpoint phrase
  `Kitchen Speaker`.

Live metadata confirmed `input_boolean.gh_trigger_101` belongs to Kitchen and
has labels `Matter GH Trigger` and `Routine - Morning`. No executing test
targeted any other area.

## Kitchen Routine result

The controlled Routine completed successfully through the new topology:

- Select Intent Engine: `6afe29624bae268554ba5c41720216d1`.
- Routine Intent Engine: `dc847b42f5c150fef5826d26cccd14a8`.
- Execution dispatcher: `eedd785284ba5d2720ed0e4799b643f1`.
- Google Automation Engine: `35c9ad41e81fac272e858ecf8bfa56a2`.
- Find Routine Trigger: `06b24dd5ba23e81995503c75ea5202c9`.

Trace evidence confirms:

- Routine Intent Engine received and returned the same complete request.
- It received and returned the same Kitchen area ID.
- It returned `execution_method: g_automation` and an empty
  `selected_endpoint`.
- The dispatcher received those four separate fields and called only Google
  Automation with `routine: morning` and the same Kitchen area.
- The unchanged trigger resolver found only `input_boolean.gh_trigger_101`.
- The unchanged terminal action turned on that helper.
- The existing Google Home automation returned the helper to `off` after the
  controlled trigger.

## Failure-path validation

All negative tests were non-executing and either used the Kitchen area ID or a
deliberately blank target area.

| Case | Dispatcher trace | Result |
| --- | --- | --- |
| Blank routine | `68b091b03958727761cd92c0d3f4e7fb` | Visible notification; `error: true`; aborted before Google Automation. |
| Blank target area | `3a4512f9f17e0e05fafeb8c55a40ee9d` | Visible notification; `error: true`; aborted before Google Automation. |
| Unknown execution method | `223efdde5a2e3acee8ab45082281c5fe` | Visible notification; `error: true`; aborted before downstream selection. |

After all three tests, the latest Google Automation trace remained the
successful Routine run `35c9ad41e81fac272e858ecf8bfa56a2`, proving no
negative case called the downstream engine.

## Kitchen Media regression results

### HA Media Player

- UID Gateway: `865124f1bbbe7c6e4928c587ea7c09b8`.
- Media Intent Engine: `5fefbc7542822b0a53aef8b7f0947491`.
- Execution dispatcher: `e1b930372b2abc49031cabe5ffaab0d1`.
- HA Media Player Engine: `6c3d26705fd707917b1b81e4694c6928`.
- The dispatcher received the accepted Classic FM request, Kitchen area,
  `ha_mplayer`, and `media_player.kitchen_speaker`.
- The unchanged downstream path called `media_player.play_media` on the
  Kitchen speaker with Classic FM. All traces finished successfully.

### Google Home Device

- UID Gateway: `cc7c663a2e072ba80bbf88b817669ed0`.
- Media Intent Engine: `e078ef03e969fa434625be67bafb2837`.
- Execution dispatcher: `cdfdfb3ff402af97db0efffee7870cd1`.
- Google Home Device Engine: `64534811c774d873c2d96211370b381b`.
- The dispatcher received the accepted LBC request, Kitchen area,
  `g_home_device`, and endpoint phrase `Kitchen Speaker`.
- The unchanged downstream path called Google Assistant with
  `play LBC Radio on Global Player on Kitchen Speaker`. All traces finished
  successfully.

## Current callers and rollback preservation

A post-cutover Home Assistant configuration search found:

- the dispatcher definition plus exactly the active Media Intent Engine and
  Select Intent Engine callers;
- the Google Automation definition plus only the dispatcher caller;
- the Routine Intent Engine definition plus only the Select Intent Engine
  caller;
- the retained Media selector only as its own unchanged definition.

The connector reported that three YAML-defined automations and three
YAML-defined scripts could not be fetched through its per-item configuration
endpoint, so that search is not exhaustive. No unexpected consumer appeared in
the searchable live configuration, current traces, contracts, architecture, or
ASTV artefacts.

## Contracts and architecture

- Updated `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` for the exact
  ASTV-17 transitional interface and topology.
  - SHA-256:
    `C60AE2631F61A82DE80A4115F2FBDC7AEBD3E74F455D1CE8BFCBF9499FC424CF`
- Updated `01_Architecture/ASTV_ARCHITECTURE.md` for both Intent Engines, the
  three dispatcher methods, branch-local dispatch, open Phase 2 split, and
  unchanged Google Automation internals.
  - SHA-256:
    `EB79099CB620F9D40DE59CCD3FCFBE238C5AE4DADC5958CC01A5171B46C7C60B`
- The user confirmed the draw.io file was closed before Codex re-read and
  edited the latest file from disk.
- Updated `01_Architecture/ASTV_Architecture.drawio` with only the Routine
  Intent Engine call/return, branch-local dispatcher call, and Google
  Automation dispatcher outcome required by current production.
  - SHA-256:
    `C3EF68AA28FEB89C973A8F7D65E4942114D2B6709507463E2406FE4E2D8B1115`
  - XML validation: 203 cells, zero duplicate IDs, zero dangling parent,
    source, or target references.
- Existing diagram objects and coordinates were preserved. No PNG or PDF
  export was created.

Production, the execution-dispatch contract, architecture narrative, and
diagram agree on the transitional ASTV-17 topology.
