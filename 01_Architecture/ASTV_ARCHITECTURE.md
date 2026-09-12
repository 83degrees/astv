# ASTV Architecture

## Purpose and Sources of Truth

This document records the verified semantic architecture of ASTV: its active components, phase ownership, calls, returned values, data dependencies, gateways, and external actions.

The governed diagram at `Diagrams/ASTV_ARCHITECTURE.drawio` represents this
semantic architecture and preserves its visual structure and phase layout. This
document is authoritative for semantic architecture and dependencies. Verified
live Home Assistant YAML/configuration establishes deployed/runtime facts only,
including current entity IDs, inputs, response variables, and service calls.
Legacy or unused scripts are not part of the current architecture merely because
they remain in YAML.

## Architecture Status and Timeframes

The end-to-end flow and phase descriptions below are **current production**.
The normalized MediaCat media flow became current after `ASTV-65` proof at
`2026-08-24T20:09:37.490Z` and was reverified through read-only live Home
Assistant configuration inspection on 2026-08-25.

The active `Diagrams/ASTV_ARCHITECTURE.drawio` file is the verified post-cutover
current-production visual updated under `ASTV-78`, with SHA-256
`AF97914C1EBB7187F7DA1966E94C9165F57148735FC57D06A4BD36384004315E`.
Its static and structural validation and final user review at normal and
overview zoom were completed and accepted under `ASTV-78`. The exact original
pre-change visual remains recoverable from Git history at the T1 baseline path
`01_Architecture/Archive/ASTV_Architecture_pre_ASTV-78_2026-08-25.drawio`.

The normalized flow is defined by the applicable provider-owned contracts
recorded in `00_Governance/PROJECT_PROFILE.md`. `ASTV-60` installed the
compatibility-safe MediaCat lookup and selection branch inside
`script.astv_intent_engine_media`. `ASTV-61` installed the conditional
five-field handoff through Select Intent Engine and Select Execution Engine and
the receiving declarations on both media engines. `ASTV-62` installed the HA
Media Player consumer and transitional dual-shape AdvMedia adapter, and
`ASTV-63` installed the Google Home Device consumer and dual-shape Google Assist
provider. `ASTV-64` prepared and non-live tested the replacement catalogue and
byte-identical rollback bundle. `ASTV-65` activated all seven normalized media
records, the schema-v3 MediaCat lookup, and both consumers coherently.

The live definitions still contain several no-`media_record` pre-cutover
branches. They are retained implementation history, not the current media
interface or a promised fallback: all active media records select the normalized
branch. `ASTV-76` also removed the v1 shape from the ASTV AdvMedia adapter, so
the retained Handle Provider AdvMedia call no longer matches that boundary. The
only current ASTV-to-AdvMedia boundary is normalized v2. `ASTV-200` replaces the
internal Phase 2-to-Phase 3 handoff with the fixed three-context dispatch
interface described below; downstream execution-engine interfaces remain
unchanged. The durable rationale is recorded in `DDR-01-001`.

## End-to-End Flow

The lifecycle moves left-to-right through four phase bands. The active NFC path enters through external NFC input, reaches the configured reader sensors over MQTT, and passes through Tag Listener and UID Gateway before all subsequent ASTV processing continues through Intent Gateway.

1. Phase 0 receives the external NFC input through the MQTT-fed reader sensors and resolves the tag UID to its canonical `intent_id`.
2. Phase 1 looks up the intent catalogue record and resolves the target area through Intent Gateway.
3. Phase 2 selects the request intent. Media resolves the playback method and selected endpoint; Routine selects Google Automation. The selected intent engine constructs the complete three-context dispatch payload and calls Select Execution Engine directly.
4. Phase 3 dispatches one of the two Media execution methods or the Google Automation flow.

The current intent outcomes are `Media` and `Routine`. The current playback-engine outcomes are `HA Media Player` and `Google Home Device`.

