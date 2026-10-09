# ASTV Intent Catalogue Integration and Migration Plan

**Status:** Approved design under ASTV-331; ASTV-333 candidate prepared, no deployment authorized
**Runtime implementation:** ASTV-333  
**Administration contract:** ASTV-332  
**Interoperability and cutover:** ASTV-336

## Scope

This plan defines the first controlled adoption of the ASTV Intent Catalogue
custom integration and schema-v1 catalogue. It does not authorize installation,
deployment, activation, production migration, rollback, or live Home Assistant
changes.

The adoption contains two independently deployable units that must be treated
as one compatible cutover set:

| Unit | Type | Governed source | Runtime target | Mechanism |
| --- | --- | --- | --- | --- |
| Catalogue provider integration | `haos_integration` | `custom_components/astv_intent_catalogue/**` | `/config/custom_components/astv_intent_catalogue/**` | HACS |
| Versioned catalogue document and script adapter | `haos_config` | `04_Implementation/haos/source/config/**` | `/config/**` | `operator_selected` |

The deterministic catalogue target remains:

```text
/config/astv/astv_intent_catalogue.yaml
```

The integration must not copy catalogue contents into config-entry data or
create a second authoritative catalogue.

## Required candidate state

Before a cutover candidate can enter review or deployment preparation,
ASTV-333 must provide:

- HACS-native source at
  `custom_components/astv_intent_catalogue/**`;
- a custom-integration `manifest.json` with a valid version;
- single-entry UI configuration and lifecycle handling;
- `astv_intent_catalogue.lookup` with
  `SupportsResponse.ONLY`;
- schema-v1 duplicate-key parsing and complete validation;
- immutable active registry and atomic reference replacement;
- a schema-v1 form of the exact eight-record baseline at
  `04_Implementation/haos/source/config/astv/astv_intent_catalogue.yaml`;
- the lookup-only script adapter in
  `04_Implementation/haos/source/config/packages/astv/astv_scripts.yaml`;
- HACS metadata and packaging/release support required by the Home Assistant
  Integration Deployment Standard;
- an updated configuration deployment manifest/runbook for every changed
  `/config/**` path; and
- tests proving the accepted lookup and failure semantics.

The production loader accepts only schema `astv.intent_catalogue` version
`"1.0.0"`. It must not infer or migrate the legacy unversioned mapping.

## Pre-cutover evidence and authority

Before any target change, the governing issue and deployment record must
identify:

- explicit authority for the exact candidate and `starburst` target;
- operator;
- immutable HACS Beta tag and full candidate SHA;
- exact configuration candidate SHA and repository-relative paths;
- content hashes or equivalent exact-byte identity for changed configuration;
- installed integration version immediately before change, or confirmed
  absence on the first installation;
- immediate prior bytes for every configuration target;
- Home Assistant backup/recovery location where used;
- HACS-created update entity after initial installation;
- Home Assistant configuration-check route;
- restart requirement and service-impact window; and
- functional validation and rollback decision points.

Credentials, tokens, backup keys, and secrets remain outside Git and Linear.

## Explicit legacy-to-v1 migration

The accepted source is the unversioned eight-record mapping at ASTV main commit
`5624e07782a3951c6bc7e7331b1a37dfdf69bb8a`,
`04_Implementation/haos/source/config/astv/astv_intent_catalogue.yaml`.
Its Git blob identity is
`cd8f977cddb8c7d21b675526a20505b89205f077`.

Migration is performed before deployment as a governed source change:

1. create the exact schema-v1 envelope;
2. place all eight existing mappings beneath `records`;
3. preserve every key and record value;
4. validate duplicate keys, the exact schema/version, all records, and
   normalized-key uniqueness;
5. compare extracted v1 runtime records with the legacy mapping for semantic
   equality;
6. verify all eight IDs plus trimmed/mixed-case representatives and an unknown
   ID; and
7. accept the resulting bytes through the normal ASTV-333 review and Beta
   route.

No production loader conversion, mixed legacy/v1 mode, or first-start rewrite is
permitted.

## Deployment order

