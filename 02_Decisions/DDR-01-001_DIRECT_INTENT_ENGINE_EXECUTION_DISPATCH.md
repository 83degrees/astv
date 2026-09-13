# DDR-01-001 — Direct Intent-Engine Execution Dispatch

## Status

`Accepted`

## Decision

`script.astv_select_intent_engine` is only the intent-family router. After a
family is selected, that intent engine owns its branch-specific preparation,
constructs the complete execution-dispatch payload, and calls
`script.astv_select_execution_engine` directly.

The intent-engine-to-execution-selector boundary has exactly three required
top-level objects:

```yaml
intent_context:
  record: ...
  data: {}

target_context:
  area: ...
  endpoint: {}

execution_context:
  engine: ...
```

All shown inner keys are required. Unused `data` and `endpoint` values remain
present as empty objects. Select Execution Engine is a pure router on
`execution_context.engine` and passes the three objects unchanged into the
selected execution engine. Each execution engine owns its context extraction,
engine-specific validation, and any adaptation at an external product boundary.

## Context

The previous topology returned branch-specific preparation results to Select
Intent Engine. That router captured the result, reconstructed a dispatcher
mapping, and then called Select Execution Engine. This made the family router
responsible for knowledge of both family-specific output and the Phase 3
dispatch interface.

Media and Routine already own the information needed to form a complete
dispatch request. ASTV needed one predictable boundary shape that keeps
family-specific data inside its family context without expanding the generic
dispatcher top level.

## Alternatives considered

### Keep central dispatch in Select Intent Engine

This would preserve one dispatcher call site, but the family router would
continue to capture and reinterpret intent-engine results. Every new family or
family-specific value could require central routing changes unrelated to family
selection.

### Introduce a separate payload-consolidation script

This could isolate reconstruction from Select Intent Engine, but would add a
component and another handoff without adding a distinct architectural
responsibility.

### Refactor the complete upstream and downstream flow at once

This could apply the context model end to end, but would enlarge the change and
compatibility surface beyond the boundary needed to resolve the current design
problem.

## Rationale

Direct dispatch keeps intent-family knowledge with the selected intent engine
and leaves Select Intent Engine with one responsibility: family routing. The
fixed context shape provides a predictable interface across Media and Routine
while allowing family-specific data to evolve under `intent_context.data`.

Carrying the three-context structure through Select Execution Engine gives all
three execution engines one consistent ASTV-owned interface. Keeping external
adaptation in the engine that crosses the boundary preserves provider-owned
contracts without coupling the selector to engine-specific requirements.

## Consequences / trade-offs

- Media and Routine each have an explicit call to Select Execution Engine.
- Adding an intent family requires that family to construct the complete fixed
  context shape.
- Select Intent Engine no longer receives a normalized branch response or owns
  execution dispatch.
- The internal dispatch contract changes incompatibly from v2 to v3, but both
  producers and the sole consumer change atomically.
- All three downstream engines receive `intent_context`, `target_context`, and
  `execution_context`; their legacy inputs are not supported in parallel.
- Select Execution Engine rejects only blank or unsupported routing keys.
- Each selected engine validates and extracts its required values locally.
- HA Media Player remains the ASTV-owned adaptation point and calls the
  AdvMedia direct-core contract without an intermediate ASTV adapter.
- The upstream intent-record input was subsequently renamed from `request` to
  `intent_record` under ASTV-203; `target_area` remains unchanged.

## Source Linear issue

`ASTV-200`; extended through Phase 3 by `ASTV-204`

## Supersedes

`Not applicable`
