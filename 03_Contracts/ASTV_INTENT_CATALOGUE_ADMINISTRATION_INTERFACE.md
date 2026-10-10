# ASTV Intent Catalogue Administration Interface

**Interface ID:** astv.intent_catalogue.administration  
**Interface version:** 1.0.0  
**Schema ID/version:** astv.intent_catalogue / 1.0.0  
**Status:** Current v1.0.0 interface with explicit activation; runtime-active on
`starburst` through the accepted HACS Beta `v0.3.0-beta.da8e078`; stable
integration release `v0.3.0` published but not installed on `starburst`
**Provider:** ASTV  
**Authoritative location:** 03_Contracts/ASTV_INTENT_CATALOGUE_ADMINISTRATION_INTERFACE.md

## Purpose, authority and boundaries

This is the ASTV-owned administration contract for the Intent Catalogue. It conforms to Product Administration Interface Standard v1.0.0 and is independent of the runtime read interface astv.intent_catalogue.lookup v1.0.0.

The interface exposes normalized catalogue records and state identities. It does not expose or accept YAML, filenames, paths, parser objects, Home Assistant storage records, backup locations or credentials. ASTV owns the schema, draft, persistence, validation, activation and concurrency boundary. A client owns its presentation and workflow.

This contract does not change Intent Invocation v1.0.0, Execution Dispatch v4.1.0, the record-only script adapter, lookup normalization, unknown-runtime-ID behavior, area resolution, MediaCat runtime lookup, or execution selection. It authorizes no implementation, deployment, migration or production change.

## Transport and registration

All operations are Home Assistant response-only actions in domain astv_intent_catalogue and use SupportsResponse.ONLY. A caller must make a blocking call and request response data. Actions are registered from integration async_setup; each handler verifies that the single config entry and required provider state are available.

Calls that reach an ASTV handler return a JSON-serializable response with ok and the common identity fields. Expected provider outcomes return structured ok: false responses. Home Assistant itself raises native errors before a provider response for an absent action, invalid top-level service schema, failure to request a required response, or rejected authorization. Unexpected implementation faults also raise a Home Assistant error and must not be converted to a misleading provider outcome.

The interface does not claim that Home Assistant transports a provider error code when Home Assistant rejects a call before the handler. The transport mapping below is part of this contract.

## Authorization

Operations have two authorization classes:

| Class | Operations | Enforced boundary |
| --- | --- | --- |
| read | capabilities, status, list, get | ordinary Home Assistant action registration; callable by contexts allowed to call the action |
| manage | both validation operations, create, update, delete, discard and, when advertised, activate | Home Assistant async_register_admin_service |

For a user-originated manage call, Home Assistant resolves call.context.user_id and rejects an unknown or non-administrator user before the ASTV handler runs. The current helper deliberately permits a trusted system context whose user_id is absent. Therefore “manage” means Home Assistant admin-service semantics, not a separately configurable role and not “a human administrator only.” Internal automations with a system context can invoke manage actions. A deployment that must prohibit such automation calls requires a separately designed authorization mechanism and must not claim that this contract already supplies it.

Read operations return non-secret normalized records. Manage validation can reveal protected candidate content and is admin-service protected. No response or diagnostic may include secrets, tokens, protected paths or complete serialized storage bytes.

## Capability and operation catalogue

| Capability | Action | Authorization | Request |
| --- | --- | --- | --- |
| discovery | get_administration_capabilities | read | empty |
| status | get_administration_status | read | empty |
| active list | list_intent_records | read | optional limit, cursor |
| active get | get_intent_record | read | intent_id |
| record validation | validate_intent_record | manage | intent_id, record |
| complete validation | validate_intent_catalogue | manage | candidate |
| staged create | create_intent_record | manage | expected_revision, intent_id, record |
| staged update | update_intent_record | manage | expected_revision, intent_id, record |
| staged delete | delete_intent_record | manage | expected_revision, intent_id |
| draft discard | discard_intent_catalogue_draft | manage | expected_revision |
| activation | activate_intent_catalogue | manage | expected_revision |

Discovery advertises only operations that are implemented, registered and callable in the installed provider release. Interface v1.0.0 initially advertised this ASTV-334 set:

- discovery
- status
- active.list
- active.get
- validation.record
- validation.candidate
- draft.create
- draft.update
- draft.delete
- draft.discard
- concurrency.expected_revision