## Phase 0 — NFC Entry and Tag-to-Intent Resolution

### External NFC Input and Reader Sensors

An external NFC read is delivered over MQTT to one of the configured Home Assistant reader sensors:

- `sensor.pi_nfc_02_last_uid`
- `sensor.pi_nfc_99_last_uid`

A state change on either sensor is evaluated by ASTV - Tag Listener. Only a valid UID-bearing new state enters the ASTV pipeline; new states that are unknown, unavailable or blank are ignored before UID Gateway invocation.

### ASTV - Tag Listener

- Entity: `automation.astv_tag_listener`
- Sources:
  - `sensor.pi_nfc_02_last_uid`
  - `sensor.pi_nfc_99_last_uid`
- Ignores a state change when the new state is unknown, unavailable or blank.
- Calls `script.astv_uid_gateway` only when the new state passes that validity guard, with:
  - `uid`
  - `trigger_entity`

No other NFC reader sensors are part of the current listener architecture.

### ASTV - UID Gateway

- Entity: `script.astv_uid_gateway`
- Inputs:
  - `uid`
  - `trigger_entity` (default `sensor.pi_nfc_99_last_uid`)
- Calls `script.astv_find_tag_record` with:
  - `uid`
- Captures the result as:
  - `tag_record_response`
- Stops with `No Tag Record Found` when the lookup is empty.
- Stops with `Invalid Tag Record` when `intent_id` is absent or blank.
- On success, temporarily creates `Tag Record Found` with UID, trigger entity, resolved intent ID, and optional tag area override.
- Calls `script.astv_intent_gateway` with:
  - `intent_id` from `tag_record_response.intent_id`
  - `trigger_area_override` from optional `tag_record_response.area_override`
  - `trigger_entity`

UID Gateway does not resolve the catalogue request or area itself and does not call Select Intent Engine directly.

#### ASTV - Fn: Find Tag Record

- Entity: `script.astv_find_tag_record`
- Input: `uid`
- Return: `tag_record_response`
- Data dependency:
  - ASTV Tag Mapping
  - `astv_tag_mapping.yaml`

The function normalizes the supplied UID using string conversion, trimming, and uppercasing, then performs an exact mapping lookup. It returns `{}` for an unknown UID and remains side-effect-free.

## Phase 1 — Intent-Catalogue Lookup and Target-Area Resolution

### ASTV - Intent Gateway

- Entity: `script.astv_intent_gateway`
- Friendly name: `ASTV - Intent Gateway`
- Inputs:
  - `intent_id` (required)
  - `trigger_area_override` (optional)
  - `trigger_entity` (optional)
- Return: none

It calls `script.astv_find_intent_record` with `intent_id` and captures the exact return as `intent_record_response`. An empty result creates a persistent notification titled `No Intent Record Found` and stops before area resolution.

For a resolved record, Intent Gateway separately calls `script.astv_resolve_area` with:

- `trigger_area_override` from the gateway input
- `intent_area_override` from the record's optional `area_override`
- `trigger_entity` from the gateway input

It captures `area_response`, derives `target_area`, and stops with a persistent notification if the area is unresolved. After successful resolution it calls `script.astv_select_intent_engine` with only:

- `request` (the complete `intent_record_response`)
- `target_area`

`intent_id`, `trigger_area_override`, and `trigger_entity` are not passed downstream. Find Intent Record and Resolve Area are independent children of Intent Gateway; neither calls the other.

#### ASTV - Fn: Find Intent Record

- Entity: `script.astv_find_intent_record`
- Input: `intent_id`
- Return: `intent_record_response`
- Data dependency:
  - ASTV Intent Catalogue
  - `astv_intent_catalogue.yaml`

The function normalizes the supplied ID using string conversion, trimming, and lowercasing. It uses the normalized `lookup_intent_id` as the exact ASTV Intent Catalogue lookup input and returns the lookup result as `intent_record_response`. It returns `{}` for an unknown ID and remains side-effect-free.

