# DDR-01-003 — Durable Shared Intent-Catalogue Draft and Explicit Activation

## Status

Proposed

## Decision

ASTV will expose one provider-owned administration boundary for the Intent Catalogue with exactly one durable provider-wide draft. The first accepted edit clones the immutable active snapshot; later create, update and delete operations replace the complete draft under opaque expected-revision concurrency control. Staging never changes runtime lookup.

Activation is explicit. ASTV validates the complete draft, constructs the immutable registry and verifies every MediaCat reference before an atomic persisted-state commit consumes the draft. The provider then swaps the single active registry reference on the Home Assistant event loop without further I/O or validation. Any expected failure before the commit retains the prior active and persisted states and the exact draft.

The administration interface exposes normalized records and opaque state identities, not YAML, paths or storage implementation. User-originated manage operations use Home Assistant admin-service enforcement. Home Assistant system contexts without a user identity retain the platform helper's trusted-call behavior; ASTV will not claim a finer role that Home Assistant does not enforce.

AdvNFC continues to own NFC mappings and reverse-reference queries. ASTV does not mirror that state, and AdvNFC availability does not gate ASTV activation.

## Context

DDR-01-002 established the immutable active registry and deferred mutation, staging, persistence and activation policy. ASTV-332 must now provide multi-client administration without exposing serialization internals, losing edits across restart, allowing stale writers, or making failed activation disturb a known-good runtime snapshot.

Separate independently writable active, persisted and draft representations would create ambiguous partial outcomes. A single shared draft and one activation commit point provide a tractable transaction boundary while preserving the approved read path.

Home Assistant supplies a native admin-service helper, but its verified behavior checks administrator status only when call.context.user_id is present. System contexts are intentionally passed through. Home Assistant has no generic entity-independent read role for the read actions.

## Alternatives considered

### Per-user drafts

Rejected. They require session identity, merge/conflict semantics and selection of which candidate activation should publish. None is needed for the household-local administration model.

### Direct CRUD against the active registry

Rejected. It would expose readers to incremental change, prevent complete-catalogue/reference validation before publication and weaken DDR-01-002 atomicity.

### Save each mutation directly to the authoritative persisted catalogue

Rejected. It would make persisted state an invalid or incomplete work area and complicate restart behavior. The durable draft keeps incomplete administrative work distinct.

### Combine save and activation

Rejected. Reviewable staged state, concurrent editing and correction/retry after dependency failure require a separately observable draft.

### Let ASTV query and mirror AdvNFC references

Rejected. AdvNFC owns the stored mapping and published reverse query. Mirroring creates a second authority and unnecessary activation coupling.

### Promise that only human administrators can manage

Rejected. Home Assistant's admin-service helper permits system contexts without user_id. Describing a stricter role without another enforceable mechanism would be false.

## Rationale

One shared complete draft is the smallest durable model that supports multiple managers, optimistic concurrency, restart continuity and deterministic activation. Expected revisions prevent lost updates without exposing storage. Complete validation and dependency preflight before a single commit point preserve the old active snapshot on expected failure. Provider-owned normalized actions keep storage replaceable and preserve product boundaries.

## Consequences / trade-offs

- Concurrent clients must refresh status after stale_revision and reapply intentional edits.
- There is no per-user private work or automatic merge.
- A valid active snapshot is required to initialize the first draft; recovery from a failed cold start remains an operator restoration concern.
- MediaCat availability and target existence gate activation of dependent records, but not side-effect-free structural validation or staging.
- AdvNFC unavailability affects only a manager's optional reverse-reference discovery.
- A crash after the activation commit point can leave the caller without a response; restart and status reconcile the committed state.
- Filesystem history, backups and deployment rollback are separate from activation failure safety.
- Implementation must reverify Home Assistant authorization and MediaCat error distinctions at its exact baseline.

## Source Linear issue

ASTV-332

## Supersedes

Not applicable
