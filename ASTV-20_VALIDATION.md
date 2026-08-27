# ASTV-20 validation evidence

Date: 2026-08-12

## Pickup and source-of-truth gate

- Linear issue `ASTV-20` was retrieved in `Ready` in this separate Codex
  implementation task.
- Current Home Assistant definitions, the execution-dispatch contract,
  architecture narrative, diagram, and applicable `AGENTS.md` rules were read
  before implementation.
- The issue's recorded starting hashes were confirmed exactly:
  - Select Execution Engine: `7ddd59fd391617dd`;
  - Google Automation Engine: `3b7f13a2f76bc49f`.
- The pre-cutover dispatcher passed complete `request` objects to the two Media
  engines but passed scalar `request.routine` to Google Automation. Google
  Automation declared scalar `routine` and `target_area` inputs.
- A repeated pre-cutover caller search found Select Execution Engine as the
  only exposed production caller of Google Automation. The connector again
  reported that three YAML-defined automations and three YAML-defined scripts
  were not exposed by the per-item configuration endpoint. The local
  `Production_ReadOnly` mount contained no hydrated files that could add
  caller evidence.
- This reproduced the limitation already recorded in the approved issue and
  introduced no source-of-truth conflict or material ambiguity.
- `ASTV-20` was moved from `Ready` to `In Progress` before implementation.

## Rollback baseline

Exact pre-cutover configurations were captured before production mutation in
`ASTV-20_Rollback/`:

| Script | Home Assistant hash | Snapshot SHA-256 |
| --- | --- | --- |
| Select Execution Engine | `7ddd59fd391617dd` | `76E194D04A8784ECEB0D26CA6BDADD4546859443ECBA0F641DBDCF503BEBCEAD` |
| Google Automation Engine | `3b7f13a2f76bc49f` | `8AFA706364D9F796649594A3C780C416A57DE03EC851F0CF28D59A51B8CBFC18` |

Both JSON snapshots parsed successfully.

Before the review revision, the current post-cutover definitions were also
captured so that the immediately preceding accepted state can be restored:

| Script | Home Assistant hash | Snapshot SHA-256 |
| --- | --- | --- |
| Select Execution Engine | `1c0b3ea458cfd2cf` | `92BD226606BDF68948F54CDA4FF90306DCE6630653BAC18025C78240F3ACFD70` |
| Google Automation Engine | `6aa39b6b39d12378` | `74E5B93110C019CDB7285A008BC86F2B3E84120CA1AFA2ED1A68D248C112E739` |

Both review-revision JSON snapshots parsed successfully. The original
pre-cutover pair remains retained alongside them.

## Production configuration

### Select Execution Engine

- Initial cutover hash: `1c0b3ea458cfd2cf`.
- Review-revision stable hash: `338ddf0d9a75efc8`.
- The Google Automation branch now calls
  `script.astv_g_automation_engine` with the unchanged complete `request` and
  separate `target_area`.
- The review revision removes `resolved_routine` and introduces no replacement
  routine-derived dispatcher variable.
- The blank-routine guard now evaluates
  `request.routine | default('', true) | string | trim` inline. The existing
  `resolved_target_area` validation remains unchanged.
- The `ha_mplayer` and `g_home_device` branches are unchanged and still pass
  complete `request` objects with `selected_endpoint`.
- Mode remains `parallel`; maximum remains `10`; the four-field dispatcher
  input boundary and no-response behaviour are unchanged.

### Google Automation Engine

- Updated stable hash: `6aa39b6b39d12378`.
- Required inputs are exactly `request` (object) and `target_area` (text).
- Find Routine Trigger receives scalar `request.routine` and `target_area`.
- The failure message derives its routine from `request.routine`.
- Mode `parallel`, maximum `10`, response capture as `trigger_response`,
  failure behaviour, and terminal `input_boolean.turn_on` action are
  unchanged.
- The connector's best-practice checker repeated warnings about inherited
  template conditions and the existing dynamic helper target. Those
  behaviours are explicitly preserved by ASTV-20 and were not broadened into
  an unrelated refactor.

## Successful normal-entry validation

All three cases were invoked through `script.astv_uid_gateway` with
`sensor.pi_nfc_99_last_uid`, preserving the shared normal entry path.

### Classic FM / HA Media Player

