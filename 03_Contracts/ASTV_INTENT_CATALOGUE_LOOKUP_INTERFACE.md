# ASTV Intent Catalogue Lookup Interface

**Interface ID:** `astv.intent_catalogue.lookup`  
**Interface version:** `1.0.0`  
**Status:** Proposed under ASTV-331; not runtime-active  
**Provider:** ASTV  
**Authoritative location:** `03_Contracts/ASTV_INTENT_CATALOGUE_LOOKUP_INTERFACE.md`

## Purpose and boundary

This contract defines the read-only provider boundary used to resolve one ASTV
intent-catalogue record from the provider's immutable active snapshot.

It is a runtime lookup interface, not the catalogue administration interface.
It does not define persistence, CRUD, candidate staging, activation commands,
history, or restoration. ASTV-332 owns those administration decisions.

The sole initial consumer is the ASTV-owned
`script.astv_find_intent_record` compatibility adapter. The provider returns a
lookup envelope; the adapter returns only the record to the existing Intent
Gateway.

## Home Assistant action

```text
astv_intent_catalogue.lookup
```

The action is read-only and is registered with
`SupportsResponse.ONLY`. A caller must request response data. The response
must be a JSON-serializable mapping.

The custom integration domain and source location are:

```text
domain: astv_intent_catalogue
source: custom_components/astv_intent_catalogue/
runtime target: /config/custom_components/astv_intent_catalogue/
```

ASTV-333 will implement and package this boundary. No implementation or
deployment is authorized by this contract.

## Request

```yaml
intent_id: <lookup value>
```

| Field | Presence | Rule |
| --- | --- | --- |
| `intent_id` | Required | Scalar value accepted by the existing Home Assistant/Jinja string conversion; mappings, sequences and null are invalid. |

Normalization is exact and locale-independent:

```text
normalized_intent_id = string(intent_id).trim().lower()
```

A blank normalized value is a valid lookup that produces an absent result. This
preserves the existing adapter behavior. The provider performs normalization
even though the initial script adapter also supplies the normalized value.

Persisted identifiers are already canonical under
`ASTV_INTENT_CATALOGUE_SCHEMA.md`; lookup never rewrites stored keys or
records.

## Successful response envelope

Every completed lookup returns:

```yaml
ok: true
interface_id: astv.intent_catalogue.lookup
interface_version: "1.0.0"
schema_id: astv.intent_catalogue
schema_version: "1.0.0"
active_revision: <opaque non-empty string>
normalized_intent_id: <normalized string>
found: true | false
record: <record mapping or {}>
```

| Field | Rule |
| --- | --- |
| `ok` | Always `true` for a completed lookup. Operational failure is raised as a Home Assistant action error and does not return a failure envelope. |
| `interface_id` | Exactly `astv.intent_catalogue.lookup`. |
| `interface_version` | Exactly `"1.0.0"`. Independent of schema and integration versions. |
| `schema_id` | Exactly `astv.intent_catalogue`. |
| `schema_version` | Version of the active validated snapshot; initially exactly `"1.0.0"`. |
| `active_revision` | Opaque identity of the active complete candidate. Consumers compare only for equality. |
| `normalized_intent_id` | Exact value used as the registry key. |
| `found` | `true` only when the normalized key exists. |
| `record` | Complete selected record, or `{}` when `found: false`. |

A found response does not synthesize `intent_id` inside `record`. The record
shape is exactly the runtime record defined by the schema contract. The
response value must be detached or deeply immutable so a caller cannot mutate
the provider's active snapshot.

An absent ID is an expected negative result, not `not_found`:

```yaml
ok: true
found: false
record: {}
```

This choice preserves the current lookup semantics and lets the Intent Gateway
retain its existing notification and non-error stop.

## Adapter compatibility contract

After ASTV-333 cutover, `script.astv_find_intent_record` will:

1. normalize its input with the existing string/trim/lower expression;
2. call `astv_intent_catalogue.lookup` and capture the response;
3. return only `response.record` when the response is successful and
   consistent; and
4. return `{}` for `found: false`.

It will not pass the provider envelope, normalized ID, active revision, schema
identity, or interface identity downstream.

The following remain unchanged:

- `script.astv_intent_gateway` calls the adapter and captures
  `intent_record_response`;
- an unknown ID causes the existing `No Intent Record Found` notification and
  a non-error stop;
- area precedence is unchanged;
- intent routing receives the complete record only;
- the fixed Execution Dispatch v4.1.0 contexts are unchanged; and
- no automatic retry, fallback, or alternative intent is introduced.

The adapter must not catch an operational provider failure and convert it to
`{}`. Doing so would falsely turn provider unavailability into an unknown ID.

## Provider availability and lifecycle

Home Assistant does not register an installed custom integration's actions
before the integration is loaded. The supported lifecycle is:

1. HACS installs an immutable integration version.
2. The operator creates the single config entry through Home Assistant UI.
3. On integration load, `async_setup` registers the lookup action so
   automations can be validated even if entry setup later fails.
4. `async_setup_entry` reads the deterministic persisted catalogue path,
   validates the complete candidate and publishes the initial active snapshot.
