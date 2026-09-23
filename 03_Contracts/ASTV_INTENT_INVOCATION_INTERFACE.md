# ASTV Intent Invocation Interface

**Contract version:** 1.0.0  
**Status:** Current  
**Provider:** ASTV  
**Authoritative location:** `03_Contracts/ASTV_INTENT_INVOCATION_INTERFACE.md`

## Purpose

This contract defines the supported boundary for a caller to submit a canonical intent invocation to ASTV through `script.astv_intent_gateway`.

The interface separates caller-owned interaction and acquisition concerns from ASTV-owned intent interpretation, target-area resolution, routing, preparation, and execution.

The initial external consumer is AdvNFC. Other governed callers may consume the same provider-owned interface in future without making their acquisition mechanism part of ASTV.

## Provider entry point

Home Assistant action:

`script.astv_intent_gateway`

ASTV owns the entry point and all behavior after the request crosses this boundary. The caller owns construction of the invocation request and any upstream acquisition, mapping, filtering, or normalization needed to produce it.

## Request

| Field | Presence | Type | Meaning |
| --- | --- | --- | --- |
| `intent_id` | Required | string | Intent identifier presented to ASTV for intent-catalogue lookup. |
| `input_area_override` | Optional | string | Explicit caller-supplied target-area override. Blank or omitted means no caller override. |
| `trigger_entity` | Optional | Home Assistant entity ID | Originating entity used by ASTV as the final area-resolution fallback when no caller or intent-record override resolves the area. Blank or omitted means no originating-entity fallback is available. |

No UID, NFC tag record, MQTT topic, reader identity schema, or other acquisition-specific payload forms part of this contract.

## Intent lookup semantics

ASTV passes `intent_id` to `script.astv_find_intent_record`.

The current provider implementation normalizes the lookup key by converting the supplied value to string, trimming surrounding whitespace, and converting it to lower case before reading the ASTV intent catalogue.

If no intent record is found, ASTV emits the current visible `No Intent Record Found` notification and stops the invocation without raising an execution error.

The caller must not depend on ASTV returning the resolved intent record.

## Area-resolution semantics

After a valid intent record is found, ASTV resolves the target area in this precedence order:

1. non-blank `input_area_override`;
2. non-blank `area_override` from the resolved ASTV intent record;
3. the Home Assistant area of `trigger_entity`, where a usable originating entity is supplied.

If no target area is resolved, ASTV emits the current visible `No Target Area Resolved` notification and stops the invocation without raising an execution error.

The caller must not independently reproduce or override this precedence as part of this contract.

## Successful invocation behavior

When intent lookup and area resolution succeed, ASTV invokes its intent-routing boundary with:

- the resolved ASTV intent record; and
- the resolved target area.

Routing, MediaCat lookup, playback-method selection, endpoint selection, execution-engine dispatch, provider handling, and terminal actions remain ASTV-owned or governed by ASTV's downstream consumed interfaces.

This interface returns no contracted response payload to the caller.

## Ownership boundary

### Caller owns

- acquisition of the originating interaction or event;
- caller-specific validity filtering;
- caller-specific identifier normalization;
- mapping from caller-specific identifiers to `intent_id`;
- construction of optional `input_area_override`;
- supply of optional `trigger_entity`;
- behavior before invoking `script.astv_intent_gateway`.

For AdvNFC specifically, NFC UID values, reader-state semantics, tag records, and tag mapping remain AdvNFC concerns and do not cross this interface.

### ASTV owns

- intent-catalogue lookup;
- intent-record interpretation;
- area-resolution precedence and result;
- intent routing;
- execution preparation and selection;
- ASTV-owned execution paths;
- the observable failure behavior documented above.

## Compatibility requirements

A compatible caller:

- supplies a non-empty usable `intent_id` when it expects ASTV to resolve an intent;
- treats `input_area_override` and `trigger_entity` as optional;
- does not depend on NFC- or caller-specific data being available inside ASTV;
- does not depend on a response payload from the invocation;
- does not assume automatic fallback to another intent, area, route, method, or execution path after an ASTV failure.

A compatible provider change must preserve these semantics or revise this contract through governed contract change before incompatible runtime behavior is introduced.

## Initial compatibility baseline

This v1.0.0 contract formalizes the existing ASTV Phase 0 UID Gateway → Intent Gateway hand-off without changing runtime behavior.

At the preparation baseline for ASTV-241, the current ASTV UID Gateway invokes `script.astv_intent_gateway` with:

- `intent_id`;
- `input_area_override`; and
- `trigger_entity`.

AdvNFC extraction is expected to consume the same interface. Runtime ownership does not move merely because this contract exists; the separate governed carve-out and cutover work controls that transition.