#### ASTV - Fn: Resolve Area

- Entity: `script.astv_resolve_area`
- Inputs:
  - `trigger_area_override` (optional)
  - `intent_area_override` (optional)
  - `trigger_entity`
- Return: `area_response`

`target_area` is resolved using this precedence: non-blank `trigger_area_override`, non-blank `intent_area_override`, `area_id(trigger_entity)`, then an empty value when unresolved. The resolver is side-effect-free.

## Phase 2 — Intent Routing

### ASTV - Select Intent Engine

- Entity: `script.astv_select_intent_engine`
- Inputs:
  - `request`
  - `target_area`
- Exclusive decision: `Intent?`
- Current outcomes:
  - `Media`
  - `Routine`

The `Routine` outcome originates here. It does not originate from Intent Engine:
Media. Select Intent Engine invokes exactly one intent engine and performs no
response capture, payload reconstruction, or execution dispatch of its own. An
unknown intent stops visibly inside the choice.

### Media Outcome: ASTV - Intent Engine: Media

- Entity: `script.astv_intent_engine_media`
- Inputs:
  - `request`
  - `target_area`
- Dispatches directly to `script.astv_select_execution_engine` with:
  - `intent_context.record`: the unchanged `request`
  - `intent_context.data.media_record`: the complete unchanged normalized MediaCat response
  - `target_context.area`: the unchanged `target_area`
  - `target_context.endpoint`: the selected area playback endpoint
  - `execution_context.engine`: the resolved playback method

The live definition reads `catalogue_id`, `item_id`, and `output.domain`
directly from `request.params`. It normalizes the two MediaCat identifiers for
branch selection using string conversion, defaulting, and trimming:

- when neither identifier is non-blank, it enters a retained pre-cutover branch
  that reads `request.params.sources` and returns the older four-field media
  response without `media_record`;
- when exactly one identifier is non-blank, it creates one persistent
  notification identifying the incomplete reference and stops with
  `error: true`; and
- when both identifiers are non-blank, the current normalized branch calls
  `curated_media.resolve_media_record` once, captures the complete result as
  `media_record_response`, and uses its complete `execution_methods` mapping
  for ASTV-owned method selection.

All seven active media intent records contain both MediaCat identifiers and no
`params.sources`. Each current request therefore selects the normalized branch,
performs one lookup, and carries the complete result through one execution-method
selection. The pre-cutover branch remains configured but is not selected by
those records.

The current normalized branch calls the three sibling support functions below
after its single MediaCat lookup. The retained pre-cutover branch calls the same
functions against `request.params.sources`. Their execution order does not imply
calls between the functions.

#### ASTV - Fn: Find Area Domain Endpoints

- Entity: `script.astv_find_area_domain_endpoints`
- Inputs:
  - `domain`
  - `area`
- Return: `area_domain_response`
- Data dependency:
  - Area Endpoints
  - `astv_area_endpoints2.yaml`

#### ASTV - Fn: Resolve Playback Method

- Entity: `script.astv_resolve_playback_method`
- Inputs:
  - `preferences`
  - `available_sources`
- Return: `playback_method_response`

#### ASTV - Fn: Select Area Playback Endpoint

- Entity: `script.astv_select_area_playback_endpoint`
- Inputs:
  - `area_playback_domain`
  - `playback_method`
- Return: `area_playback_endpoint_response`

Intent Engine: Media derives two separately named values from the one-key
`area_playback_endpoint_response`:

- `execution_method` from its key
- `selected_endpoint` from the value for that key

The current normalized branch places those values together with the unchanged
`request`, `target_area`, and complete unchanged `media_record_response` into
the fixed three-context interface and calls Select Execution Engine directly.
It does not flatten the record, remove unselected methods, or add an internal
`selected_execution_method`.

