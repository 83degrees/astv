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

The end-to-end flow and phase descriptions below describe the current approved
ASTV architecture. The normalized MediaCat media flow is current, and the HA
Media Player Engine calls the AdvMedia core directly through the provider-owned
AdvMedia interface. Historical migration states remain recoverable through
Linear and Git history and are not described here as current architecture.

Following the completed MediaCat namespace retirement, ASTV reaches the
normalized lookup only through `mediacat.resolve_media_record`. The former
`curated_media.*` Home Assistant action namespace is not part of the current
architecture and is not an available runtime rollback surface.

The current normalized flow is governed by the provider-owned contracts
recorded in `00_Governance/PROJECT_PROFILE.md`, the ASTV execution-dispatch
contract, and `DDR-01-001` for the fixed three-context internal dispatch
rationale.

## End-to-End Flow

The lifecycle moves left-to-right through four phase bands. The active NFC path enters through external NFC input, reaches the configured reader sensors over MQTT, and passes through Tag Listener and UID Gateway before all subsequent ASTV processing continues through Intent Gateway.

1. Phase 0 receives the external NFC input through the MQTT-fed reader sensors and resolves the tag UID to its canonical `intent_id`.
2. Phase 1 looks up the intent catalogue record and resolves the target area through Intent Gateway.
3. Phase 2 selects the request intent. Media resolves the playback method and selected endpoint; Routine selects Google Automation. The selected intent engine constructs the complete three-context dispatch payload and calls Select Execution Engine directly.
4. Phase 3 routes the unchanged three-context payload to one of the two Media
   execution engines or the Google Automation engine. The selected engine owns
   its context extraction and validation.

The current intent outcomes are `Media` and `Routine`. The current playback-engine outcomes are `HA Media Player` and `Google Home Device`.

## Phase 0 — NFC Entry and Tag-to-Intent Resolution

### External NFC Input and Reader Sensors

An external NFC read is delivered over MQTT to one of the configured Home Assistant reader sensors:

- `sensor.pi_nfc_02_last_uid`
- `sensor.pi_nfc_99_last_uid`

A state change on either sensor is evaluated by ASTV - Tag Listener. State transitions to or from `unknown` or `unavailable` are excluded at the Home Assistant trigger boundary before UID Gateway invocation.

### ASTV - Tag Listener

- Entity: `automation.astv_tag_listener`
- Sources:
  - `sensor.pi_nfc_02_last_uid`
  - `sensor.pi_nfc_99_last_uid`
- Excludes state transitions to or from `unknown` or `unavailable` at the Home Assistant trigger boundary.
- Calls `script.astv_uid_gateway` for each remaining state change, with:
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
  - `input_area_override` from optional `tag_record_response.area_override`
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
  - `input_area_override` (optional)
  - `trigger_entity` (optional)
- Return: none

It calls `script.astv_find_intent_record` with `intent_id` and captures the exact return as `intent_record_response`. An empty result creates a persistent notification titled `No Intent Record Found` and stops before area resolution.

For a resolved record, Intent Gateway separately calls `script.astv_resolve_area` with:

- `input_area_override` from the gateway input
- `intent_area_override` from the record's optional `area_override`
- `trigger_entity` from the gateway input

It captures `area_response`, derives `target_area`, and stops with a persistent notification if the area is unresolved. After successful resolution it calls `script.astv_select_intent_engine` with only:

- `intent_record` (the complete `intent_record_response`)
- `target_area`

`intent_id`, `input_area_override`, and `trigger_entity` are not passed downstream. Find Intent Record and Resolve Area are independent children of Intent Gateway; neither calls the other.

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
  - `input_area_override` (optional)
  - `intent_area_override` (optional)
  - `trigger_entity`
- Return: `area_response`

`target_area` is resolved using this precedence: non-blank `input_area_override`, non-blank `intent_area_override`, `area_id(trigger_entity)`, then an empty value when unresolved. The resolver is side-effect-free.

## Phase 2 — Intent Routing

### ASTV - Select Intent Engine

- Entity: `script.astv_select_intent_engine`
- Inputs:
  - `intent_record`
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
  - `intent_record`
  - `target_area`
