# ASTV Execution Dispatch Interface

## Contract Record

| Property | Value |
| --- | --- |
| Owner | ASTV |
| Current producers | `script.astv_intent_engine_media` and `script.astv_intent_engine_routine` through `script.astv_select_intent_engine` |
| Current consumer | `script.astv_select_execution_engine` |
| Current version | `2.0.0` — normalized media dispatch active after ASTV-65 proof |
| Status | Current v2; the pre-cutover v1 media shape is retained only as historical implementation context, not as a compatibility promise |
| Source path | `03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` |

## Purpose

Defines the current internal boundary between ASTV intent preparation and the
three implemented execution methods. Version 2 is the only current media
interface. The historical section records the pre-cutover media shape still
visible in dormant live branches; it does not define a current fallback or
compatibility guarantee.

Both Phase 2 intent engines return the same four separately named fields, and
the current media path additionally returns `media_record`.
`script.astv_select_intent_engine` closes the exclusive intent choice and is
the single production caller of the Phase 3 dispatcher.

## Historical Pre-Cutover Media Interface — v1

Before ASTV-65, Media and Routine both returned the same four-field mapping.
Routine still uses that unchanged four-field mapping, but it is not a legacy
media path and remains current under v2. The former media mapping below is
historical.

### Shared Intent Engine Boundary at the Pre-Cutover Boundary

Both intent engines had, and still have, exactly these inputs:

| Input | Type | Required |
| --- | --- | --- |
| `request` | object | yes |
| `target_area` | text | yes |

Before the media cutover, both returned a native Home Assistant response mapping
with exactly these separate top-level fields:

| Output | Meaning |
| --- | --- |
| `request` | Passed through unchanged. |
| `target_area` | Passed through unchanged. |
| `execution_method` | The resolved Phase 3 method. |
| `selected_endpoint` | The resolved endpoint, or an empty object when the method does not use one. |

The response is not wrapped in an `execution_request` or generic payload
object. Neither intent engine invokes an execution engine or the dispatcher.

### Historical Media Intent Engine Result

- Friendly name: `ASTV - Intent Engine: Media`
- Entity: `script.astv_intent_engine_media`
- Mode: `parallel`
- Maximum concurrent runs: `10`

The engine retained Media-specific area-domain endpoint lookup,
playback-method resolution and area endpoint selection. Its returned values
were:

| Output | Media value |
| --- | --- |
| `request` | Passed through unchanged. |
| `target_area` | Passed through unchanged. |
| `execution_method` | The key of the selected one-key playback endpoint response. |
| `selected_endpoint` | The endpoint value selected for that method. |

### Routine Intent Engine (Unchanged and Still Current)

- Friendly name: `ASTV - Intent Engine: Routine`
- Entity: `script.astv_intent_engine_routine`
- Mode: `parallel`
- Maximum concurrent runs: `10`

Inputs:

| Input | Type | Required |
| --- | --- | --- |
| `request` | object | yes |
| `target_area` | text | yes |

The engine is a side-effect-free pass-through. Its Home Assistant response
mapping contains four separate top-level fields:

| Output | Current value |
| --- | --- |
| `request` | Passed through unchanged. |
| `target_area` | Passed through unchanged. |
| `execution_method` | `g_automation` |
| `selected_endpoint` | Empty object. |

The engine does not resolve a routine trigger or execute anything.

### Historical Dispatcher Media Shape

- Friendly name: `ASTV - Select Execution Engine`
- Entity: `script.astv_select_execution_engine`
- Mode: `parallel`
- Maximum concurrent runs: `10`
- Common response: none

#### Inputs

| Input | Type | Required | Pre-cutover Media / current Routine use |
| --- | --- | --- | --- |
| `execution_method` | text | yes | Selects the implemented execution branch. |
| `request` | object | yes | Passed unchanged to all three implemented execution engines. Google Automation derives `request.routine` for trigger lookup. |
| `target_area` | text | yes | Retained as pipeline context and passed to Google Automation. |
| `selected_endpoint` | object | yes | Passed unchanged after Media branch validation; intentionally empty and unused for Google Automation. |

#### Implemented Methods

##### `ha_mplayer`

- Requires a non-blank `selected_endpoint.media_entity`.
- Calls `script.astv_ha_mplayer_engine` with `request` and
  `selected_endpoint`.

##### `g_home_device`

