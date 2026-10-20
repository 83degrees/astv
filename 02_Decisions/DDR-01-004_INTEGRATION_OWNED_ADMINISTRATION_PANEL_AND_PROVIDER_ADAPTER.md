# DDR-01-004 — Integration-Owned Administration Panel and Provider Adapter

## Status

Proposed under ASTV-350

## Decision

ASTV will deliver its catalogue administration UI as a non-iframe Home
Assistant custom panel bundled with the existing `astv_intent_catalogue` HACS
custom integration. The panel will use Home Assistant's authenticated frontend
WebSocket connection to invoke the provider's response-only service actions. It
will not introduce a Home Assistant App, shared web server, direct YAML access
or separate deployment route.

One client-side provider adapter will own capability negotiation, explicit
active/draft selection, response extraction, native transport-error mapping,
bounded loading/timeout state, read/manage presentation separation and
optimistic-concurrency reconciliation. Before a guarded mutation it will read
current administration status and use `editable_revision`. On
`stale_revision` it will refresh status and the selected provider view, expose
a conflict and never retry or overwrite automatically. Staging and activation
remain separate user actions.

The panel will be visible to authenticated users for non-secret normalized
reads. Browser admin state may control manage affordance visibility, but the
provider's Home Assistant admin-service registration remains the authorization
boundary for validation and state change.

AdvNFC reverse association will be an optional read-only adapter dependency.
AdvNFC remains authoritative for tag mappings, and its absence or
incompatibility will not disable independent ASTV administration.

Frontend files will remain inside the HACS integration tree. The registered
module URL will carry a digest of the installed module bytes for cache
invalidation. HACS update/removal plus the required Home Assistant restart will
remain the lifecycle mechanism; ASTV will not invent hot file replacement or a
second cleanup path.

## Context

The accepted ASTV administration interface v1.1.0 exposes capability/status,
normalized active and provider-owned durable-draft reads, guarded staging and
explicit activation. ASTV-351 needs a responsive editor, but ASTV-350 must
first establish a supported Home Assistant presentation and transport boundary
without confusing active state, shared draft state or browser-local edits.

Home Assistant custom panels can reuse the authenticated frontend session and
sidebar. Response-only actions require `return_response: true`; service-bus
authorization and schema rejection can fail before an ASTV handler returns its
structured envelope. The client therefore needs an explicit transport/provider
outcome boundary.

The single shared draft permits concurrent clients only if stale writers stop
and reconcile. A timeout on a mutating WebSocket call is also ambiguous: it
cannot safely authorize a blind retry.

## Alternatives considered

### Separate Home Assistant App or shared administration server

Rejected. It adds a deployable unit, authentication boundary and operational
lifecycle when the existing integration and Home Assistant frontend already
provide the required local surface.

### Lovelace card only

Rejected. A card can demonstrate calls but does not supply the discoverable,
integration-owned sidebar workspace approved for catalogue administration.

### Admin-only panel

Rejected. The provider deliberately exposes non-secret read operations to
ordinary Home Assistant service-call contexts. Hiding the entire panel would
collapse the read/manage distinction. Manage actions remain server-enforced.

### Browser-local draft or active-as-draft fallback

Rejected. Either choice misrepresents the durable shared draft, loses restart
and multi-client semantics, and defeats revision conflict handling.

### Automatic retry after stale revision or timeout

Rejected. It can overwrite a concurrent edit or repeat an operation whose
server outcome is unknown. Reconciliation must precede a new explicit action.

### Copy AdvNFC associations into ASTV

Rejected. AdvNFC owns tag mappings and its reverse query. Mirroring creates a
second authority and couples ASTV editing to an optional provider.

## Rationale

An integration-owned panel is the smallest boundary that preserves native Home
Assistant authentication, HACS delivery and product independence. A dedicated
adapter concentrates the contract-sensitive behavior that the later editor
must not duplicate. Digest-addressed assets make upgrades deterministic without
disabling static caching, while restart-based cleanup matches the HACS custom
integration lifecycle.

## Consequences / trade-offs

- The panel is present for read-only users; UI affordance checks improve
  clarity but never replace provider authorization.
- A Home Assistant restart is required after HACS update or removal before the
  process route and module identity are rebuilt.
- A timed-out mutation remains indeterminate until status and relevant views are
  reread.
- Concurrent edits can require manual reapplication after conflict; there is no
  automatic merge.
- The adapter depends on administration interface major version 1 and negotiates
  optional capabilities before use.
- Mobile layout must account for Home Assistant safe-area insets and narrow
  iPhone viewports without a separate mobile application.
- ASTV schema v1.0.0, immutable `intent_id`, `title` as UI Name and the two
  supported intent discriminators remain unchanged; Description remains absent.

## Source Linear issue

ASTV-350

## Supersedes

Not applicable