- UID: `7AB06354E000`.
- Select Execution Engine trace: `fab40184356becb8f6bb447c45347019`.
- HA Media Player Engine trace: `442c045350e732cd4975b3c5c0762330`.
- The unchanged request selected `media_player.kitchen_speaker` and loaded
  Classic FM through `media_player.play_media`.

### LBC / Google Home Device

- UID: `DEADLBC`.
- Select Execution Engine trace: `94d39855462313ba6e8eafa82bbc32a7`.
- Google Home Device Engine trace: `131a30f91c1cf91587bb897f434264dc`.
- The unchanged request and endpoint phrase `Kitchen Speaker` produced the
  accepted command `play LBC Radio on Global Player on Kitchen Speaker` and
  invoked `google_assistant_sdk.send_text_command`.

### Morning Routine / Google Automation

- UID: `DEADMORNING`.
- Select Intent Engine trace: `c50c790ff4fa30e19e7470ae41d52e6b`.
- Select Execution Engine trace: `b356123920f3abb6bafd8e25f480cbb9`.
- Google Automation Engine trace: `303ed877b2b13a41ff216174da4bb62b`.
- Find Routine Trigger trace: `cb76df7c2284d4aa3b2b08b57307f86a`.
- The dispatcher passed the complete unchanged request
  `{intent: routine.run, routine: morning, title: Good Morning Routine,
  params: {}}` and Kitchen area
  `5fa17a3cccaf4af0a5daef18141375fd` to Google Automation.
- Google Automation passed scalar `morning` and the same Kitchen area to Find
  Routine Trigger.
- The resolver selected the same `input_boolean.gh_trigger_101`; Google
  Automation turned it on, and the existing Google Home automation returned
  it to `off` at `2026-08-12T17:37:36.953232+01:00`.

## Failure-path validation

| Case | Dispatcher trace | Result |
| --- | --- | --- |
| Blank `request.routine` | `b3f39802d5539b78e6553612725d5231` | Visible notification; aborted with `error: true`; no Google Automation call. |
| Blank `target_area` | `53f61cb58558592abe84012482f3cc1c` | Visible notification; aborted with `error: true`; no Google Automation call. |

After both negative cases, Google Automation's newest trace remained the
successful Morning trace `303ed877b2b13a41ff216174da4bb62b`, proving neither
failure path called the downstream engine.

## Current caller evidence

Post-cutover Home Assistant configuration search found:

- Select Execution Engine is the sole exposed caller of Google Automation.
- Its call supplies `request` and `target_area`; no exposed caller supplies a
  scalar `routine` field to Google Automation.
- Google Automation itself supplies scalar `request.routine` and `target_area`
  only to Find Routine Trigger, as required.

The connector still reported the same three YAML-defined automations and three
YAML-defined scripts as unscannable through the configuration endpoint. No
unexpected consumer appeared in searchable live configuration, current
traces, contracts, architecture, or available ASTV artefacts.

## Review-revision validation

The issue was retrieved again in `Ready` after review, checked against current
production and current documentation, and moved to `In Progress` before the
revision. Production matched the recorded intermediate hashes and the only
remaining defect was the unnecessary `resolved_routine` alias identified by
review.

The Select Execution Engine was updated with an optimistic-lock transform from
hash `1c0b3ea458cfd2cf` to `338ddf0d9a75efc8`. The transform made exactly two
semantic edits:

- removed `resolved_routine` from the initial variables action;
- changed the blank-routine guard to
  `{{ request.routine | default('', true) | string | trim == '' }}`.

The resulting dispatcher variables are exactly
`resolved_execution_method`, `resolved_selected_endpoint`, and
`resolved_target_area`. The four input fields, mode `parallel`, maximum `10`,
all branch calls, messages, stop actions, and Media endpoint validation remain
unchanged. Google Automation remained unchanged at hash
`6aa39b6b39d12378`.

### Review-revision normal-path tests

All three positive tests again entered through `script.astv_uid_gateway` and
`sensor.pi_nfc_99_last_uid`.

| Path | UID | Dispatcher trace | Engine trace | Result |
| --- | --- | --- | --- | --- |
| Morning Routine / Google Automation | `DEADMORNING` | `3a5ecdc639528173c3fe2a95e0766ae1` | `3826a52a72f39a3b570b2f33b996dee9` | Complete unchanged request reached Google Automation; scalar `morning` and Kitchen area reached Find Routine Trigger; `input_boolean.gh_trigger_101` was selected and activated. |
| Classic FM / HA Media Player | `7AB06354E000` | `ba5751b078e1552ab861585b01028db1` | `13a558ab797e6cb083941b40ad02c565` | Complete unchanged request and `media_player.kitchen_speaker` reached the existing engine; Classic FM was loaded through `media_player.play_media`. |
| LBC / Google Home Device | `DEADLBC` | `5d81f177a087ab033e84a6aa19d948ef` | `1aa7d370b0ff90fca875cc21027566ff` | Complete unchanged request and `Kitchen Speaker` endpoint reached the existing engine; the accepted Google Assistant command was sent. |