### Routine Outcome: ASTV - Intent Engine: Routine

- Entity: `script.astv_intent_engine_routine`
- Inputs:
  - `request`
  - `target_area`
- Dispatches directly to `script.astv_select_execution_engine` with:
  - `intent_context.record`: the unchanged `request`
  - `intent_context.data: {}`
  - `target_context.area`: the unchanged `target_area`
  - `target_context.endpoint: {}`
  - `execution_context.engine: g_automation`

The engine does not resolve the routine trigger. Its only execution-side effect
is invoking the execution selector with the complete fixed-shape context.

## Phase 3 — Execution

### ASTV - Select Execution Engine

- Entity: `script.astv_select_execution_engine`
- Inputs:
  - `intent_context`
    - `record`
    - `data`
  - `target_context`
    - `area`
    - `endpoint`
  - `execution_context`
    - `engine`
- Common response: none
- Exclusive decision: `Execution Method?`
- Current implemented outcomes:
  - `HA Media Player` (`ha_mplayer`)
  - `Google Home Device` (`g_home_device`)
  - `Google Automation` (`g_automation`)

All three top-level objects and their inner keys are mandatory. `data` and
`endpoint` remain present as `{}` when unused. Select Execution Engine adapts
this boundary to the unchanged downstream execution-engine inputs. All three
implemented execution engines receive `intent_context.record` as their existing
`request`; Media engines also receive `target_context.endpoint`,
`execution_context.engine`, and `intent_context.data.media_record`. Google
Automation receives `target_context.area`. The dispatcher validates
`target_context.endpoint.media_entity` for `ha_mplayer` and
`target_context.endpoint.phrase` for `g_home_device`. A missing endpoint or a blank
or unsupported method creates a persistent notification and stops the run as
failed before any downstream engine is called.

For `g_automation`, the dispatcher validates non-blank
`intent_context.record.routine` and `target_context.area`, then calls
`script.astv_g_automation_engine` with those values mapped back to its existing
`request` and `target_area` inputs. `target_context.endpoint` is intentionally
empty and unused for this method. A blank
Routine value or blank Routine target area creates a persistent notification
and stops the run as failed before Google Automation is called.

The dispatcher returns no common data response.

### HA Media Player Branch

#### ASTV - HA Media Player Engine

- Entity: `script.astv_ha_mplayer_engine`
- Inputs:
  - `request`
  - `selected_endpoint`
  - `execution_method`, required on the current Media path
  - `media_record`, required on the current Media path
- Calls
  `script.astv_adapter_advmedia` directly with:
  - complete `media_record`
  - `selected_execution_method`, mapped from `execution_method`
  - selected `media_player`
- Captures the provider result as:
  - `provider_payload_response`
- Terminal action:
  - `media_player.play_media`

The live field declarations remain optional so the script can retain its
pre-cutover no-context branch, but the two context values are a required pair on
every current Media call. A partial pair stops before any downstream call. An
adapter or AdvMedia failure does not select the retained branch as fallback.

#### ASTV - Adapter: AdvMedia

- Entity: `script.astv_adapter_advmedia`
- Inputs from the HA Media Player engine:
  - complete `media_record`
  - `selected_execution_method`
  - `media_player`
- Optional:
  - `media_profile`
- Adapter return:
  - `payload_response`

The adapter calls `script.advmedia_process_media_record` exactly once with the
complete normalized record, selected method, player, and optional profile. It
contains no catalogue lookup, method or endpoint selection, fallback, or call to
`script.advmedia_prepare_playback`.

The external subsystem returns `advmedia_response` to the adapter.
`advmedia_response` is the subsystem result; `payload_response` is the adapter
result consumed by the HA Media Player engine under its separately named caller
capture variable. These names are distinct and must not be normalised.

The AdvMedia subsystem is an external boundary. Its internal preparation
scripts, record lookup, profile handlers, and provider-specific implementation
details are intentionally excluded from ASTV architecture documentation.