The operator performs only an explicitly authorized sequence inside a declared
maintenance window in which callers do not invoke the Intent Gateway.

1. Confirm the recorded immediate-prior integration version and configuration
   bytes are recoverable.
2. Install the exact immutable HACS Beta tag for the integration. On first
   installation, do not restart Home Assistant or create the config entry yet.
   Installation alone is not proof that the action is registered.
3. Transfer the accepted schema-v1 catalogue and script adapter bytes to their
   exact `/config/**` targets without editing or transformation. Treat the
   accepted file set as one cutover unit.
4. Establish resulting target identity with hashes or byte comparison where
   available.
5. Run the Home Assistant-supported configuration check.
6. Only after a successful check and restart authority, restart Home Assistant.
   On an update, the existing config entry now loads the provider and activates
   schema v1. On a first installation there is no entry yet, so the new adapter
   remains intentionally unavailable during the maintenance window.
7. For a first installation, create the single config entry through Home
   Assistant UI after the restart. The setup reads the deterministic schema-v1
   target and publishes the initial active registry. Do not configure an
   arbitrary path.
8. Confirm the integration version, config-entry loaded state, action
   availability, schema/active identity, and absence of load errors.
9. Exercise the governed functional matrix below.
10. End the maintenance window only after the compatibility checks pass.

This order never asks the schema-v1-only provider to activate legacy bytes and
never asks the legacy direct-include script to interpret the v1 envelope. It
accepts a bounded first-installation interval in which the new script adapter
is present but lookup is unavailable; preventing gateway calls during that
interval is an explicit cutover responsibility, not an automatic fallback.

## Functional validation matrix

The deployed candidate must demonstrate:

- `classic_fm` returns the exact record-only shape through
  `script.astv_find_intent_record`;
- surrounding whitespace and mixed case normalize to the same record;
- an unknown ID returns `{}`;
- Intent Gateway retains its existing `No Intent Record Found` notification
  and non-error stop;
- one representative media intent preserves area resolution, intent routing,
  MediaCat handoff, and fixed dispatch contexts without requiring a terminal
  playback action where a safer isolated validation is available;
- the routine record remains unchanged;
- invalid refresh input cannot replace the active registry;
- the retained active revision and lookup result remain unchanged after that
  failed refresh; and
- restart with the valid persisted candidate rebuilds the expected active
  registry.

Live reference probes or management activation behavior not yet contracted by
ASTV-332 are not invented by this plan.

## Failure and paired rollback

Cutover fails closed on transfer ambiguity, failed byte verification, Home
Assistant configuration error, integration load/setup error, absent lookup
action, invalid initial catalogue, response incompatibility, or a failed
functional check.

Recovery restores a compatible implementation/data pair:

1. stop further progression and preserve non-secret diagnostics;
2. restore the exact prior `/config/**` bytes to every changed target;
3. restore the exact prior HACS integration version, or uninstall the candidate
   if the immediate prior state had no integration;
4. do not leave the schema-v1-only implementation paired with legacy bytes, or
   the legacy script paired with a provider-only catalogue path;
5. repeat the Home Assistant configuration check against the restored bytes;
6. restart or reload only with the required authority;
7. verify the restored integration/configuration state and one representative
   pre-cutover lookup; and
8. record the rollback target identities and final runtime status.

Branch names are not rollback identities. The HACS version/tag and exact prior
configuration bytes are the recovery identities.

A failed in-process catalogue refresh with a valid active snapshot is not by
itself a filesystem rollback: the provider retains the prior snapshot and the
failed candidate remains a persisted/admin concern. ASTV-332 will define
persistence restoration responsibilities.

## Deferred decisions

The following are deliberately outside ASTV-331:

- CRUD and candidate persistence;
- administration discovery/status operations;
- guarded mutations and revision concurrency;
- who initiates activation and through which management action;
- durable last-known-good storage across process restart;
- live MediaCat or AdvNFC reference probes;
- automated configuration transport; and
- production cutover authorization.

They require ASTV-332, ASTV-333, or ASTV-336 as identified above.