The Morning path also produced Select Intent Engine trace
`4d9e2859fc1e8ba5ac70e097fbd290ec` and Find Routine Trigger trace
`88ceefb9afc554fee698eb831907ab0a`. The resolver again selected
`input_boolean.gh_trigger_101`; the downstream Google Home automation returned
it to `off` at `2026-08-12T17:54:28.655206+01:00`.

### Review-revision failure tests

| Case | Dispatcher trace | Result |
| --- | --- | --- |
| Empty routine | `c64e8940502b47fb0c5477347652c17c` | Visible notification and `error: true`; no Google Automation call. |
| Whitespace-only routine | `6f6a159cc42ff9e15eea946c430f1cb5` | Visible notification and `error: true`; no Google Automation call. |
| Missing routine key | `1e35537b4937a54c705125856ae8afa7` | Visible notification and `error: true`; no Google Automation call. |
| Blank target area | `4b23ca9795c81a10dae827bd18f8af3a` | Visible notification and `error: true`; no Google Automation call. |

After all four failure cases, Google Automation's newest trace remained the
successful Morning trace `3826a52a72f39a3b570b2f33b996dee9`.

The post-revision caller search again found Select Execution Engine as the only
exposed caller of Google Automation, supplying only `request` and
`target_area`. It retained the documented limitation that three YAML-defined
automations and three YAML-defined scripts are not exposed by the per-item
configuration endpoint; the read-only production mount still contains no
hydrated files that add caller evidence.

The user confirmed the diagram was closed before its latest saved contents
were re-read. No review-revision diagram edit was necessary because the first
cutover already left the requested labels in place. Revalidation confirmed:

- Select Execution Engine to Google Automation labels: `request`,
  `target_area`;
- Google Automation to Find Routine Trigger labels: `routine`, `target_area`;
- 196 cells, zero duplicate IDs, and zero dangling parent, source, or target
  references;
- unchanged diagram SHA-256
  `A261534526B78D3E96B27F1E552D37CBD2030C5CFB8EB1E9BB838A3403030116`.

The interface contract and architecture narrative already expressed the
normalized boundary and therefore required no review-revision content change.
Their hashes remain `0CC0A796B7FF69A13B895431F25578C6052D70FC742211AFDE15833C2F2E8F00`
and `B166912B098FB3662DEFBDF5A700266288CC9882109C2BFC60016BA842D6EB1A`
respectively. No PNG or PDF was exported.

## Contracts and architecture

- Updated `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` so all three
  implemented engines receive complete `request`, while Google Automation
  receives separate `target_area` and calls Find Routine Trigger with scalar
  `request.routine`.
  - SHA-256:
    `0CC0A796B7FF69A13B895431F25578C6052D70FC742211AFDE15833C2F2E8F00`.
- Updated `01_Architecture/ASTV_ARCHITECTURE.md` with the same boundary.
  - SHA-256:
    `B166912B098FB3662DEFBDF5A700266288CC9882109C2BFC60016BA842D6EB1A`.
- The user confirmed the diagram was closed before Codex re-read the latest
  saved file. Its pre-edit SHA-256 was
  `076922CE88F80FEC72DE68B0BF0BEEDD435EEA9FB9B78B2DEBB04E792D517255`.
- Updated only the existing Select Execution Engine to Google Automation
  connector payload value from `routine` to `request`. The separate
  `target_area` label and Google Automation to Find Routine Trigger labels
  `routine` and `target_area` remain unchanged.
- Diagram SHA-256:
  `A261534526B78D3E96B27F1E552D37CBD2030C5CFB8EB1E9BB838A3403030116`.
- XML validation: 196 cells, zero duplicate IDs, and zero dangling parent,
  source, or target references.
- No PNG or PDF was exported.

Production definitions, current caller evidence, the interface contract,
architecture narrative, and diagram agree on the normalized execution
boundary. No unrelated production configuration, contracts, architecture
objects, or project files were changed.
