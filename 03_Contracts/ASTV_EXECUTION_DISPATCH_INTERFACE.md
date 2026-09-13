# ASTV Execution Dispatch Interface

## Contract Record

| Property | Value |
| --- | --- |
| Owner | ASTV |
| Producers | `script.astv_intent_engine_media` and `script.astv_intent_engine_routine` |
| Consumers | `script.astv_select_execution_engine`, `script.astv_ha_mplayer_engine`, `script.astv_g_home_device_engine`, and `script.astv_g_automation_engine` |
| Interface version | `4.1.0` |
| Change authority | [ASTV-208](https://linear.app/83degrees/issue/ASTV-208/restore-provider-routing-and-generic-command-builder-boundary-for) |
| Source path | `03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` |

## Purpose

This contract defines the internal boundary between ASTV intent-family
preparation and execution selection. Each selected intent engine constructs the
complete dispatch payload and calls `script.astv_select_execution_engine`
directly. `script.astv_select_intent_engine` is the intent-family router only;
it is not a producer or adapter at this boundary.

The execution selector is a pure router. It routes only on
`execution_context.engine` and passes all three context objects unchanged to
the selected Phase 3 execution engine. Each execution engine uses the context
it needs and owns its downstream orchestration, including applicable validation
and adaptation at any external product boundary.

## Required Interface

```yaml
intent_context:
  record: <original intent catalogue record>
  data: <intent-family-specific data object; {} when unused>

target_context:
  area: <resolved target area>
  endpoint: <selected endpoint object; {} when unused>

execution_context:
  engine: <selected execution engine>
```

All three top-level objects are mandatory. The inner keys `record`, `data`,
`area`, `endpoint`, and `engine` are mandatory. `data` and `endpoint` remain
present as empty objects when unused.

The dispatcher returns no common response.

## Producer Mappings

### Media

`script.astv_intent_engine_media` maps its existing values as follows:

| Existing value | Dispatch field |
| --- | --- |
| `intent_record` | `intent_context.record` |
| `media_record_response` | `intent_context.data.media_record` |
| `target_area` | `target_context.area` |
| `selected_endpoint` | `target_context.endpoint` |
| `execution_method` | `execution_context.engine` |

The Media producer supplies the complete unchanged normalized MediaCat record.
It does not flatten the record, remove unselected methods, or write ASTV's
selected method into that record.

### Routine

`script.astv_intent_engine_routine` maps its existing values as follows:

| Existing value | Dispatch field |
| --- | --- |
| `intent_record` | `intent_context.record` |
| no family-specific data | `intent_context.data: {}` |
| `target_area` | `target_context.area` |
| no selected endpoint | `target_context.endpoint: {}` |
| `g_automation` | `execution_context.engine` |

Routine-trigger resolution remains downstream in the Google Automation path.

## Phase 3 Consumer Mappings

### `ha_mplayer`

| Selector input | HA Media Player Engine input |
| --- | --- |
| `intent_context` | `intent_context` |
| `target_context` | `target_context` |
| `execution_context` | `execution_context` |

### `g_home_device`

| Selector input | Google Home Device Engine input |
| --- | --- |
| `intent_context` | `intent_context` |
| `target_context` | `target_context` |
| `execution_context` | `execution_context` |

### `g_automation`

| Selector input | Google Automation Engine input |
| --- | --- |
| `intent_context` | `intent_context` |
| `target_context` | `target_context` |
| `execution_context` | `execution_context` |

There is no selector compatibility shim for the former `request`,
`selected_endpoint`, `execution_method`, `media_record`, or `target_area`
execution-engine inputs.

## Execution Methods and Validation

### `ha_mplayer`

- The HA Media Player Engine requires a non-blank
  `target_context.endpoint.media_entity` and
  `intent_context.data.media_record`.
- It adapts the ASTV contexts into the unchanged AdvMedia direct-core inputs and
  calls `script.advmedia_process_media_record`.

### `g_home_device`

- The Google Home Device Engine requires
  `intent_context.data.media_record` and reads the selected source through
  `execution_context.engine`.
- It selects the provider from `source.provider`; the selected generic command
  builder determines whether `target_context.endpoint.phrase` must be non-blank.

### `g_automation`

- The Google Automation Engine requires a non-blank
  `intent_context.record.routine` and `target_context.area`.
- It extracts the routine and target area locally and does not consume
  `target_context.endpoint`.

A blank or unsupported `execution_context.engine` creates the existing visible
failure in the selector. Engine-specific validation and failure handling occur
inside the selected engine or its selected ASTV-owned helper before an external
boundary is crossed. These ownership rules do not introduce automatic retry or
fallback.

## Compatibility Assessment

Version 4 is an intentionally breaking replacement of the three execution
engines' legacy input interfaces. The three-context shape itself is unchanged
from version 3, but it now continues unchanged through the selector into each
Phase 3 engine. All affected producers and consumers are ASTV-owned and change
atomically under ASTV-204.

No declared external consumer uses this internal contract. Version 4.1 retains
the complete version 4 three-context shape and relaxes no producer requirement:
media selection still supplies an endpoint object. It clarifies that command
construction, including conditional endpoint-phrase validity, belongs to the
selected ASTV command builder. The MediaCat and AdvMedia provider-owned
contracts listed in `00_Governance/PROJECT_PROFILE.md` remain separate and
unchanged. The HA Media Player Engine remains the ASTV-owned adaptation point
and calls the AdvMedia direct core without an intermediate ASTV adapter. The
Google provider helper change is ASTV-internal and changes atomically with its
sole caller.

## Version History

### `4.1.0` — Google Home provider and command-builder responsibility

- Preserved the complete three-context dispatch shape and Phase 3 mappings.
- Clarified that the Google Home Device Engine selects the provider from the
  selected source.
- Moved command and conditional endpoint-phrase validation responsibility to
  the selected ASTV command builder.
- Confirmed that no failure introduces automatic retry or fallback.

### `4.0.0` — shared Phase 3 execution-engine context

- Kept the version 3 context objects and their inner shapes unchanged.
- Made Select Execution Engine a pure router on `execution_context.engine`.
- Passed all three context objects unchanged into every Phase 3 execution
  engine.
- Removed the legacy execution-engine inputs and moved engine-specific
  extraction and validation into each engine.
- Preserved external provider, adapter, and helper interfaces.

### `3.0.0` — direct intent-engine dispatch

- Replaced the five-field dispatcher input with the fixed three-context shape.
- Made each selected intent engine the direct producer and caller.
- Made Select Intent Engine routing-only.
- Kept Select Execution Engine as the temporary adapter to the then-unchanged
  downstream engines; version 4 removed that temporary adaptation.

### `2.0.0` — normalized MediaCat dispatch

Version 2 used `request`, `target_area`, `execution_method`, and
`selected_endpoint` as common top-level fields and added `media_record` on the
Media path. Select Intent Engine captured the selected intent-engine response,
reconstructed that mapping, and was the sole dispatcher caller. It became
historical when version 3 replaced the internal boundary.

### `1.x` — pre-cutover Media shape

Before the normalized MediaCat cutover, Media used the same four top-level
fields as Routine and did not carry `media_record`. This is historical context,
not a compatibility promise or supported fallback.

## Change Control

Adding an intent or execution method, changing any required context key or its
meaning, introducing a common execution response, changing direct producer or
consumer ownership, or changing external adapter guarantees requires a
coordinated implementation, contract, architecture, and diagram update.