ASTV-335 added `activation.explicit`,
`references.mediacat.activation_check` and the `activate` operation mapping after
`activate_intent_catalogue` was implemented, registered and tested. A provider
must not advertise a placeholder or an operation that Home Assistant cannot
call. This capability addition is backward-compatible within interface major
version 1: discovery already defines capabilities and operations as the
negotiated optional set, existing required meanings and operations do not
change, and consumers must ignore unknown optional capabilities.

AdvNFC reverse-reference discovery is not an ASTV operation and is not advertised as an ASTV capability.

Every response produced by ASTV contains:

~~~yaml
ok: true | false
interface_id: astv.intent_catalogue.administration
interface_version: "1.0.0"
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
~~~

Unknown optional fields must be ignored by consumers.

## Discovery

Action: astv_intent_catalogue.get_administration_capabilities

Request: empty.

Successful response:

~~~yaml
ok: true
interface_id: astv.intent_catalogue.administration
interface_version: "1.0.0"
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
mode: managed
mutation_supported: true
activation_applicable: false
authorization:
  read: home_assistant_service_call
  manage: home_assistant_admin_service
capabilities:
  - discovery
  - status
  - active.list
  - active.get
  - validation.record
  - validation.candidate
  - draft.create
  - draft.update
  - draft.delete
  - draft.discard
  - concurrency.expected_revision
operations:
  discovery: get_administration_capabilities
  status: get_administration_status
  active_list: list_intent_records
  active_get: get_intent_record
  validate_record: validate_intent_record
  validate_candidate: validate_intent_catalogue
  create: create_intent_record
  update: update_intent_record
  delete: delete_intent_record
  discard: discard_intent_catalogue_draft
limits:
  list_default: 100
  list_maximum: 200
~~~

Discovery reports the contract, not provider health. It remains available after action registration when the config entry, active state or persistence layer is unavailable.

The current v0.3.0 implementation reports `activation_applicable: true` and
advertises the activation capabilities and callable operation mapping. The
historical ASTV-334 v0.2.0 implementation reported false because it exposed no
callable activation operation.

## State identities and status

The identities are independent:

| Identity | Meaning |
| --- | --- |
| integration release version | installed HACS implementation |
| interface_version | this external administration contract |
| schema_version | normalized catalogue vocabulary |
| active_revision | immutable in-memory registry currently serving runtime lookup |
| persisted_revision | complete authoritative catalogue durable at the runtime startup source |
| draft_revision | complete durable shared candidate being edited; null when no draft |
| editable_revision | revision a guarded mutation must supply: draft_revision when a draft exists, otherwise active_revision |

Revisions are opaque, non-empty strings. A consumer may compare only for equality. A revision must not encode a promised sequence, timestamp, schema or release version. Equal revision values mean equal normalized complete catalogue content within this provider version; serialization-only differences do not change equality.

Action: astv_intent_catalogue.get_administration_status

Successful response includes:

~~~yaml
ok: true
interface_id: astv.intent_catalogue.administration
interface_version: "1.0.0"
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
provider_state: available
active_state: available
persisted_state: valid
draft_state: absent
active_revision: <revision or null>
persisted_revision: <revision or null>
draft_revision: <revision or null>
editable_revision: <revision or null>
activation_required: false
active_count: <integer or null>
persisted_count: <integer or null>
draft_count: <integer or null>
last_activation_error: null
~~~

Enumerated states are:

- provider_state: available or unavailable.
- active_state: available or unavailable.
- persisted_state: valid, invalid or unavailable.
- draft_state: absent, valid, invalid or unavailable.

activation_required is true exactly when a valid draft exists and its normalized content differs from active content. A redundant valid draft equal to active is still reported, but activation_required is false and discard remains available. Persisted and active may temporarily differ after an externally changed file, provider reload failure or interrupted activation; status must report the actual identities and must not imply that persisted is active.

last_activation_error is null or a detached mapping with code, refinement, message and observed_at. It is cleared only by successful activation of the intended draft or explicit discard of that draft. It contains no secret or path.

Status itself returns ok: true when the handler can inspect administration state, including degraded state. It returns dependency_unavailable only when administration state cannot be inspected at all.

## Active list and get

Action: astv_intent_catalogue.list_intent_records

Request:

~~~yaml
limit: 100
cursor: <opaque cursor, optional>
~~~

limit defaults to 100 and must be an integer from 1 through 200. Results are ordered by canonical intent_id in ascending Unicode code-point order. A cursor is opaque and bound to one active_revision and last returned ID. Use of a cursor after active_revision changes returns stale_revision. No cursor means the first page.

