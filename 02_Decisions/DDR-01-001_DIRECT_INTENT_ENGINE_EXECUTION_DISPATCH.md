# DDR-01-001 — Direct Intent-Engine Execution Dispatch

## Status

`Proposed`

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
present as empty objects. Select Execution Engine adapts this boundary to the
existing downstream execution-engine interfaces until separately governed work
changes them.

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

Keeping Select Execution Engine as a temporary adapter contains the breaking
interface change within ASTV and preserves the established downstream engine
interfaces and validation behaviour.

## Consequences / trade-offs

- Media and Routine each have an explicit call to Select Execution Engine.
- Adding an intent family requires that family to construct the complete fixed
  context shape.
- Select Intent Engine no longer receives a normalized branch response or owns
  execution dispatch.
- The internal dispatch contract changes incompatibly from v2 to v3, but both
  producers and the sole consumer change atomically.
- Downstream engines continue to use their existing input names, so Select
  Execution Engine temporarily owns the adapter mappings.
- The upstream intent-record input was subsequently renamed from `request` to
  `intent_record` under ASTV-203; `target_area` remains unchanged.

## Source Linear issue

`ASTV-200`

## Supersedes

`Not applicable`
