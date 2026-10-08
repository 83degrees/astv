# ASTV Intent Catalogue Schema

**Schema ID:** `astv.intent_catalogue`  
**Schema version:** `1`  
**Status:** Proposed under ASTV-330; not approved or active until G3 human acceptance  
**Owner:** ASTV  
**Authoritative location:** `03_Contracts/ASTV_INTENT_CATALOGUE_SCHEMA.md`

## Purpose and scope

This document proposes the persisted YAML schema for the ASTV Intent Catalogue.
It defines the versioned document envelope, record identifiers, the two current
intent-record shapes, validation boundaries, and the one-time migration from the
unversioned deployed catalogue.

Schema v1 covers only:

- `media.play_source`; and
- `routine.run`.

This document does not implement a loader, validator, administration interface,
activation mechanism, runtime reference probe, deployment, or production
migration. Those remain downstream work, principally ASTV-331 and ASTV-332.

## Authorities and compatibility baseline

This proposal is constrained by:

- `01_Architecture/ASTV_ARCHITECTURE.md`;
- `03_Contracts/ASTV_INTENT_INVOCATION_INTERFACE.md` v1.0.0;
- `03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` v4.1.0;
- MediaCat's provider-owned `MEDIACAT_ITEM_LOOKUP_INTERFACE.md` v2.2.0;
- `04_Implementation/haos/source/config/astv/astv_intent_catalogue.yaml`;
- `04_Implementation/haos/source/config/packages/astv/astv_scripts.yaml`;
- `PRODUCT_ADMINISTRATION_INTERFACE_STANDARD.md`; and
- `HOME_ASSISTANT_CONFIG_DEPLOYMENT_STANDARD.md`.

The current source catalogue contains eight records: seven
`media.play_source` records and `morning_routine` with
`routine: morning`. Schema v1 preserves every identifier and record value.

## Version identities are independent

| Identity | Meaning | Initial/current value |
| --- | --- | --- |
| `schema_version` | Persisted ASTV Intent Catalogue vocabulary and shape | `1` |
| Intent Invocation `interface_version` | External caller-to-ASTV invocation contract | `1.0.0` |
| Execution Dispatch interface version | Internal ASTV dispatch contract | `4.1.0` |
| Future administration `interface_version` | External ASTV catalogue administration contract | Defined by ASTV-332 |
| Persisted/active revision | Opaque identity of one provider state | Defined by ASTV-331/332 |

A schema version is not an interface version or a revision. Moving the persisted
catalogue to schema v1 does not by itself change either existing ASTV interface.

## Complete document envelope

A schema-v1 catalogue is exactly one YAML document whose root is a mapping with
these keys:

```yaml
schema: astv.intent_catalogue
schema_version: 1
records:
  <intent_id>:
    <record>
```

| Field | Presence | Type | Rule |
| --- | --- | --- | --- |
| `schema` | Required | string | Exactly `astv.intent_catalogue` |
| `schema_version` | Required | integer | Exactly `1`; the string `"1"` is invalid |
| `records` | Required | mapping | One or more uniquely identified records |

No other root key is permitted. YAML directives, custom tags, merge keys and
aliases are not part of schema v1. A loader must reject duplicate raw YAML
mapping keys rather than accept parser-specific last-key-wins behavior.

## Intent identifiers and lookup normalization

Each key in `records` is the authoritative ASTV `intent_id`. The identifier
is not duplicated inside its record.

A persisted identifier must:

- be a YAML string;
- already be in canonical lower-case form;
- match `^[a-z0-9][a-z0-9_]*$`;
- contain no leading or trailing whitespace; and
- be unique after ASTV lookup normalization.

Lookup normalization remains the v1.0.0 invocation behavior:

```text
normalized_lookup_id = string(input).trim().lower()
```

Validation applies that same normalization to every raw record key and rejects
the complete document if two keys normalize to the same value. It then rejects
any key that is not already canonical. The validator must not silently rename,
merge, or discard a record.

There is no maximum identifier length in schema v1. Adding one later would need
compatibility assessment.

## Common record fields

Every record is a mapping with these common fields:

| Field | Presence | Type | Rule |
| --- | --- | --- | --- |
| `intent` | Required | string | Exactly one supported intent discriminator |
| `title` | Required | string | Non-empty after trimming; preserved verbatim |
| `area_override` | Optional | string | Non-empty after trimming and matches `^[a-z0-9][a-z0-9_]*$` |
| `params` | Required | mapping | Shape selected by `intent` |

If `area_override` is omitted, the record contributes no area override. It has
no materialized default. If present, it must not be blank or `null`.

Runtime precedence remains unchanged:

1. non-blank invocation `input_area_override`;
2. the record's `area_override`;
3. `area_id(trigger_entity)`;
4. unresolved.

The schema does not validate that an area currently exists. Runtime area
resolution remains ASTV behavior.