- Dispatches directly to `script.astv_select_execution_engine` with:
  - `intent_context.record`: the unchanged `intent_record`
  - `intent_context.data.media_record`: the complete unchanged normalized MediaCat response
  - `target_context.area`: the unchanged `target_area`
  - `target_context.endpoint`: the selected area playback endpoint
  - `execution_context.engine`: the resolved playback method

The live definition reads `catalogue_id`, `item_id`, and `output.domain`
directly from `intent_record.params`. It normalizes the two MediaCat identifiers
using string conversion, defaulting, and trimming.

- when exactly one identifier is non-blank, it creates a persistent notification
  identifying the incomplete reference and stops with `error: true`;
- when both identifiers are blank, it creates a persistent notification
  identifying the missing MediaCat reference and stops with `error: true`; and
- when both identifiers are non-blank, it calls
  `mediacat.resolve_media_record` once, captures the complete result as
  `media_record_response`, and uses its complete `execution_methods` mapping for
  ASTV-owned method selection.

All seven active media intent records use `catalogue_id: curated_media` as the
logical MediaCat catalogue identity. That value does not identify a Home
Assistant integration/action namespace and remains unchanged after retirement
of the former `curated_media.*` runtime surface.

After the MediaCat lookup, ASTV calls
`script.astv_find_area_domain_endpoints`. If the returned area/domain playback
configuration is empty or has no usable `preference` list, the Media Intent
Engine creates `ASTV - Missing Playback Configuration` and stops before
playback-method resolution.

ASTV then calls `script.astv_resolve_playback_method`. That function preserves
configured preference order and selects the first preference present in the
available MediaCat execution methods. If no configured preference matches, it
creates `ASTV - No Compatible Playback Method` and stops before evaluating
`matching_sources | first`.

On successful method resolution, ASTV selects the endpoint for that method and
dispatches the unchanged normalized MediaCat record, selected target and
selected method through the fixed three-context interface.

The three support functions below are siblings called by Intent Engine: Media.
Their execution order does not imply calls between the functions.

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

Intent Engine: Media places those values together with the unchanged
`intent_record`, `target_area`, and complete unchanged `media_record_response`
into the fixed three-context interface and calls Select Execution Engine directly.
It does not flatten the record, remove unselected methods, or add an internal
`selected_execution_method`.

### Routine Outcome: ASTV - Intent Engine: Routine

- Entity: `script.astv_intent_engine_routine`
- Inputs:
  - `intent_record`
  - `target_area`
- Dispatches directly to `script.astv_select_execution_engine` with:
  - `intent_context.record`: the unchanged `intent_record`
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
`endpoint` remain present as `{}` when unused. Select Execution Engine is a pure
router: it routes only on `execution_context.engine`, passes all three context
objects unchanged, and rejects a blank or unsupported engine. Engine-specific
extraction and validation belong to the selected execution engine.

The dispatcher returns no common data response.

### HA Media Player Branch

#### ASTV - HA Media Player Engine

- Entity: `script.astv_ha_mplayer_engine`
- Inputs:
  - `intent_context`
  - `target_context`
  - `execution_context`
- Calls
  `script.advmedia_process_media_record` directly with:
  - complete `media_record`, extracted from `intent_context`
  - `execution_engine`, extracted from `execution_context`
  - selected `media_player`
- Captures the AdvMedia result as:
  - `advmedia_processed_response`
- Successful result field:
  - `playback_payload`
- Consumes only:
  - `advmedia_processed_response.playback_payload`
- Terminal action:
  - `media_player.play_media`

The engine extracts and validates the selected media-player entity and
normalized media record from the shared contexts. It supplies the complete
record, selected method, and selected player directly to the AdvMedia core,
which performs no catalogue lookup. An AdvMedia failure does not trigger an
alternative execution path.

The external subsystem returns a one-field successful result containing only
`playback_payload`. The engine captures that result as
`advmedia_processed_response` and consumes
`advmedia_processed_response.playback_payload` for the terminal action.
AdvMedia resolves the media profile internally but does not echo the selected
endpoint in its result: ASTV retains its own `media_player_entity` and uses that
ASTV-owned value as the terminal target.