#### Retained Pre-Cutover Provider Branch — Historical / Inactive

The HA Media Player Engine still contains a no-context branch that calls
`script.astv_handle_provider` with `request_object` and `media_player`. No active
media record selects this branch after ASTV-65.

##### ASTV - Fn: Handle Provider

- Entity: `script.astv_handle_provider`
- Inputs:
  - `request_object`
  - `media_player`
- Return to HA Media Player Engine:
  - `provider_payload_response`
- Exclusive provider outcomes:
  - `Radio Browser`
  - `AdvMedia`

This component is not part of the current production media flow. Its retained
AdvMedia outcome still supplies the retired `media_catalogue` / `media_item_id`
shape to the now v2-only adapter, so it is not a supported fallback path.

##### Retained Radio Browser Provider

- Component: ASTV - Fn: Provider - Radio Browser
- Entity: `script.astv_provider_radiobrowser`
- Input: `provider_data_object`
- Return: `provider_payload_response`

### Google Home Device Branch

#### ASTV - Google Home Device Engine

- Entity: `script.astv_g_home_device_engine`
- Inputs:
  - `request`
  - `selected_endpoint`
  - `execution_method`, required on the current Media path
  - `media_record`, required on the current Media path
- Reads only
  `media_record.execution_methods[execution_method].source`, validates the
  `assistant_command` source and `google_assistant` provider, and calls
  `script.astv_provider_g_assist` with:
  - `assistant_source`
  - `endpoint_phrase`
- A partial context pair, unusable selected source, unsupported provider,
  missing command, or required but unusable endpoint phrase stops explicitly
  before the terminal action.
- Captures the provider result as:
  - `provider_command_response`
- Terminal action:
  - `google_assistant_sdk.send_text_command`
- Command source:
  - `provider_command_response.command`

This branch does not output to a Home Assistant media player. The normalized
branch reaches the one Google Assistant SDK action. The live definition retains
a pre-cutover no-context branch that supplies `intent`, `request_object`, and
`endpoint_phrase` to the provider, but no active media record selects it.

#### ASTV - Provider: Google Assist

- Entity: `script.astv_provider_g_assist`
- Current input shape:
  - `assistant_source`
  - `endpoint_phrase`
- Retained pre-cutover input shape (historical / inactive):
  - `intent`
  - `request_object`
  - `endpoint_phrase`
- Return to Google Home Device Engine:
  - `provider_command_response`
- Command-builder split: `Select Command Builder?`
- Current implemented outcome: `Media`

##### ASTV - Command Builder: Media

- Entity: `script.astv_cmd_builder_media`
- Inputs:
  - `phrase`
  - `append_target`
  - `endpoint_phrase`
- Return: `command_response`

The command-builder exclusive split and merge gateways represent control flow only. They are not scripts or functions, and the merge does not transform `command_response` or imply a consolidator.

### Routine / Google Automation Branch

The Routine branch reaches this Phase 3 region through the shared execution
dispatcher's `g_automation` outcome. Select Intent Engine initiates dispatch
once after the Phase 2 `choose` has closed.

#### ASTV - Google Automation Engine

- Entity: `script.astv_g_automation_engine`
- Inputs:
  - `request`
  - `target_area`
- Calls `script.astv_find_routine_trigger` with:
  - `routine` from `request.routine`
  - `target_area`
- Captures the result as:
  - `trigger_response`
- Action:
  - `input_boolean.turn_on`
- Target:
  - `trigger_response.entity_id`

#### ASTV - Fn: Find Routine Trigger

- Entity: `script.astv_find_routine_trigger`
- Inputs:
  - `routine`
  - `target_area`
- Return: `trigger_response`
- Home Assistant metadata/registry dependency:
  - area: `target_area`
  - label: `routine_<routine>`
  - label: `matter_gh_trigger`