- Requires a non-blank `selected_endpoint.phrase`.
- Calls `script.astv_g_home_device_engine` with `request` and
  `selected_endpoint`.

##### `g_automation`

- Requires a non-blank `request.routine`.
- Requires a non-blank `target_area`.
- Calls `script.astv_g_automation_engine` with:
  - `request: request`
  - `target_area: target_area`
- Google Automation passes scalar `request.routine` and `target_area` to
  `script.astv_find_routine_trigger`.
- Does not consume `selected_endpoint`.

All three implemented execution engines therefore receive the complete
`request` object unchanged from the dispatcher. Google Automation additionally
receives `target_area` because routine-trigger lookup remains area-specific.

#### Failure Contract

A blank or unsupported `execution_method`, a missing HA Media Player endpoint,
a missing Google Home Device endpoint, a blank Routine value, or a blank
Routine target area creates a persistent notification and stops the dispatcher
run with `error: true`. No downstream execution engine is called for a failed
validation. This validation behavior remains current under v2.

## Current Interface — v2

### Status and ownership

Version 2 is the current active production contract after ASTV-65 proof.
ASTV-61 installed the conditional context transport, ASTV-62 installed the HA
Media Player consumer, and ASTV-63 installed the Google Home Device consumer.
ASTV-65 activated those consumers with the seven normalized media records. ASTV
continues to own intent orchestration, method preference and selection, endpoint
selection, dispatch, final Google Home command construction and execution, and
runtime fallback policy.

MediaCat produces the complete normalized media record defined only in the
provider-owned `MEDIACAT_ITEM_LOOKUP_INTERFACE.md` recorded in
`PROJECT_PROFILE.md`. The dispatcher contract references that record and does
not copy its schema.

### Current v2 boundary shape

The Routine response and the common portion of the Media response use these
four fields:

- `request`
- `target_area`
- `execution_method`
- `selected_endpoint`

The current Media path adds one field:

| Field | Presence | Meaning |
| --- | --- | --- |
| `media_record` | Required on the media path; absent on the routine path | Complete normalized MediaCat returned record. |

All seven active media intent records contain both `catalogue_id` and `item_id`
and no `params.sources`; every current Media call therefore supplies
`media_record`. Its optional Home Assistant field declaration exists only so the
live definitions can retain an inactive pre-cutover call shape. It does not make
`media_record` optional on the current Media contract.

The existing internal `execution_method` remains the selected method name. The
internal dispatcher boundary does not add a duplicate
`selected_execution_method` field.

The Routine path retains exactly the four common fields, does not supply
`media_record`, continues to select `g_automation`, and keeps its current
routine-trigger lookup and execution behaviour.

### Media lookup and selection sequence

Before dispatching a media request, ASTV:

1. requests a MediaCat item using `catalogue_id` and `item_id`;
2. receives the complete normalized record with all available
   `execution_methods`;
3. selects one method using ASTV-owned area and domain preference;
4. selects the endpoint for that method; and
5. passes the record, selected method, and selected endpoint through the ASTV
   dispatcher.

If MediaCat lookup fails, ASTV stops before method and endpoint selection in
accordance with the MediaCat item-lookup failure contract.

### Current `ha_mplayer` branch

The dispatcher passes `request`, `selected_endpoint`, `execution_method`, and
`media_record` to the ASTV HA Media Player path. The ASTV AdvMedia adapter maps:

| Internal ASTV value | ASTV–AdvMedia v2 field |
| --- | --- |
| `media_record` | `media_record` |
| `execution_method` | `selected_execution_method` |
| `selected_endpoint.media_entity` | `media_player` |
| an explicit non-blank ASTV profile override, when present | `media_profile` |

The cross-product handoff and its failure behaviour are defined in the
provider-owned `ASTV_ADVMEDIA_INTERFACE.md` recorded in
`PROJECT_PROFILE.md`. AdvMedia returns the full contracted result mapping; the
ASTV adapter extracts `playback_payload`, and ASTV performs the final
`media_player.play_media` call.

### Current `g_home_device` branch

The dispatcher passes the complete `media_record`, `execution_method`, and
`selected_endpoint` through the ASTV-owned Google Home execution path. That path
reads:

`media_record.execution_methods[execution_method].source`

For `g_home_device`, the selected source must be `assistant_command`. ASTV uses
its `provider`, `command`, and `append_target` fields to construct the final
command. If `append_target` is `true`, ASTV appends the independently selected
endpoint's usable target phrase. ASTV then executes the command.