## `media.play_source` record

The exact shape is:

```yaml
intent: media.play_source
title: <non-blank string>
area_override: <optional canonical Home Assistant area ID>
params:
  output:
    domain: <canonical ASTV playback-domain ID>
  catalogue_id: <MediaCat catalogue ID>
  item_id: <MediaCat item ID>
```

| Path | Presence | Type | Rule |
| --- | --- | --- | --- |
| `intent` | Required | string | Exactly `media.play_source` |
| `title` | Required | string | Common-field rule |
| `area_override` | Optional | string | Common-field rule |
| `params` | Required | mapping | Only `output`, `catalogue_id`, `item_id` |
| `params.output` | Required | mapping | Only `domain` |
| `params.output.domain` | Required | string | Matches `^[a-z0-9][a-z0-9_]*$` |
| `params.catalogue_id` | Required | string | Matches MediaCat's `^[a-z0-9][a-z0-9_-]*$` |
| `params.item_id` | Required | string | Matches MediaCat's `^[a-z0-9][a-z0-9_-]*$` |

The three parameter values must be non-empty after trimming and already
canonical; validation does not trim or rewrite persisted values. Schema v1 does
not default `output.domain`, `catalogue_id`, or `item_id`.

The schema validates the reference structure and identifier syntax only. It does
not prove that the MediaCat catalogue or item exists.

## `routine.run` record

The exact shape is:

```yaml
intent: routine.run
routine: <canonical routine ID>
title: <non-blank string>
area_override: <optional canonical Home Assistant area ID>
params: {}
```

| Path | Presence | Type | Rule |
| --- | --- | --- | --- |
| `intent` | Required | string | Exactly `routine.run` |
| `routine` | Required | string | Matches `^[a-z0-9][a-z0-9_]*$` |
| `title` | Required | string | Common-field rule |
| `area_override` | Optional | string | Common-field rule |
| `params` | Required | mapping | Must be the empty mapping `{}` |

The `morning_routine` record remains keyed by `morning_routine` and retains
`routine: morning`. The routine ID selects the existing
`routine_<routine>` label lookup and is not inferred from the record key.

## Requiredness, defaults, nulls and unknown keys

Schema v1 is fail-closed.

- Every required field must be explicitly present.
- Omission of optional `area_override` is the only defaulted condition and
  means "no record override".
- A required value that is blank, whitespace-only or `null` is invalid.
- An optional value, when present, must satisfy its full type and value rule;
  blank and `null` are invalid.
- String fields do not accept booleans, numbers, sequences or mappings.
- `schema_version` does not accept a numeric string.
- Unknown keys are rejected at the envelope, record, `params`, and `output`
  levels.
- An unknown `intent` discriminator is rejected; there is no generic record
  fallback.
- Exact duplicate YAML keys and duplicate normalized intent IDs reject the
  entire document.
- Validation is atomic: one invalid record makes the complete candidate invalid.

## Ordering and serialization

Mapping order has no semantic meaning. A conforming consumer must not select or
prioritize records by file order.

For human review, canonical serialization should place `schema`,
`schema_version`, then `records`; retain a stable record order; and use the
field order shown above. Reordering alone does not change catalogue meaning or
revision equality unless a future provider contract explicitly defines
byte-based revisions.

## Version selection and rejection

ASTV supports only the current schema version. For this document that is
`schema_version: 1`.

A loader must inspect the envelope before exposing records. A missing, malformed
or unsupported version rejects the complete candidate. It must not:

- guess the version from record shape;
- treat the legacy unversioned mapping as v1;
- migrate in memory;
- partially load recognized records;
- fall back to a previous schema parser; or
- reinterpret a future version as v1.

Migration is an explicit governed operation, not loader behavior.

## Persisted document versus runtime lookup record

The persisted document contains the envelope and keyed `records` mapping. The
runtime lookup boundary returns only the selected record mapping, unchanged.

For example, a lookup for `classic_fm` returns:

```yaml
intent: media.play_source
title: Play Classic FM
params:
  output:
    domain: audio
  catalogue_id: curated_media
  item_id: classic_fm
```

It does not return `schema`, `schema_version`, `records`, or a synthesized
`intent_id`. Unknown IDs still return `{}`. This is the compatibility bridge
ASTV-331 must implement so the existing gateway, intent engines, and execution
dispatch continue to receive the current record shape.

## Cross-product reference boundaries

| Condition | Classification | Owner and required meaning |
| --- | --- | --- |
| Missing, blank, wrong-type or malformed `catalogue_id`/`item_id` | Structurally invalid ASTV record | ASTV rejects the candidate before activation |
| Well-formed reference whose catalogue or item does not exist | Structurally valid, unresolved target | MediaCat owns lookup and explicit not-found behavior; schema validity is not proof of existence |
| MediaCat unavailable | Dependency unavailable | Runtime/admin operation reports dependency unavailability where applicable; stored reference is preserved |
| MediaCat returns a record | Referenced target resolved | MediaCat owns item existence, membership, metadata and execution methods |
| AdvNFC tag maps to an ASTV intent ID | External inbound reference | AdvNFC owns the mapping, its validation, and reverse relationship queries |