The lookup is dynamic and uses Home Assistant area and label metadata. There is no static YAML routine-to-trigger lookup matrix.

After the engine turns on the resolved Matter-exposed `input_boolean`, a Google Home automation reacts to the helper state:

`Matter-exposed input_boolean` → `Google Home automation`

The Google Automation Engine does not call the Google Home automation directly.

## Current Normalized Media Architecture

The current normalized architecture is governed by:

- provider-owned `MEDIACAT_ITEM_LOOKUP_INTERFACE.md`, at the authoritative
  location recorded in `00_Governance/PROJECT_PROFILE.md`, for the normalized MediaCat lookup
  and returned record;
- `../03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` for ASTV's internal media
  context and execution branches; and
- provider-owned `ASTV_ADVMEDIA_INTERFACE.md`, at the authoritative location
  recorded in `00_Governance/PROJECT_PROFILE.md`, for the ASTV-to-AdvMedia handoff.

Those contracts remain the single sources for exact fields, record structure,
presence promises, and failure behaviour. This narrative describes ASTV's
responsibilities and flow without restating their schemas.

### ASTV ownership and selection

For a media request, ASTV obtains the complete normalized record from MediaCat
before selecting an execution method or endpoint. MediaCat supplies every
available method and its source facts; ASTV applies its area/domain preference,
selects one method, and selects the endpoint for that method.

ASTV continues to own fallback policy. This migration cycle does not add
automatic retry or failover after lookup, method processing, command construction,
or execution fails. A failed selected path stops according to the applicable
contract; choosing another method or source remains future refinement.

### Record preservation and dispatch

ASTV passes the complete normalized MediaCat record unchanged through the selected
media execution path. It does not remove unselected methods or write its selection
into the MediaCat record. The existing internal `execution_method` remains the
ASTV-selected method, carried separately from `media_record`; a duplicate
`selected_execution_method` field is not added to the internal dispatcher
boundary. The ASTV boundary adapter uses the separately named
`selected_execution_method` only where required by the cross-product AdvMedia
contract.

The current media intent engine carries the normalized record in
`intent_context.data.media_record`, with the selected method in
`execution_context.engine` and the resolved target in `target_context`. The
Routine path uses the same fixed shape, with empty `data` and `endpoint`
objects.

### Current HA Media Player path

For `ha_mplayer`, ASTV passes the complete record, selected method, and selected
media-player endpoint into its AdvMedia boundary adapter. The adapter supplies
the normalized record directly to the new AdvMedia processing core and maps
ASTV's selected method to the separately named cross-product selection context.
ASTV may also supply a non-blank explicit profile override; otherwise AdvMedia
resolves the profile under its own rules. Endpoint selection remains ASTV-owned,
profile resolution remains AdvMedia-owned, and MediaCat owns neither.

AdvMedia returns its complete contracted result. The ASTV adapter extracts the
prepared playback payload for the HA Media Player engine, and ASTV performs the
final `media_player.play_media` call.

### Current Google Home Device path

For `g_home_device`, ASTV carries the complete record, selected method, and
selected assistant endpoint through its own execution branch. It reads the
selected method's `assistant_command` source facts, validates the provider,
constructs the final command, appends the independently selected target phrase
when directed, and invokes `google_assistant_sdk.send_text_command` directly.

This branch does not call AdvMedia and has no media-player profile. MediaCat
supplies item-specific source facts but does not select the endpoint, construct the
final command, or invoke the assistant SDK.

### Current standalone AdvMedia MediaCat gateway

ASTV-67 replaced the standalone compatibility shape with an AdvMedia-owned
MediaCat gateway whose caller supplies the catalogue reference, already selected
execution method, and media-player endpoint. The gateway resolves the record
once and calls the shared core once. It is separately contracted in the
AdvMedia-owned `ADVMEDIA_MEDIACAT_GATEWAY_INTERFACE.md`.