This branch does not call AdvMedia. MediaCat does not select the endpoint or build
the final assistant command.

ASTV stops the branch with an explicit error when:

- `g_home_device` is absent from `media_record.execution_methods`;
- the selected source is not `assistant_command`;
- the source's `provider` is unsupported by the ASTV Google Home path;
- the source cannot supply its `command`; or
- `append_target` is `true` but the selected endpoint has no usable target
  phrase.

ASTV sends no assistant command, does not call AdvMedia, and does not
automatically select another method or source after any of these failures. These
are minimum execution-boundary failures, not broader catalogue validation rules.

### Cutover and retained pre-cutover history

The deployed v1 media path remained current until the separately authorised
media implementation and ASTV-65 cross-product proof completed. The routine path
remained unchanged. After that proof, the complete v2 media flow became current;
the former v1 media branches remain visible only as inactive implementation
history. They are not a current interface, rollback contract, or compatibility
guarantee.

Implementation is divided across:

- [ASTV-60](https://linear.app/83degrees/issue/ASTV-60/update-astv-media-intent-engine-for-mediacat-lookup-and-method-selection) — MediaCat lookup and ASTV method selection;
- [ASTV-61](https://linear.app/83degrees/issue/ASTV-61/implement-astv-execution-dispatch-media-context-changes) — installed inactive media context transport through the dispatcher and receiving declarations;
- [ASTV-62](https://linear.app/83degrees/issue/ASTV-62/update-astv-ha-media-player-path-for-normalized-mediacat-handoff) — installed inactive HA Media Player and AdvMedia v2 handoff;
- [ASTV-63](https://linear.app/83degrees/issue/ASTV-63/update-astv-google-home-media-path-for-mediacat-execution-data) — installed inactive ASTV-owned Google Home command path;
- [ASTV-64](https://linear.app/83degrees/issue/ASTV-64/migrate-astv-media-intent-records-to-method-neutral-mediacat) — migration of ASTV media intents after proof; and
- [ASTV-65](https://linear.app/83degrees/issue/ASTV-65/prove-and-coordinate-mediacat-v3-cross-product-cutover) — coordinated cross-product proof and cutover.

The central registry describes the deployed current v2 dispatcher. Registry,
manifest, index, and governance-validation activation completed using ASTV-65
cutover evidence through
[ASTV-69](https://linear.app/83degrees/issue/ASTV-69/governance-cr-activate-mediacat-contracts-in-the-central-registry-at).

## Current Caller Topology and Retained Historical Branches

`script.astv_select_intent_engine` identifies the intent path and invokes
exactly one intent engine. The active normalized Media outcome captures the
complete response as `intent_response`, including `media_record`; the unchanged
Routine outcome captures the four-field response without `media_record`. The
exclusive `Intent?` choice then finishes, forming a control-flow merge only; no
consolidator or transformation script is introduced.

After the choice, Select Intent Engine invokes
`script.astv_select_execution_engine` exactly once with one mapping containing
the four current values and, only when supplied by the selected response, the
complete `media_record`. Select Intent Engine is therefore the single active
production caller of the dispatcher. An unknown intent creates a persistent
notification and stops with `error: true` before the shared Phase 3 call.

Routine-trigger resolution remains inside
`script.astv_g_automation_engine` and `script.astv_find_routine_trigger` Phase 3
flow.

The live Media Intent Engine, dispatcher, HA Media Player Engine, Google Home
Device Engine, and Google Assist provider still contain conditional
pre-cutover shapes used before ASTV-65. They are delimited from the current
contract by all of the following production facts:

- all active media records contain normalized MediaCat references and do not
  contain `params.sources`;
- every current Media response and dispatcher call carries `media_record`;
- `script.astv_adapter_advmedia` is v2-only after ASTV-76; and
- the retained Handle Provider AdvMedia outcome still supplies the removed
  `media_catalogue` / `media_item_id` shape and therefore is not a supported
  fallback through the current adapter.

The unchanged four-field Routine response remains current and must not be
misclassified as a v1 media interface merely because it shares four field names
with the historical Media response.

## Change Control

Adding an intent or execution method, changing an input or output name or type,
introducing a common execution response, or changing the exclusive merge and
single-dispatch ownership requires a coordinated production, contract, and
architecture update.
