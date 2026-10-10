# ASTV Intent Catalogue Integration Deployment and Recovery Runbook

**Status:** Current operator handoff under ASTV-336
**Integration release:** stable `v0.3.0` at
`b5d847ea9a7319f176c049f5980e7bab7e5442c0`
**Current `starburst` installation:** accepted HACS Beta
`v0.3.0-beta.da8e078` at
`da8e078c7814701b6b78ba8eb5c6f0f24c59bb3e`; eight original records; no
draft
**Runtime implementation:** ASTV-333, ASTV-334 and ASTV-335
**Interoperability and handoff:** ASTV-336

## Purpose and authority

This runbook is the ordered product-aware handoff for installing, updating,
validating and recovering the ASTV Intent Catalogue provider and its Home
Assistant configuration adapter. It does not authorize a deployment, restart,
catalogue mutation, activation, rollback or stable promotion.

The governing Linear issue, Central Governance, the Home Assistant Integration
Deployment Standard, the Home Assistant Configuration Deployment Standard and
`ASTV_HAOS_CONFIG_DEPLOYMENT_RUNBOOK.md` remain authoritative. An operator must
stop if the exact candidate, target, authority or recovery route is ambiguous.

The deployment contains two independently deployable units that form one
compatibility boundary for a first installation or schema cutover:

| Unit | Type | Governed source | Runtime target | Mechanism |
| --- | --- | --- | --- | --- |
| Catalogue provider integration | `haos_integration` | `custom_components/astv_intent_catalogue/**` | `/config/custom_components/astv_intent_catalogue/**` | HACS |
| Versioned catalogue and lookup adapter | `haos_config` | `04_Implementation/haos/source/config/astv/astv_intent_catalogue.yaml` and `04_Implementation/haos/source/config/packages/astv/astv_scripts.yaml` | matching `/config/**` paths | `operator_selected` |

The deterministic catalogue and draft paths are:

```text
/config/astv/astv_intent_catalogue.yaml
/config/astv/astv_intent_catalogue.draft.yaml
```
The draft is provider-owned mutable state. It is never repository source and
must not be copied into Git.

## Contract and interoperability baseline

The supported combination is:

| Identity | Required value or rule |
| --- | --- |
| Integration manifest version | `0.3.0` |
| Lookup interface | `astv.intent_catalogue.lookup` `1.0.0` |
| Administration interface | `astv.intent_catalogue.administration` `1.0.0` |
| Catalogue schema | `astv.intent_catalogue` `1.0.0` only |
| MediaCat lookup | provider-owned `mediacat.resolve_media_record`; current contract v2.2.0 |
| AdvNFC reverse query | discover from the deployed AdvNFC provider before use; ASTV neither provides nor stores it |

There is no mandatory ASTV manager. An authorized client may call the published
Home Assistant response actions directly after discovery. A manager must use
normalized records and opaque revisions; it must not read or write ASTV YAML or
depend on serialization.

MediaCat availability is required only for explicit activation of a draft that
contains media references. Missing `mediacat.resolve_media_record` or an
operational failure is `dependency_unavailable`; a registered action's explicit
well-formed not-found result is `activation_failed`. Diagnostic message parsing
is forbidden.

AdvNFC owns NFC assignments and reverse-reference lookup. A client may call the
deployed AdvNFC interface only after capability discovery advertises its query
operation, currently described as `advnfc.query_tag_mappings` with
`action_type: astv_intent` and `intent_id`. No matches is a successful empty
result. Missing, unavailable, unapproved or non-advertised AdvNFC query support
disables only dependent-reference display; it must not block ASTV validation,
staging, activation or runtime lookup, and must never cause ASTV to copy or
delete NFC mappings.

The ASTV-329 evidence reviewed an AdvNFC v3 candidate and recorded outstanding
authorization and common-error-mapping remediation in ASTV-337 and ASTV-338.
An operator or client must therefore discover and verify the actually deployed
AdvNFC interface rather than assume the candidate is available.

## Authorization boundary

ASTV administration actions use two classes:

- read: capabilities, status, list and get;
- manage: record/candidate validation, create, update, delete, discard and
  activate.

Manage actions use Home Assistant admin-service enforcement. A non-admin user
context is rejected before the ASTV handler runs. A trusted Home Assistant
system context without `user_id` is permitted by the platform helper. This is
not a promise that only a human administrator can invoke manage actions.

## Pre-deployment record and backup

Before any target change, record in the governing Linear issue or linked
authoritative evidence:

1. explicit authority, operator, target instance and maintenance window;
2. exact HACS tag/version and full commit SHA;
3. exact configuration candidate SHA, source paths and byte identities;
4. current installed integration version or confirmed absence;
5. current config-entry state and HACS update entity;
6. active, persisted and draft status/revisions where the current provider can
   report them;
7. immediate prior bytes and recovery location for the catalogue, optional
   draft and script adapter;
8. a Home Assistant backup that covers the affected integration/configuration
   state, where used, with backup identifier and capture time;
9. Home Assistant configuration-check route; and
10. restart impact and the exact rollback target.

Capture the immediate prior target state before overwrite or removal. A backup
name alone is not proof that all affected bytes are recoverable. Keep secrets,
tokens and backup keys out of Git and Linear.

For the current `starburst` state, the prior integration rollback identity is
`v0.3.0-beta.da8e078`, not `beta`, `main` or another moving branch name. Before
a future deployment, reconfirm this observation rather than treating this
runbook as fresh runtime evidence.

## Ordered deployment procedure

Perform only the steps covered by explicit authority.

1. Pause Intent Gateway callers for a first installation/schema cutover.
2. Verify the candidate identity, manifest version, HACS metadata and immutable
   tag-to-full-SHA mapping. Confirm the requested version exists and is not a
   moving branch or raw SHA.
3. Complete the pre-deployment record and verify restoration of the complete
   affected set, including any durable draft.
4. Verify `mediacat.resolve_media_record` is registered. This is an activation
   prerequisite, not an installation prerequisite.
5. Discover the deployed AdvNFC administration interface if reverse-reference
   display is part of the human test. Record an absent or non-advertised query
   as an optional prerequisite gap; do not invent compatible semantics.
6. Install or update the exact integration version through the verified
   HACS-created update entity. For a governed Beta use the immutable Beta tag in
   `update.install`; normal stable installation uses the published stable
   version.
7. For a first cutover, transfer the accepted schema-v1 catalogue and
   `astv_scripts.yaml` bytes to their deterministic `/config/**` targets without
   editing or transformation. For an update with unchanged configuration,
   record that no configuration transfer occurred.
8. Verify resulting configuration bytes with target-side hashes or byte
   comparison where available; otherwise record the strongest read-back and its
   limitation.
9. Run the Home Assistant-supported configuration check. Stop on error or an
   unresolved material warning.
10. Restart Home Assistant only with separate restart authority. On first
    installation, create the single ASTV Intent Catalogue config entry through
    Home Assistant UI after restart.
11. Confirm the exact installed HACS version/tag, loaded config entry, registered
    actions and absence of integration load errors.
12. Run the non-mutating smoke checks below before any staged mutation.
13. Run staged or activation tests only when separately authorized, using the
    human test plan and exact restoration checks below.
14. Resume callers only after the accepted checks pass or rollback completes.

The loader accepts only schema v1.0.0. It never infers or converts the legacy
unversioned document. A pre-v1 rollback restores the matching pre-v1
implementation and data bytes together.

## Non-mutating operator smoke checks

Request response data for every response-only action.

1. Call `astv_intent_catalogue.get_administration_capabilities` and verify the
   interface/schema identities, advertised operation map, `activation_applicable`
   and authorization classes.
2. Call `astv_intent_catalogue.get_administration_status` and verify provider,
   active and persisted availability; record active/persisted/draft revisions,
   counts, activation requirement and last activation error.
3. List the active records and verify the expected count and canonical ordering.
4. Get `classic_fm` and verify a record-only schema-v1 shape; get an unknown ID
   and verify administration `not_found` remains distinct from runtime lookup.
5. Run one valid record validation and one intentionally invalid structural
   validation. Confirm neither changes active, persisted or draft identity.
6. Call `astv_intent_catalogue.lookup` for `classic_fm`, mixed-case/whitespace
   `classic_fm`, and an unknown ID. Verify the unknown result is successful with
   `found: false` and `{}`.
7. Call `script.astv_find_intent_record` for the same known and unknown IDs and
   verify only the record or `{}` crosses the adapter.

These checks do not create a draft, activate a catalogue, invoke a routine or
perform media playback.

## Controlled administration test plan

These steps mutate provider state and require explicit catalogue-mutation and,
where applicable, activation authority. Reuse accepted ASTV-335 live evidence
when the exact immutable runtime state and criterion are unchanged; do not
repeat destructive failure injection merely to reproduce evidence.