ASTV must not copy MediaCat item state or AdvNFC reverse-reference state into
this catalogue. Whether validation or activation probes live references, and
the exact error mapping and retained-active-state behavior, belong to ASTV-332.
This schema does not pre-implement that policy.

## Migration from the deployed unversioned catalogue

### Source baseline

The migration source is the exact eight-record mapping at
`04_Implementation/haos/source/config/astv/astv_intent_catalogue.yaml`.
The source has no envelope. Each top-level key becomes an entry under
`records`; each record mapping is copied byte-for-value without changing its
meaning.

```yaml
# before
classic_fm:
  intent: media.play_source
  ...

# proposed v1
schema: astv.intent_catalogue
schema_version: 1
records:
  classic_fm:
    intent: media.play_source
    ...
```

The complete expected candidate is
`05_Tests/fixtures/astv_intent_catalogue/v1/valid/current_baseline_migrated.yaml`.

### Preservation requirements

Migration must preserve:

- all eight record keys;
- all seven `catalogue_id: curated_media` references;
- each existing `item_id`;
- every `output.domain: audio`;
- every title;
- `morning_routine` with `routine: morning` and `params: {}`;
- lookup normalization of trim plus lower-case;
- unknown lookup returning `{}`;
- unchanged record-only runtime return;
- area precedence; and
- Intent Invocation v1.0.0 and Execution Dispatch v4.1.0 behavior.

### Governed adoption sequence

ASTV-330 stops at accepted documentation and fixtures. A later authorized
implementation/adoption sequence must:

1. identify the exact accepted source candidate and target path;
2. capture the immediate prior deployed file bytes and recovery location;
3. generate or review the complete v1 candidate without editing record meaning;
4. validate YAML parsing with duplicate-key detection;
5. validate the complete candidate against schema v1;
6. compare the eight migrated runtime records with the legacy records for
   semantic equality;
7. validate every current ID and representative unknown-ID lookup through the
   proposed adapter;
8. keep the previous valid active catalogue unchanged if any check fails;
9. switch only after applicable human acceptance and explicit deployment or
   activation authority;
10. run the Home Assistant-supported configuration check and the governed
    runtime validation required by the implementation issue; and
11. record candidate, target, prior-state, validation and outcome evidence.

There is no implicit migration and no mixed legacy/v1 operating mode.

### Failure and recovery

Before any target replacement, preserve the exact immediate prior unversioned
file separately from the target path. If transfer, parsing, validation,
activation, Home Assistant configuration validation, or runtime checks fail:

1. stop further progression;
2. retain the failure evidence;
3. restore the captured prior bytes to the same deterministic target path;
4. repeat the Home Assistant-supported configuration check;
5. perform any authorized reload/restart required for the restored state; and
6. record the restored identity and final target status.

The legacy fixture
`invalid/rollback_legacy_unversioned.yaml` demonstrates recovery input. It is
intentionally invalid as schema v1 and must never be accepted by a v1-only
loader. Recovery of a pre-v1 runtime therefore uses the pre-v1 implementation
and its exact prior data together; it is not a schema-v1 fallback mode.

## Fixture catalogue

The fixture manifest at
`05_Tests/fixtures/astv_intent_catalogue/v1/README.md` defines the expected
outcome for every positive and negative fixture. Fixtures are evidence for this
proposal, not executable validation code.

## Architecture and DDR assessment

No architecture update is proposed. The approved architecture already assigns
intent-catalogue lookup and record interpretation to ASTV, records the exact
record-only lookup boundary, and separates MediaCat and AdvNFC ownership. The
v1 envelope changes future persistence, not components, responsibilities,
routing, area precedence, dispatch, or external interface behavior.

No DDR is proposed. This schema contract is the durable authority for the data
shape and compatibility rule; the migration plan records adoption mechanics.
There is no separate significant architectural decision whose rationale would
otherwise be lost. If review changes an architectural responsibility or flow,
that new decision must be classified and assessed separately before acceptance.

## Decisions requiring G3 human agreement

Human acceptance is required for the proposed:

1. `schema`/`schema_version`/`records` envelope;
2. keyed-record identity model and canonical identifier rules;
3. strict unknown-key, null, duplicate and atomic-rejection policy;
4. exact `media.play_source` and `routine.run` shapes;
5. record-only runtime compatibility boundary;
6. current-schema-only support and no implicit migration;
7. cross-product structural/reference boundary and ASTV-332 deferral; and
8. conclusion that no architecture or DDR change is required.

Until that acceptance, schema v1 remains proposed and must not be described as
approved or active.