Success returns active_revision, count for this page, total_count, records as entries containing intent_id and record, and next_cursor or null. No active registry returns dependency_unavailable. Response records and nested values are defensive copies.

Action: astv_intent_catalogue.get_intent_record

Request contains scalar intent_id. Get applies the runtime-compatible normalization string(value).trim().lower(). Null, mappings and sequences are invalid_request. Blank after normalization is invalid_request for administration get. A known ID returns normalized_intent_id, active_revision and record. A valid absent ID returns not_found; it is not an empty successful record. This differs intentionally from runtime lookup, whose found: false behavior remains unchanged.

## Normalized candidate shape

Operations accept records, never serialized documents.

A complete candidate is:

~~~yaml
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
records:
  <canonical_intent_id>:
    <record mapping from ASTV_INTENT_CATALOGUE_SCHEMA.md>
~~~

The request mapping is a normalized logical model, not a promise about storage serialization. Mapping order has no meaning.

For validation and mutation, intent_id must already be a canonical string satisfying the schema. ASTV does not trim, lowercase or rename a persisted identifier. A record does not contain a synthesized intent_id.

## Side-effect-free validation

Action: astv_intent_catalogue.validate_intent_record

The handler validates intent_id and record as one keyed schema-v1 record. Success returns valid: true, canonical intent_id and errors: []. Failure returns invalid_request with refinement invalid_record and an ordered errors array. The operation does not read or change draft, persisted or active state and does not probe MediaCat.

Action: astv_intent_catalogue.validate_intent_catalogue

The handler validates the complete normalized candidate: exact schema identity/version, at least one record, identifiers, closed record shapes, duplicate normalized IDs and every record. Success returns valid: true, record_count, candidate_revision and errors: []. candidate_revision is informational identity for the supplied normalized content and does not imply persistence. Failure returns invalid_request with refinement invalid_candidate and deterministic errors.

Validation errors contain path, code and message. Clients branch on error.code and error.refinement; messages are diagnostic. Validation is all-or-nothing, but the response may report multiple independent violations found during one side-effect-free pass.

## Shared durable draft and guarded mutation

There is exactly one provider-wide durable draft, shared by every client. There are no per-user sessions.

All mutation handlers take the provider administration lock and apply this order:

1. enforce manage authorization and top-level request schema;
2. read current draft and active identities;
3. compare expected_revision with editable_revision;
4. clone the complete active snapshot when no draft exists, otherwise clone the complete draft;
5. apply the requested complete-record operation;
6. validate the complete resulting schema-v1 candidate;
7. persist the complete draft with atomic replacement; and
8. publish the new draft_revision in status.

A stale comparison returns stale_revision before record-existence checks and has no side effect. A failed semantic check, complete-candidate validation or atomic write leaves draft, persisted and active state unchanged.

The first accepted edit always initializes from the active snapshot. If no valid active snapshot exists, create/update/delete return dependency_unavailable with refinement active_state_unavailable. Recovery then requires restoration of a valid compatible persisted catalogue and provider setup; this interface does not invent an empty production catalogue.

create_intent_record requires a canonical intent_id absent from the editable candidate and a complete record. An existing ID returns invalid_request with refinement already_exists.

update_intent_record requires a canonical intent_id present in the editable candidate and replaces the complete record. Absence returns not_found.

delete_intent_record requires a canonical intent_id present in the editable candidate. Deletion is staged only. Deleting the final record would violate schema v1 and returns invalid_request with refinement invalid_candidate.

Successful mutation returns operation, intent_id, prior_revision, draft_revision, draft_count, active_revision and activation_required: true. It never changes active_revision or persisted_revision.

Restart preserves a valid draft and its revision. Provider reload must reacquire active, persisted and draft state under the same rules and must not silently activate or discard the draft. An invalid or unreadable draft is reported through status; mutation and activation are refused until it is discarded or the provider-owned storage is recovered.

## Discard

Action: astv_intent_catalogue.discard_intent_catalogue_draft

expected_revision must equal current draft_revision. When no draft exists, return not_found with refinement draft_not_found. A stale value returns stale_revision. Success atomically removes only the draft and returns draft_revision: null, activation_required: false and editable_revision equal to active_revision. Active and persisted state do not change.

A readable but schema-invalid draft still has an opaque byte/content identity and may be discarded using the revision reported by status. If no reliable draft revision can be established because storage is unavailable, discard returns dependency_unavailable; operator recovery is required.