The AdvMedia subsystem is an external boundary. Its internal preparation
scripts, record lookup, profile handlers, and provider-specific implementation
details are intentionally excluded from ASTV architecture documentation.

### Google Home Device Branch

#### ASTV - Google Home Device Engine

- Entity: `script.astv_g_home_device_engine`
- Inputs:
  - `intent_context`
  - `target_context`
  - `execution_context`
- Reads only
  `intent_context.data.media_record.execution_methods[execution_context.engine].source`,
  then selects a provider through an exclusive route on `source.provider`.
- Current implemented provider outcome:
  - `Google Assistant` (`google_assistant`)
- The Google Assistant route calls `script.astv_provider_g_assist` with:
  - `intent`, from `intent_context.record.intent`
  - `source`
  - `endpoint_phrase`
- A missing media record or unsupported provider stops explicitly before the
  terminal action. Source command and conditional endpoint validity belong to
  the selected command builder rather than this engine.
- Captures the provider result as:
  - `provider_response`
- Terminal action:
  - `google_assistant_sdk.send_text_command`
- Command source:
  - `provider_response.command`

This branch does not output to a Home Assistant media player. The selected
provider returns its command-builder response unchanged, and the engine owns
the one terminal Google Assistant SDK action. A failure does not trigger another
provider or execution method.

#### ASTV - Provider: Google Assist

- Entity: `script.astv_provider_g_assist`
- Inputs:
  - `intent`
  - `source`
  - `endpoint_phrase`
- Return to Google Home Device Engine:
  - `provider_response`
- Derives the command-builder family from the portion of `intent` before the
  first `.`.
- Command-builder split: `Intent Family?`
- Current implemented outcome: `media`
- Unsupported intent families stop explicitly.
- The provider selects the builder but does not validate or construct its
  command. It returns the selected builder response unchanged.

##### ASTV - Command Builder: Media

- Entity: `script.astv_cmd_builder_media`
- Inputs:
  - `phrase`
  - `append_target`
  - `endpoint_phrase`
- Return: `command_response`

The Media command builder is provider-agnostic. It owns final command
construction, rejects a blank `phrase`, requires a non-blank `endpoint_phrase`
only when `append_target` is true, and otherwise preserves supplied phrase and
endpoint values without trimming or normalization. When requested, it joins
the values with the exact text ` on `.

The command-builder exclusive split and merge gateways represent control flow only. They are not scripts or functions, and the merge does not transform `command_response` or imply a consolidator.

### Routine / Google Automation Branch

The Routine branch reaches this Phase 3 region through the shared execution
selector's `g_automation` outcome.

#### ASTV - Google Automation Engine

- Entity: `script.astv_g_automation_engine`
- Inputs:
  - `intent_context`
  - `target_context`
  - `execution_context`
- Calls `script.astv_find_routine_trigger` with:
  - `routine` extracted from `intent_context.record.routine`
  - `target_area` extracted from `target_context.area`
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

ASTV continues to own fallback policy. The current architecture does not provide
automatic retry or failover after lookup, method processing, command construction,
or execution fails. A failed selected path stops according to the applicable
contract; choosing another method or source remains future refinement.

### Record preservation and dispatch

ASTV passes the complete normalized MediaCat record unchanged through the selected
media execution path. It does not remove unselected methods or write its selection
into the MediaCat record. `execution_context.engine` remains the ASTV-selected
method, carried separately from `intent_context.data.media_record`; a duplicate
`selected_execution_method` field is not added to the internal dispatcher
boundary. The HA Media Player Engine supplies the selected method to AdvMedia
under the separately named cross-product field `execution_engine`, as
required by the provider-owned AdvMedia contract.

The current media intent engine carries the normalized record in
`intent_context.data.media_record`, with the selected method in
`execution_context.engine` and the resolved target in `target_context`. The
Routine path uses the same fixed shape, with empty `data` and `endpoint`
objects.

### Current HA Media Player path