The retired `script.advmedia_find_media_record` wrapper is absent from current
source and live Home Assistant after explicit user approval and post-removal
proof. This change does not alter the current ASTV adapter or any ASTV method,
endpoint, fallback, or playback responsibility. A normal ASTV v2 Classic FM
request passed after retirement without calling the standalone gateway.

`ASTV-65` proved the full normalized flow current end to end. Seven sequential
UID requests each performed exactly one lookup and one method selection before
one terminal action; all produced clean traces and logs and audible user
confirmation. The ASTV-65 operational rollback window is closed; its historical
evidence remains available through Linear and Git history. The active Draw.io
bytes are the accepted current-production visual completed and reviewed under
`ASTV-78`.

## Gateway Semantics

- Exclusive split gateways represent genuine routing decisions with one incoming flow and mutually exclusive outgoing outcomes.
- Exclusive merge gateways represent convergence only. They are not scripts or functions, do not transform data, and do not imply a consolidator.
- Parallel gateways are used only when the architecture genuinely requires parallel execution and/or synchronisation.
- Gateway outcome labels describe routing outcomes and are not components.

## External and Data Dependencies

| Dependency | Type | Consumer or relationship |
|---|---|---|
| External NFC input | External input | Delivered over MQTT to the configured NFC reader sensors |
| `sensor.pi_nfc_02_last_uid`, `sensor.pi_nfc_99_last_uid` | MQTT-fed Home Assistant sensors | Valid UID-bearing state-change inputs evaluated by ASTV - Tag Listener; unknown, unavailable or blank new states are ignored before UID Gateway |
| `astv_tag_mapping.yaml` | Data source | Active Find Tag Record lookup |
| `astv_intent_catalogue.yaml` | Data source | Find Intent Record lookup using `lookup_intent_id`; result `intent_record_response` |
| `astv_area_endpoints2.yaml` | Data source | Find Area Domain Endpoints |
| Home Assistant metadata / registry | Dynamic data source | Find Routine Trigger |
| AdvMedia subsystem | External subsystem | Reached through ASTV - Adapter: AdvMedia |
| `media_player.play_media` | External action | HA Media Player Engine |
| `google_assistant_sdk.send_text_command` | External action | Google Home Device Engine |
| Matter-exposed `input_boolean` | External/Home Assistant entity | Turned on by Google Automation Engine |
| Google Home automation | External automation | Reacts to the Matter-exposed helper |

## Interface Naming and Return Boundaries

Exact verified names must be preserved. In particular:

- `lookup_intent_id`
- `intent_record_response`
- `request`
- `execution_method`
- `selected_endpoint`
- `area_response`
- `area_domain_response`
- `playback_method_response`
- `area_playback_endpoint_response`
- `provider_payload_response`
- `payload_response`
- `advmedia_response`
- `command_response`
- `provider_command_response`
- `trigger_response`
- `intent_context`
- `target_context`
- `execution_context`

A caller's `response_variable` name describes how that caller captures a result. A child's returned payload name describes the child's own interface. Do not rename either for visual or documentary consistency, and do not collapse names across adapter/provider boundaries.

## Retained Historical and Excluded Components

The following scripts or branches remain configured but are not current
architecture components unless a verified active dependency is added in the
future:

- `script.astv_resolver`
- `script.astv_resolver_v2`
- `script.astv_sound_tag_feedback`
- `script.astv_handle_provider`
- `script.astv_provider_radiobrowser`
- the no-`media_record` branch in `script.astv_intent_engine_media`
- the no-context media branches in `script.astv_select_execution_engine`,
  `script.astv_ha_mplayer_engine`, and `script.astv_g_home_device_engine`
- the legacy input branch in `script.astv_provider_g_assist`

Their presence in live configuration does not make them part of the current
ASTV flow. In particular, the retained Handle Provider AdvMedia call uses
fields removed from the v2-only adapter and is not a supported fallback.