## Activation and atomicity

Action: astv_intent_catalogue.activate_intent_catalogue

expected_revision must equal the current draft_revision. No draft returns not_found; a mismatch returns stale_revision. Activation runs under the administration lock:

1. read the exact durable draft named by expected_revision;
2. parse and validate the complete schema-v1 candidate;
3. construct the complete deeply immutable registry off to the side;
4. verify every distinct MediaCat reference as described below;
5. prepare the provider-owned atomic replacement of the authoritative persisted catalogue;
6. atomically replace persisted state from the durable draft; this replacement is the activation commit point and consumes the draft;
7. without awaiting further work, replace the single active registry reference on the Home Assistant event loop; and
8. record success and clear last_activation_error.

No step before the commit point changes persisted or active state or removes the draft. Any expected failure before the commit point returns activation_failed, retains the previous active and persisted revisions, and retains the exact draft for correction or retry.

The implementation must make step 6 a single provider-owned atomic replace/rename, not an in-place write and not two independently visible writes. The candidate registry is fully built before the commit point. The step-7 operation is a non-awaiting reference assignment and is not permitted to perform validation, I/O or dependency work.

A process crash after the commit point but before a response can make the caller's outcome unknown. On restart the normal ASTV-331 cold-start rule validates the committed persisted candidate before publishing it. Status is the reconciliation authority. The provider must never claim that a response was delivered when it was not.

Successful activation returns equal active_revision and persisted_revision, draft_revision: null, activation_required: false, active_count and operation: activate. Existing lookup calls observe either the complete old registry before the swap or the complete new registry afterward.

Activation failure is not a filesystem-history or backup rollback feature. The draft enables correction and retry before commit. Deployment rollback remains restoration of a compatible implementation/data pair under the governed deployment route.

## MediaCat reference verification

ASTV owns reference syntax and the decision to activate. MediaCat owns catalogue/item existence and lookup behavior.

Activation must verify every distinct media.play_source pair through the published mediacat.resolve_media_record action. The provider first checks that the action is registered. If it is absent, activation returns dependency_unavailable with refinement mediacat_unavailable, retains draft/persisted/active state and does not report a missing item.

At the verified design baseline, structurally valid MediaCat requests have these distinguishable outcomes:

- a successful response resolves the target;
- ServiceValidationError from the registered action represents the published explicit catalogue/item not-found path and becomes activation_failed with refinement referenced_target_not_found and per-reference errors;
- service absence or another operational Home Assistant error becomes dependency_unavailable with refinement mediacat_unavailable.

ASTV-335 must reverify this distinction against its exact MediaCat implementation baseline. If MediaCat no longer provides a deterministic distinction, ASTV must not advertise or implement activation until a provider contract/implementation change restores it. Diagnostic message parsing is forbidden.

References are deduplicated before probing. All targets must resolve. No partial activation, fallback catalogue, automatic reference deletion or cached MediaCat record is permitted. MediaCat response contents are not copied into the ASTV catalogue.

## AdvNFC reverse-reference boundary

AdvNFC owns stored NFC mappings and reverse-reference query. ASTV does not mirror, cache or validate AdvNFC mapping state during record mutation or activation.

A manager may separately discover mappings through AdvNFC's advertised query operation for action_type astv_intent and intent_id. No matches is a successful empty AdvNFC result. If AdvNFC is absent, unavailable or does not advertise that query, only dependent reference discovery is unavailable; ASTV validation, CRUD, activation and runtime behavior remain unchanged. Removing an ASTV record does not remove or rewrite an AdvNFC mapping.

## Operation outcome matrix

All failure rows mean ok: false with the named common code and no state change unless the row explicitly describes native Home Assistant rejection before the handler.