For `ha_mplayer`, the ASTV HA Media Player Engine extracts the selected
media-player endpoint from `target_context`, passes the complete normalized
MediaCat record, selected execution engine, and selected media player directly
to `script.advmedia_process_media_record`, and captures the contracted result as
`advmedia_processed_response`. The successful result contains only
`playback_payload`.

AdvMedia owns playback preparation, including internal media-profile resolution,
and returns only `playback_payload`. ASTV consumes
`advmedia_processed_response.playback_payload` and performs the final
`media_player.play_media` action using its existing `media_player_entity`.
Endpoint selection and terminal targeting remain ASTV-owned; the endpoint is
not returned by AdvMedia. AdvMedia owns its internal profile and
payload-generation rules; MediaCat owns neither.

### Current Google Home Device path

For `g_home_device`, ASTV carries the complete record, selected method, and
selected assistant endpoint through its own execution branch. It reads the
selected method's source, uses `source.provider` to select Google Assist, and
passes the ASTV intent, complete selected source, and endpoint phrase to that
provider. Google Assist derives the intent family and selects the generic Media
command builder. The builder alone constructs the final phrase and conditionally
appends the independently selected endpoint phrase. The provider returns that
builder response unchanged, and the Google Home Device Engine invokes
`google_assistant_sdk.send_text_command` with its `command` field.

This branch does not call AdvMedia and has no media-player profile. MediaCat
supplies item-specific source facts but does not select the endpoint, construct the
final command, or invoke the assistant SDK.

## Gateway Semantics

- Exclusive split gateways represent genuine routing decisions with one incoming flow and mutually exclusive outgoing outcomes.
- Exclusive merge gateways represent convergence only. They are not scripts or functions, do not transform data, and do not imply a consolidator.
- Parallel gateways are used only when the architecture genuinely requires parallel execution and/or synchronisation.
- Gateway outcome labels describe routing outcomes and are not components.

## External and Data Dependencies

| Dependency | Type | Consumer or relationship |
|---|---|---|
| External NFC input | External input | Delivered over MQTT to the configured NFC reader sensors |
| `sensor.pi_nfc_02_last_uid`, `sensor.pi_nfc_99_last_uid` | MQTT-fed Home Assistant sensors | State-change inputs evaluated by ASTV - Tag Listener; transitions to or from `unknown` or `unavailable` are excluded at the Home Assistant trigger boundary before UID Gateway invocation |
| `astv_tag_mapping.yaml` | Data source | Active Find Tag Record lookup |
| `astv_intent_catalogue.yaml` | Data source | Find Intent Record lookup using `lookup_intent_id`; result `intent_record_response` |
| `astv_area_endpoints2.yaml` | Data source | Find Area Domain Endpoints |
| Home Assistant metadata / registry | Dynamic data source | Find Routine Trigger |
| AdvMedia subsystem | External subsystem | Reached directly by ASTV - HA Media Player Engine through `script.advmedia_process_media_record` |
| `media_player.play_media` | External action | HA Media Player Engine |
| `google_assistant_sdk.send_text_command` | External action | Google Home Device Engine |
| Matter-exposed `input_boolean` | External/Home Assistant entity | Turned on by Google Automation Engine |
| Google Home automation | External automation | Reacts to the Matter-exposed helper |

## Interface Naming and Return Boundaries

Exact verified names must be preserved. In particular:

- `lookup_intent_id`
- `intent_record_response`
- `intent_record`
- `execution_method`
- `selected_endpoint`
- `area_response`
- `area_domain_response`
- `playback_method_response`
- `area_playback_endpoint_response`
- `advmedia_processed_response`
- `command_response`
- `provider_response`
- `trigger_response`
- `intent_context`
- `target_context`
- `execution_context`

A caller's `response_variable` name describes how that caller captures a result.
A child's returned payload name describes the child's own interface. Do not
rename either for visual or documentary consistency, and do not collapse names
across provider or subsystem boundaries.

## Historical and Retired Implementations

Retired or quarantined ASTV implementations remain recoverable through Git and
Linear history but are not part of current source or current architecture.
Their historical existence does not imply a supported compatibility path,
fallback path, or active dependency.
