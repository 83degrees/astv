# DDR-01-002: Immutable Runtime Intent-Catalogue Registry

**Status:** Proposed  
**Owner:** ASTV  
**Source Linear issue:** [ASTV-331](https://linear.app/83degrees/issue/ASTV-331/design-astv-runtime-catalogue-registry-and-lookup-migration)  
**Supersedes:** None

## Decision

ASTV will move runtime intent lookup behind an ASTV-owned Home Assistant custom
integration with domain `astv_intent_catalogue`. The provider will expose one
read-only lookup action, `astv_intent_catalogue.lookup`, and own an immutable
active registry built from the exact current
`astv.intent_catalogue` schema version.

A candidate becomes active only after the complete persisted document has been
parsed and validated off to the side. Activation replaces the single active
registry reference atomically on the Home Assistant event loop. Readers see
either the complete old snapshot or the complete new snapshot; they never see
a partially built or mutating registry.

Cold startup has no inherited in-memory active state. If the persisted
candidate is unavailable or invalid, config-entry setup fails and no lookup is
served from legacy or partially valid data. During an in-process refresh, a
failed candidate leaves the prior valid active snapshot and its identity
unchanged.

Persisted revision, active revision, schema version, lookup-interface version,
and integration release version are separate identities. Revisions are opaque
to consumers even when the implementation derives them from content.

The existing `script.astv_find_intent_record` remains the lookup-only
compatibility adapter. It preserves trim-and-lower-case lookup normalization,
returns only the selected record, returns `{}` for an absent ID, and does not
expose the provider envelope or synthesize an `intent_id`.

The first adoption is an explicit, governed migration of the existing
unversioned eight-record YAML document. The schema-v1 loader will not infer,
upgrade, or fall back to that legacy shape. Runtime cutover and integration
implementation remain ASTV-333 work; administration mutation, staging, and
activation operations remain ASTV-332 work.

## Context

The current script directly includes a mutable YAML mapping for each lookup.
That couples the runtime consumer to persisted serialization, offers no
complete-candidate activation boundary, and cannot retain a known-good
in-memory snapshot when a replacement candidate fails.

ASTV-330 approved schema v1.0.0, including a versioned envelope, strict
complete-document validation, record-only runtime compatibility, and explicit
migration. The Product Administration Interface Standard establishes the
separation of persisted and active state and requires failure-safe activation
where those states differ. Home Assistant provides read-only response actions
through `SupportsResponse.ONLY`, and recommends registering integration
actions in `async_setup` while validating config-entry availability inside the
handler.

## Alternatives considered

### Continue direct YAML inclusion in the script

Rejected. It preserves current simplicity but has no provider boundary,
transactional replacement, stable active identity, or retained-active behavior.

### Cache a mutable dictionary and update it in place

Rejected. Concurrent lookups could observe a mixed candidate, and rollback
would depend on reconstructing earlier mutable state.

### Let the script parse the schema-v1 document

Rejected. It would leave persistence and provider validation coupled to a
consumer adapter, make service discovery and administration evolution harder,
and repeat logic outside the owning integration.

### Persist the active snapshot separately

Deferred. A second persisted active copy could survive an invalid cold-start
candidate, but it introduces additional storage, reconciliation, backup, and
restoration policy. ASTV-331 does not invent that policy. Initial startup is
fail-closed; future administration design may propose a separately governed
durable-last-known-good mechanism.

### Return only the raw record from the integration action

Rejected for the provider action. A stable envelope is needed to distinguish an
expected miss from provider state and to expose independent interface, schema,
and active-revision identities. The existing script strips that envelope so
downstream ASTV behavior remains compatible.

## Rationale

A frozen complete snapshot plus one atomic reference swap is the smallest
design that gives deterministic reads, complete-candidate validation, and
failure retention without introducing a database or shared mutable state.
Keeping the script as an adapter isolates the migration from the established
Intent Gateway, area resolution, intent routing, and fixed dispatch contexts.

Using a Home Assistant custom integration creates a discoverable provider
boundary with native response-action and config-entry lifecycle behavior.
Keeping lookup read-only and deferring all mutation operations avoids deciding
ASTV-332 policy prematurely.

## Consequences and trade-offs

- Runtime lookup depends on a configured and loaded custom integration after
  cutover.
- Installation alone does not register an action; Home Assistant must load the
  integration. The action is registered in `async_setup`, and a call made
  without a loaded config entry fails visibly.
- An invalid cold-start candidate makes lookup unavailable. The design does not
  silently serve legacy bytes or stale memory after a process restart.
- A failed in-process refresh retains the prior active snapshot.
- Memory use includes one complete candidate plus the active snapshot during
  preflight.
- Records must be deeply frozen or defensively copied so a response cannot
  mutate provider state.
- The existing caller-visible absent-ID behavior remains `{}`; provider
  operational failures remain execution failures rather than being disguised
  as missing records.
- The ASTV repository gains a separately deployable `haos_integration` unit
  delivered by HACS, while catalogue bytes remain a distinct
  `haos_config` unit under the operator-selected deployment standard.
- Initial cutover and rollback must treat integration implementation and
  catalogue bytes as one compatible pair.