| Action | Required success fields beyond common identity | Expected provider failures |
| --- | --- | --- |
| get_administration_capabilities | mode, authorization, capabilities, operations, limits | none while action is registered |
| get_administration_status | four state fields, four revision fields, activation_required, counts, last_activation_error | dependency_unavailable only when state cannot be inspected |
| list_intent_records | active_revision, count, total_count, records, next_cursor | invalid_request, stale_revision, dependency_unavailable |
| get_intent_record | normalized_intent_id, active_revision, record | invalid_request, not_found, dependency_unavailable |
| validate_intent_record | valid, intent_id, errors | invalid_request/invalid_record |
| validate_intent_catalogue | valid, record_count, candidate_revision, errors | invalid_request/invalid_candidate |
| create_intent_record | operation: create, intent_id, prior_revision, draft_revision, draft_count, active_revision, activation_required | stale_revision, invalid_request/already_exists, invalid_request/invalid_candidate, dependency_unavailable |
| update_intent_record | operation: update plus the same revision/count fields | stale_revision, not_found, invalid_request/invalid_candidate, dependency_unavailable |
| delete_intent_record | operation: delete plus the same revision/count fields | stale_revision, not_found, invalid_request/invalid_candidate, dependency_unavailable |
| discard_intent_catalogue_draft | operation: discard, prior_revision, draft_revision: null, editable_revision, active_revision, activation_required: false | stale_revision, not_found/draft_not_found, dependency_unavailable |
| activate_intent_catalogue | operation: activate, equal active/persisted revisions, draft_revision: null, active_count, activation_required: false | stale_revision, not_found/draft_not_found, dependency_unavailable, activation_failed |

Example guarded create success:

~~~yaml
ok: true
interface_id: astv.intent_catalogue.administration
interface_version: "1.0.0"
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
operation: create
intent_id: evening_news
prior_revision: rev-a
draft_revision: rev-b
draft_count: 9
active_revision: rev-a
activation_required: true
~~~

Example stale write:

~~~yaml
ok: false
interface_id: astv.intent_catalogue.administration
interface_version: "1.0.0"
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
active_revision: rev-a
draft_revision: rev-c
editable_revision: rev-c
error:
  code: stale_revision
  refinement: stale_edit_revision
  message: The candidate changed; refresh status before retrying.
~~~

Example failed activation retains the draft:

~~~yaml
ok: false
interface_id: astv.intent_catalogue.administration
interface_version: "1.0.0"
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
active_revision: rev-a
persisted_revision: rev-a
draft_revision: rev-b
activation_required: true
error:
  code: activation_failed
  refinement: referenced_target_not_found
  message: One or more MediaCat targets could not be resolved.
~~~

## Dependency failure table

| Condition | Contract classification | Required effect |
| --- | --- | --- |
| ASTV action not registered | Home Assistant ServiceNotFound; common dependency_unavailable mapping | no provider response; no state change |
| ASTV action registered but config entry/state unavailable | dependency_unavailable/provider_state_unavailable | discovery remains usable; affected operation fails |
| no active registry after cold-start validation failure | dependency_unavailable/active_state_unavailable | list/get and first edit unavailable; no legacy or partial lookup |
| persisted catalogue invalid/unavailable while active remains | degraded status; activation_required reflects draft | active lookup continues; draft may be initialized from active; activation may repair persisted state |
| draft invalid | degraded draft_state | active lookup continues; mutation/activation blocked; guarded discard or operator recovery |
| draft persistence atomic replace fails | dependency_unavailable/persistence_unavailable | active, persisted and prior draft remain unchanged |
| MediaCat action absent | dependency_unavailable/mediacat_unavailable | activation fails before commit; never report item not-found |
| MediaCat valid reference explicitly absent | activation_failed/referenced_target_not_found | activation fails before commit; draft retained |
| MediaCat registered action has operational failure | dependency_unavailable/mediacat_unavailable | activation fails before commit; draft retained |
| AdvNFC absent or query unsupported | dependent reference discovery unavailable only | no effect on ASTV validation, staging, activation or runtime |
| Home Assistant restarts with valid persisted A and draft B | normal recovery | A becomes active after complete validation; B remains staged |
| crash after activation commit point | outcome unknown to caller | restart validates committed persisted state; status reconciles identity |

## Error model

A provider failure response is:

~~~yaml
ok: false
interface_id: astv.intent_catalogue.administration
interface_version: "1.0.0"
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
error:
  code: <common category>
  refinement: <optional stable ASTV refinement>
  message: <diagnostic>
~~~

| Common code | Representative refinements and use |
| --- | --- |
| invalid_request | invalid_record, invalid_candidate, already_exists, invalid_cursor, invalid_limit |
| not_found | intent_not_found, draft_not_found |
| permission_denied | mapping for native Unauthorized; normally no provider envelope |
| unsupported_operation | operation not advertised for negotiated version |
| stale_revision | stale_edit_revision, stale_draft_revision, stale_cursor |
| dependency_unavailable | provider_state_unavailable, persistence_unavailable, active_state_unavailable, mediacat_unavailable |
| activation_failed | referenced_target_not_found, candidate_invalid, persisted_replace_failed |