5. The handler validates that the single config entry is loaded and an active
   snapshot exists before serving a lookup.
6. Normal Home Assistant restart repeats steps 3–5. No in-memory state survives
   a restart.

If the integration has never been configured or Home Assistant has not loaded
it, the action is absent and Home Assistant raises its normal service-not-found
error. If the action is registered but the entry or active snapshot is
unavailable, the handler raises a translated `ServiceValidationError` or
equivalent Home Assistant error. Neither condition is an absent intent ID.

The lookup action remains registered by `async_setup`; it is not registered
and removed per config-entry load/unload. Unload releases the active registry
and makes subsequent calls fail availability validation until setup succeeds
again.

## Registry and transactional refresh guarantees

The provider owns one active registry object containing:

- schema identity and version;
- opaque active revision; and
- the complete mapping of normalized ID to deeply immutable record.

Initial setup and every later refresh use the same sequence:

1. read a complete candidate and derive its persisted identity;
2. parse with duplicate-key detection;
3. require the exact current schema envelope;
4. validate every key and record;
5. construct and deeply freeze a complete candidate registry;
6. run all preflight checks applicable to the requested operation; and
7. replace the single active registry reference on the Home Assistant event
   loop.

No step before 7 changes active state.

### Invalid initial load

At cold startup there is no prior active in-memory snapshot. Failure at steps
1–6 fails config-entry setup, leaves active state absent, and makes lookup
unavailable. The provider does not infer legacy shape, partially load records,
or recover stale state from memory.

### Failed in-process refresh

When a valid active snapshot exists, failure at steps 1–6 leaves that snapshot,
its records, schema version, and active revision unchanged. The refresh reports
failure to its invoker. Lookup continues from the retained snapshot.

The mechanism that requests an administrative refresh or activation, and the
complete administration outcome/status contract, are deferred to ASTV-332.
ASTV-331 defines only the registry invariant that those operations must
preserve.

## Authorization

The lookup exposes non-secret catalogue records and has no entity target. It is
not registered as an admin-only action. It is available to Home Assistant
contexts permitted to call actions, including internal automations whose
context has no user ID.

Home Assistant does not provide a generic per-service read permission equivalent
to its admin-service wrapper. The provider therefore cannot promise a finer
read role at this transport boundary. Future mutation, staging, activation, and
protected validation actions must enforce manage authority at the provider
boundary as defined by ASTV-332.

Responses and diagnostics must not expose credentials, secrets, backup
locations, protected internal paths, or complete persisted file bytes.

## Failure mapping

Home Assistant's response-action guidance requires operational errors to be
raised as exceptions rather than returned as error-code response data.
Accordingly, a completed lookup returns only `ok: true`; failures use native
action errors.

This lookup is not the conforming administration interface governed by ASTV-332.
The following mapping nevertheless preserves the common administration
vocabulary without changing Home Assistant transport behavior:

| Condition | Common category | Lookup behavior |
| --- | --- | --- |
| Request has missing, null, mapping or sequence `intent_id` | `invalid_request` | Service schema or handler raises `ServiceValidationError`. |
| Normalized ID is absent | Expected negative result | Successful `found: false`, `record: {}`; not an error. |
| Config entry or active snapshot unavailable | `dependency_unavailable` | Handler raises a translated Home Assistant error. |
| Caller lacks platform authority to call the action | `permission_denied` | Home Assistant rejects the call before or at the provider boundary. |
| Candidate refresh fails while an active snapshot exists | `activation_failed` | Refresh invoker receives failure; lookup keeps serving the prior snapshot. |
| Integration/action is not installed, configured or loaded | Outside provider response | Home Assistant service-not-found behavior. |

Diagnostic message text is not a machine contract. ASTV-332 may expose
structured administration outcomes and provider-specific refinements; it must
not change this runtime lookup behavior silently.

## Compatibility and versioning

The lookup interface version, catalogue schema version, integration release
version, persisted revision, and active revision are independent.

Backward-compatible additions may add optional envelope fields while preserving
all required fields and meanings. Consumers must ignore unknown optional
fields. Removing or renaming a required field, changing normalization,
returning an ID inside the record, changing an absent ID into an error, or
weakening snapshot atomicity requires a new interface major version and
coordinated consumer change.

The current Intent Invocation v1.0.0 and Execution Dispatch v4.1.0 interfaces
remain unchanged because the script adapter preserves their existing inputs,
record shape, and caller-visible absent-ID behavior.

## Verified platform basis

The Home Assistant platform assumptions were verified on 2026-10-09 against
`home-assistant/core` commit
`d5c30b135f3f565d67b8f0b70ae76ca383a5a7af`:

- `SupportsResponse.ONLY` is defined for read-only actions whose callers must
  request response data;
- response data is a JSON-serializable mapping;
- missing services raise `ServiceNotFound`;
- service schemas validate before handler execution;
- the admin-service helper enforces administrator access when used; and
- current developer guidance registers integration actions in `async_setup`
  and validates config-entry availability inside the handler.

This source identity is design evidence, not a permanent pin on Home Assistant.
ASTV-333 must reverify compatibility against its implementation baseline.
