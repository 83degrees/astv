# ASTV Pre-Project Context Handover

> **Status:** Historical/reference only. This preserves durable context from the pre-project ChatGPT conversation. It is not an active source of truth and must never override current live evidence, contracts, architecture, or applicable agent rules.

## Project goals

ASTV is a Home Assistant orchestration system that turns NFC tag scans into area-aware actions. It resolves a UID and target area, routes the request to `Media` or `Routine`, selects a playback path for media, and executes routines through dynamically resolved Matter-exposed helpers. External systems such as AdvMedia remain behind explicit, stable interfaces. Architecture work must be verifiable against production without giving routine AI workflows write access to production.

## Chat / Work / Codex / MCP roles

- **Chat:** architecture discussion, design decisions, stand-back review, cross-project reasoning, and result review.
- **Work:** longer multi-file audits, comparisons, specifications, and finished deliverables inside deliberately scoped local sources.
- **Codex:** local file implementation, validation, diffs, and repository-style work; only explicitly in-scope local files may be changed.
- **HA MCP:** live production evidence for scripts, automations, entities, labels, areas, helpers, and configuration. During architecture work it is a read source, not the normal production-change route.
- **Project files:** durable shared context. Conversation memory is not a substitute for current files, contracts, or live evidence.

Preferred flow: agree the concept in Chat; use Work for coordinated analysis/specification when helpful; record active scope in `CURRENT_WORK.md`; implement locally with Codex; validate; promote durable decisions into current architecture or contracts.

## Production safety model

Production HA is on another machine and must not be exposed as a writable filesystem to Chat, Work, or Codex during normal architecture work.

- Writable ASTV scope: `C:\Users\Graham\OneDrive\Documents\Computing\Home_Assistant\ASTV`.
- AdvMedia and sibling projects stay outside that writable scope unless a specific cross-project task explicitly requires access.
- `AGENTS.md` is an instruction boundary, not a hard security boundary; filesystem scope, a one-way snapshot, and MCP read-only enforcement are stronger controls.
- Production changes use a separate, deliberate, explicitly approved route.
- Use one active editor per file. Save and close draw.io before Codex edits the diagram, then reopen the saved file.

HA-MCP has a **Read Only Mode** intended to disable write tools and block write/destructive calls. A mode change requires restarting the add-on and refreshing/reconnecting the client tool list. Normal architecture work should use read-only mode when MCP is available.

## Local structure and operating files

```text
Home_Assistant\
├── AGENTS.md
├── CURRENT_WORK.md
├── contracts\
│   └── ASTV_ADVMEDIA_INTERFACE.md
├── ASTV\
│   ├── 00_PreProject_History\
│   │   └── CONTEXT_HANDOVER.md
│   └── 01_Architecture\
│       ├── AGENTS.md
│       ├── ASTV_ARCHITECTURE.md
│       └── ASTV_Architecture.drawio
└── Production_ReadOnly\
    └── starburst\
```

`CURRENT_WORK.md` is the short-lived change specification: objective, scope, agreed design, pending decisions, files allowed/not allowed to change, validation, dependencies, status, and notes. Root rules cover HA-wide work; subsystem rules add ASTV constraints; `contracts/` owns shared boundaries. `.$ASTV_Architecture.drawio.bkp`, when present, is an older temporary backup and not the current source of truth.

## `Production_ReadOnly\starburst` workflow

Manual snapshot path:

`C:\Users\Graham\OneDrive\Documents\Computing\Home_Assistant\Production_ReadOnly\starburst\`

This is a sibling reference area, not part of writable ASTV. Manually copy production files to it using a one-way HA→PC flow, preserving HA subfolders where practical. Likely files include `configuration.yaml`, `scripts.yaml`, `automations.yaml`, `astv_tags2.yaml`, and `astv_area_endpoints2.yaml`.

Before an audit: refresh the copy; never sync changes back to HA; compare the local architecture/contracts with the snapshot; remember the snapshot is current only as of its last refresh. Prefer verified live read-only HA evidence when freshness matters and MCP is available.

## Current ASTV architecture

The lifecycle flows left-to-right across three phase bands.

### Phase 1 — Entry and request resolution

- `automation.astv_tag_listener` is triggered only by `sensor.pi_nfc_02_last_uid` and `sensor.pi_nfc_99_last_uid`; it calls `script.astv_uid_gateway` with `uid` and `trigger_entity`.
- `script.astv_uid_gateway` calls `script.astv_find_uid_record(uid)` and captures `request`.
- It separately calls `script.astv_resolve_area(request, trigger_entity)` and captures `area_response`, deriving `target_area`.
- It calls `script.astv_select_intent_engine(request, trigger_entity, target_area)`.
- `script.astv_find_uid_record` depends on `astv_tags2.yaml`.
- Find UID Record and Resolve Area are sibling children of UID Gateway; execution order does not create a function-to-function call.

### Phase 2 — Intent routing

- `script.astv_select_intent_engine` makes the exclusive `Intent?` decision: `Media` or `Routine`.
- `Routine` originates here and bypasses the Media intent engine.
- `Media` enters `script.astv_intent_engine_media(request, trigger_entity, target_area)`.
- It calls three sibling functions:
  - `script.astv_find_area_domain_endpoints(domain, area)` → `area_domain_response`, using `astv_area_endpoints2.yaml`.
  - `script.astv_resolve_playback_method(preferences, available_sources)` → `playback_method_response`.
  - `script.astv_select_area_playback_endpoint(area_playback_domain, playback_method)` → `area_playback_endpoint_response`.
- It then calls `script.astv_select_media_engine(request, playback_endpoint)`.

### Phase 3 — Execution

`script.astv_select_media_engine` makes the exclusive `Playback Engine?` decision: `HA Media Player` or `Google Home Device`.

**HA Media Player**

- `script.astv_ha_mplayer_engine(request, selected_endpoint)` calls `script.astv_handle_provider(request_object, media_player)`, captures `provider_payload_response`, and terminates at `media_player.play_media`.
- `script.astv_handle_provider` selects `Radio Browser` or `AdvMedia`.
- `script.astv_provider_radiobrowser(provider_data_object)` returns `provider_payload_response`.
- `script.astv_adapter_advmedia` is the ASTV-owned boundary into AdvMedia.

**Google Home Device**

- `script.astv_g_home_device_engine(request, selected_endpoint)` calls `script.astv_provider_g_assist(intent, request_object, endpoint_phrase)`, captures `provider_command_response`, and calls `google_assistant_sdk.send_text_command` using `provider_command_response.command`.
- `script.astv_provider_g_assist` selects a command builder; the currently implemented outcome is `Media`.
- `script.astv_cmd_builder_media(phrase, append_target, endpoint_phrase)` returns `command_response`.
- Split/merge gateways are control flow only; a merge is not a component and does not transform the response.

**Routine / Google Automation**

- `script.astv_g_automation_engine(routine, target_area)` calls `script.astv_find_routine_trigger(routine, target_area)` and captures `trigger_response`.
- `script.astv_find_routine_trigger` searches HA metadata dynamically using area `target_area` and labels `routine_<routine>` and `matter_gh_trigger`; no static routine-to-trigger YAML matrix exists.
- The engine calls `input_boolean.turn_on` on `trigger_response.entity_id`.
- A Google Home automation reacts to the Matter-exposed helper. ASTV does not call that automation directly.

## Exact interface contracts and names

Preserve these verified names: `request`, `area_response`, `area_domain_response`, `playback_method_response`, `area_playback_endpoint_response`, `provider_payload_response`, `payload_response`, `advmedia_response`, `command_response`, `provider_command_response`, and `trigger_response`.

A caller's `response_variable` name is not automatically the child's returned object name. Do not normalise names across caller, provider, or adapter boundaries.

### ASTV ↔ AdvMedia

- ASTV boundary: `script.astv_adapter_advmedia`.
- AdvMedia entry point: `script.advmedia_prepare_playback`.
- ASTV owns intent/routing, adapter selection, target endpoint selection, and passing playback context.
- AdvMedia owns AdvMedia lookup, metadata preparation, player-profile handling, and final AdvMedia payload generation.
- Contractual inputs: `media_item_id`, `media_catalogue`, `media_player`, `media_profile`.
- AdvMedia returns `advmedia_response` to the adapter.
- The adapter returns `payload_response` to `script.astv_handle_provider`.
- Handle Provider's result is captured as `provider_payload_response` by the HA Media Player Engine.
- ASTV may show the adapter and external AdvMedia subsystem, but must not expand AdvMedia internals.
- Any field, required/optional, return, ownership, or entry-point change requires updating `contracts\ASTV_ADVMEDIA_INTERFACE.md`, identifying both-side changes, updating relevant architecture, and validating both projects.

## Diagram / draw.io rules and naming

- `ASTV_Architecture.drawio` is the authoritative visual structure and phase layout; `ASTV_ARCHITECTURE.md` is the semantic record; live YAML is authoritative for implementation details.
- Do not edit the diagram unless explicitly requested/approved. A rule-file change alone does not authorise a diagram edit.
- Read the latest diagram from disk immediately before editing. Preserve manual geometry, labels, styles, phase placement, and routes. Make the smallest change; do not globally relayout, compact, crop, centre, symmetrise, or remove deliberate whitespace.
- Primary flow is left-to-right through Phase 1/2/3. Components remain in their owning phase. Supporting functions sit near/beneath their real caller; sibling functions are not connected merely because they execute sequentially.
- Use compact diamonds only for real gateways. Exclusive merge means convergence only; parallel (`+`) is only for genuine parallelism/synchronisation.
- Gateway names: `gateway_split_<purpose>`, `gateway_merge_<purpose>`, `gateway_parallel_<purpose>`.
- Outcome labels (`Media`, `Routine`, `HA Media Player`, `Google Home Device`, `AdvMedia`, `Radio Browser`) are native connector labels near the gateway, never separate shapes.
- Current connector convention: one invocation = one solid call connector; one return = one separate dashed connector. Each payload variable gets its own bordered native label on that connector. Never combine variables in one bordered label or create one connector per variable.
- On horizontal blue primary calls, stack input labels vertically above/top-left of the receiver with clear whitespace.
- Prefer orthogonal routing, call/return separation, local grouping, and short dependency/external-action paths.
- Colours: blue primary ASTV scripts; green support functions/providers; yellow data sources; purple external actions; neutral grey HA entities; grey hexagon external subsystem.
- Do not export PNG/PDF unless requested.

## Legacy / excluded scripts

Present in YAML does not mean architecturally active. These are excluded unless a verified dependency is added:

- `script.astv_resolver`
- `script.astv_resolver_v2`
- `script.astv_sound_tag_feedback`

## Governance and precedence

When sources conflict:

1. verified live production evidence or refreshed production snapshot;
2. explicit architecture/interface contracts;
3. current subsystem architecture documentation and authoritative diagram;
4. applicable `AGENTS.md` rules;
5. project documentation and working/change-state files;
6. this pre-project history.

Identify conflicts rather than guessing. Manual user edits are authoritative unless explicitly superseded. Do not change unrelated files, broaden scope, invent architecture for convenience, or change a cross-project interface without identifying affected consumers and obtaining agreement. Changes to ownership, boundaries, inputs/outputs, routing, or external dependencies are architecture changes.

## Unresolved items at handover

1. **Desktop MCP connector failure:** rich `ha-mcp-starburst-v2` tools were discoverable, but invocation reported the connector disabled/unavailable in the desktop session. HA, PC, and desktop-app restarts and read-only toggling did not fix it. The plugin worked in ChatGPT web, pointing to a desktop connector/session issue rather than HA. Until resolved, use web for live MCP reads and the snapshot for desktop audits; do not keep changing HA server configuration to chase this symptom.
2. **`AGENTS.md` connector-rule contradiction:** an early rule says each input gets its own call line; later/current rules say one invocation gets one connector with a separate bordered native label per variable. The intended convention is the latter. Reconcile the older wording only in a separate explicitly scoped change; this handover does not modify `AGENTS.md`.
3. **Snapshot freshness/automation:** the snapshot is manual. Any future refresh automation must remain strictly one-way HA→PC and create no write path to production.
4. **Desktop MCP retest:** after a relevant desktop update/reconnect, test a safe read such as `ha_config_get_script("script.astv_uid_gateway")` while MCP read-only mode is enabled.

## Historical-use rule

Use this file to understand why the current structure and safety model exist and to recover pre-project decisions not represented elsewhere. To promote a historical statement into active governance, put it in the appropriate current source and validate it there.