Transport/schema rejection raises ServiceValidationError. Manage rejection raises Unauthorized. Missing action raises ServiceNotFound. Consumers must map those native conditions to invalid_request, permission_denied and dependency_unavailable respectively when presenting the common model. They must not parse diagnostic message text.

A failed operation is never returned as partial success. If an unexpected error occurs after the activation commit point, status determines committed state; this is outcome reconciliation, not a partial provider response.

## State transitions

| Start | Operation/outcome | End |
| --- | --- | --- |
| active A, no draft | first guarded edit succeeds | active A; persisted unchanged; draft B |
| active A, draft B | later guarded edit succeeds | active A; draft C |
| active A, draft B | stale edit | unchanged |
| active A, draft B | discard succeeds | active A; no draft |
| active A, draft B | validation or MediaCat preflight fails | active A; persisted unchanged; draft B retained |
| active A, draft B | activation succeeds | active B; persisted B; no draft |
| no active | edit or activate | rejected; recovery required |
| restart with active-source A and draft B | setup succeeds | active A; draft B retained |

## Contract cases and future test obligations

ASTV-333 and ASTV-334 must provide automated evidence for at least:

- discovery identity, exact advertised capabilities and unknown-field tolerance;
- read versus manage registration and admin/non-admin/system-context behavior;
- response-only invocation and JSON serialization;
- list ordering, page boundaries, cursor binding and detached nested responses;
- get normalization, blank input, found and not-found outcomes;
- every schema-v1 record and complete-candidate positive/negative case;
- side-effect-free validation;
- first-edit cloning, durable restart, create/update/delete and final-record rejection;
- two-writer stale rejection with no write;
- atomic draft replacement and injected write failure;
- discard success, absent draft, stale discard and invalid-draft recovery;
- failed cold start with no active state and successful in-process failure retention;
- native Home Assistant exception mapping; and
- unchanged Intent Invocation, lookup adapter and Execution Dispatch contracts.

ASTV-335 must provide automated evidence for at least:

- activation success with old-or-new reader visibility only;
- failure before commit retaining active, persisted and draft identities;
- action absence versus MediaCat not-found versus operational failure;
- deduplicated MediaCat probes and all-reference requirement;
- callable-only activation discovery; and
- manager interoperability without depending on storage serialization.

ASTV-336 must verify exact implementation/data versions, restart recovery, dependency failure isolation and compatible paired rollback before deployment handoff.

## Compatibility and evolution

Interface, schema, integration release and revisions evolve independently. Adding optional fields, capabilities or operations is compatible within major version 1 when existing required meanings remain intact. Consumers discover before invoking and ignore unknown optional fields.

Removing or renaming an operation/required field, changing an input type or normalization, weakening atomicity or retained-state guarantees, changing revision equality, changing authorization class, replacing a stable common code/refinement, or changing list/get absence semantics requires a new interface major version and consumer impact assessment.

A schema version change is not automatically an interface break, but the supported schema set and normalized record contract must be advertised. Version 1.0.0 supports only schema 1.0.0.

Legacy unversioned catalogue data is never inferred or accepted by this interface. Initial migration remains an explicit governed conversion and deployment. Rollback restores the matching pre-v1 implementation and prior data together; it does not ask a schema-v1 provider to interpret legacy bytes.

## Verified evidence

Design evidence was checked on 2026-10-09 against:

- Product Administration Interface Standard v1.0.0;
- ASTV schema 1.0.0, lookup interface 1.0.0 and approved ASTV-331 registry design;
- Home Assistant core dev commit 35c3bbd5a0c299e4c31d23d2bd75f55576077d7e, including homeassistant/core.py, homeassistant/helpers/service.py and homeassistant/exceptions.py;
- Home Assistant developer guidance for integration action registration and response actions;
- MediaCat Item Lookup Interface 2.2.0 and MediaCat main implementation of mediacat.resolve_media_record reviewed on 2026-10-09; and
- AdvNFC Administration Interface candidate version 3 reverse query contract reviewed on 2026-10-09.

The Home Assistant source shows SupportsResponse.ONLY requires response data, ServiceRegistry raises ServiceNotFound for an absent action, async_register_admin_service rejects non-admin user contexts but permits a context without user_id, and ServiceValidationError/Unauthorized are native error transports. These source identities are design evidence, not permanent runtime pins; implementation issues must reverify their own baselines.