1. Record status and the exact starting active/persisted/draft identities.
2. If a pre-existing draft exists, stop and obtain a decision from its owner;
   never overwrite or discard it as test setup.
3. Stage a uniquely named disposable `routine.run` record. Confirm the draft is
   durable, active lookup is unchanged and a stale revision is rejected.
4. Update the complete disposable record, then delete it from the draft. Confirm
   each successful response advances the draft revision and leaves active and
   persisted revisions unchanged.
5. Discard the now-redundant draft and verify no active/persisted change.
6. If activation testing is separately authorized, stage a disposable routine
   record again and activate the exact draft revision. Activation still probes
   every distinct existing MediaCat reference; verify all resolve.
7. Confirm successful activation makes active and persisted revisions equal,
   clears the draft, preserves every original record and adds only the
   disposable record.
8. Stage deletion of the disposable record, activate the exact restoration
   draft, and prove the starting normalized revision/count and representative
   `classic_fm` result are restored.
9. Query AdvNFC reverse references separately only if its deployed discovery
   advertises the operation. Verify no matches is empty success and the query
   causes no ASTV state change. Do not create or delete AdvNFC assignments.

ASTV-335 already supplies accepted live evidence for a MediaCat not-found
activation failure retaining active, persisted and draft state, a successful
activation, and exact restoration. Operational MediaCat outage, negative admin
context, torn write and crash-window cases remain automated-test evidence and
must not be injected into `starburst` without new explicit authority and a safe
need.

## Kitchen-only gateway/routing regression

Any live end-to-end ASTV regression under this handoff is limited to the
Kitchen area unless the user separately authorizes another area. The operator
must use a known existing intent and the least externally consequential path
available.

Verify:

- Intent Gateway accepts the unchanged invocation v1.0.0 request;
- area precedence resolves to Kitchen through the intended input;
- the record-only adapter does not leak provider identities or revisions;
- intent selection and fixed Execution Dispatch v4.1.0 contexts remain intact;
- MediaCat receives the contracted `catalogue_id`/`item_id` when the selected
  path requires it; and
- no terminal playback, Google action or routine is executed unless that exact
  external action is separately authorized.

An isolated script trace or stopped-before-terminal-action check is preferred
when it proves the regression criterion without audible playback or an external
side effect.

## Failure and exact rollback/recovery

Stop progression on ambiguous identity, failed transfer verification, failed
configuration check, integration load error, absent required action,
incompatible interface/schema identity, unexpected pre-existing draft, failed
smoke check or unexplained state change.

Recovery restores a compatible integration/configuration pair:

1. stop callers and preserve non-secret diagnostics;
2. identify whether failure occurred before or after an activation commit by
   reconciling status and persisted bytes;
3. restore the exact immediate-prior integration version through HACS, or
   uninstall the candidate if the prior state had no integration;
4. restore the exact prior catalogue, optional draft and adapter bytes to the
   same deterministic target paths;
5. never pair a schema-v1-only provider with legacy bytes or a legacy adapter
   with the provider-only schema-v1 catalogue;
6. verify restored bytes, run the Home Assistant configuration check and then
   restart/reload only with the required authority;
7. verify the restored installed version, config entry, actions, status and one
   representative lookup; and
8. record rollback identities, transport, validation result and final runtime
   state.

A failed pre-commit activation normally needs no filesystem rollback: the
previous active and persisted state and exact draft are retained for correction
or discard. A process loss after the commit point is reconciled from persisted
state after restart. Branch names are never rollback identities.

## Human handoff checklist

Copy this checklist into the governing issue or linked evidence. Do not record
secrets.

```text
Authority / governing issue:
Authorised operator and time:
Target instance/environment: starburst / <environment>
Maintenance window and caller pause:

Integration tag/version and full SHA:
Manifest version and HACS metadata verified:
Prior installed version/tag:
HACS update entity:

Configuration candidate SHA and exact source paths:
Exact target paths:
Source/target byte identities:
Transport used:

Immediate prior-state capture and backup identity:
Prior catalogue/draft/adapter identities and recovery locations:
Rollback route confirmed:

Configuration-check route/time/result:
Restart/reload authority and result:
Installed version and config-entry state:

Capabilities/status/list/get/validation smoke results:
Lookup and script-adapter smoke results:
MediaCat availability/reference result:
AdvNFC discovered query capability or explicit optional gap:
Kitchen-only routing result, if separately authorised:

Staged mutation/activation authority and results, if applicable:
Exact restored active/persisted/draft identities:
Rollback invoked and result:
Unresolved conditions:
```
