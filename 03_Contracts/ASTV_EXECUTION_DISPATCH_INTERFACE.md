# ASTV Execution Dispatch Interface

## Contract Record

| Property | Value |
| --- | --- |
| Owner | ASTV |
| Producers | `script.astv_intent_engine_media` and `script.astv_intent_engine_routine` |
| Consumer | `script.astv_select_execution_engine` |
| Interface version | `3.0.0` |
| Change authority | [ASTV-200](https://linear.app/83degrees/issue/ASTV-200/review-astv-intent-engine-branch-structure) |
| Source path | `03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` |

## Purpose

This contract defines the internal boundary between ASTV intent-family
preparation and execution selection. Each selected intent engine constructs the
complete dispatch payload and calls `script.astv_select_execution_engine`
directly. `script.astv_select_intent_engine` is the intent-family router only;
it is not a producer or adapter at this boundary.

The execution selector adapts this interface to the existing downstream
execution-engine interfaces. ASTV-200 does not change those downstream
interfaces.

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
| `request` | `intent_context.record` |
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
| `request` | `intent_context.record` |
| no family-specific data | `intent_context.data: {}` |
| `target_area` | `target_context.area` |
| no selected endpoint | `target_context.endpoint: {}` |
| `g_automation` | `execution_context.engine` |

Routine-trigger resolution remains downstream in the Google Automation path.

## Execution Selector Adapter Mappings

### `ha_mplayer`

| Dispatch field | Existing downstream input |
| --- | --- |
| `intent_context.record` | `request` |
| `target_context.endpoint` | `selected_endpoint` |
| `execution_context.engine` | `execution_method` |
| `intent_context.data.media_record` | `media_record` |

### `g_home_device`

| Dispatch field | Existing downstream input |
| --- | --- |
| `intent_context.record` | `request` |
| `target_context.endpoint` | `selected_endpoint` |
| `execution_context.engine` | `execution_method` |
| `intent_context.data.media_record` | `media_record` |

### `g_automation`

| Dispatch field | Existing downstream input |
| --- | --- |
| `intent_context.record` | `request` |
| `target_context.area` | `target_area` |

The downstream interfaces of `script.astv_ha_mplayer_engine`,
`script.astv_g_home_device_engine`, and `script.astv_g_automation_engine` remain
unchanged.

## Execution Methods and Validation

### `ha_mplayer`

- Requires a non-blank `target_context.endpoint.media_entity`.
- Requires `intent_context.data.media_record`.
- Calls `script.astv_ha_mplayer_engine` using the adapter mapping above.

### `g_home_device`

- Requires a non-blank `target_context.endpoint.phrase`.
- Requires `intent_context.data.media_record`.
- Calls `script.astv_g_home_device_engine` using the adapter mapping above.

### `g_automation`

- Requires a non-blank `intent_context.record.routine`.
- Requires a non-blank `target_context.area`.
- Calls `script.astv_g_automation_engine` using the adapter mapping above.
- Does not consume `target_context.endpoint`.

A blank or unsupported `execution_context.engine`, a missing Media endpoint, a
missing Media record, a blank Routine value, or a blank Routine target area
creates the existing visible failure and stops the dispatcher before any
downstream execution engine is called. ASTV-200 does not change these validation
semantics or introduce automatic retry or fallback.

## Compatibility Assessment

This is an intentionally breaking replacement of the internal Phase 2-to-Phase
3 input shape. Both producers and the sole consumer are ASTV-owned and are
changed atomically under ASTV-200. `script.astv_select_intent_engine` ceases to
be an intermediary producer.

No declared external consumer uses this internal contract. The MediaCat and
AdvMedia provider-owned contracts listed in `00_Governance/PROJECT_PROFILE.md`
are not changed. Downstream ASTV execution-engine interfaces are preserved by
the selector adapter.

## Version History

### `3.0.0` — direct intent-engine dispatch

- Replaced the five-field dispatcher input with the fixed three-context shape.
- Made each selected intent engine the direct producer and caller.
- Made Select Intent Engine routing-only.
- Kept Select Execution Engine as the adapter to unchanged downstream engines.

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
meaning, introducing a common execution response, changing direct producer
ownership, or changing downstream adapter guarantees requires a coordinated
implementation, contract, architecture, and diagram update.
