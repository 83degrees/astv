# ASTV-60 validation evidence

Date: 2026-08-24

## Pickup gate and authoritative boundaries

- Linear issue `ASTV-60` was retrieved in full from team `astv` in `Ready`.
- Dependencies `ASTV-31` and `ASTV-53` were both confirmed `Done`.
- `CURRENT_WORK.md` was absent.
- The issue was checked against the current live script and caller,
  `contracts/MEDIACAT_ITEM_LOOKUP_INTERFACE.md`, approved-target v2 in
  `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md`, and
  `01_Architecture/ASTV_ARCHITECTURE.md`.
- No material conflict or ambiguity remained. `ASTV-60` was moved to
  `In Progress` before any live or repository mutation.

## Pre-change evidence and rollback

The live Home Assistant script configuration API returned:

- script: `script.astv_intent_engine_media`;
- storage key: `astv_intent_engine_media`;
- stable configuration hash: `b36661a38e022b4b`;
- category: `01K9QMV1C04YWV4HAS8G6V7FRV`; and
- the exact six-step legacy definition captured in
  `ASTV-60_Rollback/astv_intent_engine_media.pre-change.json`.

Rollback evidence:

- rollback payload SHA-256:
  `99AFC22812B8C4CF75249BA9E1C5251EE57EB4A899863A72E0FFA9A6D2BD1FA5`;
- restoration instructions:
  `ASTV-60_Rollback/README.md`; and
- instructions SHA-256:
  `7D4E229070FFD45C19314BECF6B4190D7545B00B50BDD60BC2E9A913C6197DD2`.

The restoration procedure uses a fresh live hash as an optimistic lock and
replaces only the target script with the captured config object and category.
No unrelated reload or Home Assistant restart is required.

## Caller and active-input baseline

Live configuration search found `script.astv_select_intent_engine` as the known
caller of `script.astv_intent_engine_media`. The caller remained at stable hash
`e9759f8b814b63df`. The search was partial because three YAML-defined
automations and three YAML-defined scripts are not exposed by the per-item
configuration endpoint. The hash-checked read-only `scripts.yaml` snapshot also
contains the same caller and no additional call site; its SHA-256 is
`F13C5BFAA7E895C1E8BDE0202365ECDD31D00D806923F9AE5D2A19D42647277C`.

All seven active media records were re-resolved through the live, side-effect-free
`script.astv_find_intent_record` function:

| Intent ID | Method key | Live `params` keys | MediaCat IDs |
| --- | --- | --- | --- |
| `classic_fm` | `ha_mplayer` | `output`, `sources` | absent |
| `lbc_news` | `ha_mplayer` | `output`, `sources` | absent |
| `gold_radio` | `ha_mplayer` | `output`, `sources` | absent |
| `bbc_radio_2` | `ha_mplayer` | `output`, `sources` | absent |
| `smooth_radio` | `g_home_device` | `output`, `sources` | absent |
| `lbc_radio` | `g_home_device` | `output`, `sources` | absent |
| `news_briefing` | `g_home_device` | `output`, `sources` | absent |

Every record retained `output.domain: audio`. The read-only snapshot copy of
`astv_intent_catalogue.yaml` matched its indexed SHA-256
`8B99B82A4D2E5C47F787A1393B844486086F726C12B4CEFC9EB48B71181ECBD2`.
The snapshot still lacks an independent capture manifest; the live lookups above
are the freshness evidence for active record shape.

Service discovery before and after installation returned only
`curated_media.resolve_item`. `curated_media.resolve_media_record` is
intentionally unregistered while schema v2 remains active.

## Reviewed configuration change

The supported Home Assistant script configuration API accepted one full-config
replacement with the pre-change hash as its optimistic lock. It loaded the
updated script without a separate broad reload or restart.

- installed stable configuration hash: `883e77ec37747186`;
- configuration validation accepted the dormant
  `curated_media.resolve_media_record` action reference and reported it as not
  present in the current service registry, which is the expected schema-v2
  state; and
- the best-practice checker noted template conditions. The conditions compare
  two normalized per-call variables for the three-way compatibility decision;
  no native entity-state condition represents that decision.

Structured pre-installation comparison proved that sequence steps 2 through 7
of the installed definition are exactly the captured six-step legacy sequence.
Focused inspection of the retrieved installed definition proved:

- `catalogue_id` and `item_id` are read directly from `request.params` and
  normalized with default, string conversion, and trimming;
- `output.domain` is read directly from `request.params.output.domain` on both
  execution paths;
- the incomplete-reference branch creates one notification and stops with
  `error: true`;
- the normalized branch contains exactly one
  `curated_media.resolve_media_record` action;
- the full action response is captured as `media_record_response`;
- `media_record_response.execution_methods` is passed unchanged as the existing
  resolver's `available_sources` input;
- the existing endpoint selector receives the resolver's selected source;
- the normalized response returns the current four fields plus
  `media_record: media_record_response`;
- the legacy response contains exactly the current four fields;
- the normalized branch contains no `request.params.sources` reference or
  fallback; and
- the both-identifiers condition selects the normalized branch before legacy
  fall-through, so both identifiers take precedence even if `sources` is also
  present; and
- no `selected_execution_method` field exists.

## Focused non-live selection proof

Representative mappings were passed only to the unchanged
`script.astv_resolve_playback_method` function. No media lookup or external
playback action was performed by these tests.

| Case | Preference | Result | Trace |
| --- | --- | --- | --- |
| Direct `url` under `ha_mplayer` | `ha_mplayer`, `g_home_device` | `ha_mplayer` | `1f51bc72e8699f87f1d348795d22aca0` |
| Radio Browser-backed `ha_media_source` under `ha_mplayer` | `ha_mplayer`, `g_home_device` | `ha_mplayer` | `8df3b763effa52fee8b8a3a8e2bec9fb` |
| Multi-method record | `ha_mplayer`, `g_home_device` | `ha_mplayer` | `4c04fcf1cbc52f2afaa1288d856c2fc4` |
| Same multi-method record, reversed order | `g_home_device`, `ha_mplayer` | `g_home_device` | `805702e4bbc35c280275b94675ec9fa5` |
| No preferred method available | `ha_mplayer` only; record has `g_home_device` | blank selected source | `412b884cc36b2eed9a36402e8201af85` |

The no-match result preserves the existing behavior. The endpoint selector and
dispatcher were not changed; the current dispatcher rejects a blank method
before executing a downstream path.

## Partial-reference failure

A direct, non-executing Media Intent Engine test supplied
`catalogue_id: " curated_media "` and a whitespace-only `item_id`.

- Media Intent Engine trace: `e55ca5890739c1f05c0024cd9330b521`.
- The trace normalized the values to `curated_media` and blank.
- Compatibility choice 0 was selected.
- Exactly one persistent notification titled `Incomplete MediaCat Reference`
  was created; notification count changed from zero to one.
- The notification identified `catalogue_id: curated_media` and
  `item_id: (blank)`.
- The run stopped with `error: true` before any lookup, area-domain lookup,
  method resolution, endpoint selection, dispatcher, or execution path.

## Legacy live regressions

All tests used `script.astv_uid_gateway` with the established Kitchen reader
`sensor.pi_nfc_99_last_uid`. The resolved target area was
`5fa17a3cccaf4af0a5daef18141375fd`; current area-domain resolution selected
`media_player.kitchen_speaker` for `ha_mplayer` and `Kitchen Speaker` for
`g_home_device`.

### Classic FM — Radio Browser through `ha_mplayer`

- UID: `7AB06354E000`.
- UID Gateway: `dd38f2f0e9ba47c4dd3b2dd139a34be7`.
- Intent Gateway: `9b202d1a1066b59c1f0850b7fb907382`.
- Select Intent Engine: `2ace172eb586aa10008fd972140b05e2`.
- Media Intent Engine: `7169e2b51f354b846449854b20cc17d1`.
- Dispatcher: `f5122d2a9ecb072ef9295c9aea7c7991`.
- HA Media Player Engine: `368d2c521ef296ab83604df418019443`.

The Media trace showed normalized identifiers both blank, neither MediaCat
branch selected, legacy steps 2–4 executed in their original order, method
`ha_mplayer`, endpoint `media_player.kitchen_speaker`, and exactly the four-field
response. Radio Browser resolved Classic FM and the HA Media Player path loaded
the station successfully.

### BBC Radio 2 — legacy AdvMedia catalogue reference through `ha_mplayer`

- UID: `DEADBEEF`.
- UID Gateway: `d2164a7c49598c039ebc8087027731ca`.
- Intent Gateway: `b395abf3aed5fd5725620517457b89a3`.
- Select Intent Engine: `43c77e98b5eda1dbc866eb3cb96af3c3`.
- Media Intent Engine: `3226ba1d50afe780f136c61329c6fc08`.
- Dispatcher: `297978b30655a5a16897722715570175`.
- HA Media Player Engine: `d097ca9db9e8bc45d9cc7a4502bc9a90`.
- ASTV AdvMedia adapter: `9e61a3219027e8b774ee7b07a0e5fc41`.

The Media trace again selected neither MediaCat branch, passed the unchanged
legacy `sources.ha_mplayer` mapping to the resolver, selected the same Kitchen
endpoint, and returned only the four legacy fields. The existing AdvMedia
catalogue-reference path completed and the Kitchen speaker reported BBC Radio 2
playing.

### Smooth Radio — `g_home_device`

- UID: `DEADSMOOTH`.
- UID Gateway: `40907c5c0c8a2f8128f894fec64807d5`.
- Intent Gateway: `2b7905acf36b96aa98d448df7e344a22`.
- Select Intent Engine: `34f9cae901d49ce4b8d60c242a89d977`.
- Media Intent Engine: `71c283e1318907cc297b0440a104cd05`.
- Dispatcher: `a89f1b4a032c6f6e90e63944a6d589ff`.
- Google Home Device Engine: `8bf9c21ffc6e546fdc64822a6cd97e96`.

The Media trace selected neither MediaCat branch, selected
`g_home_device` and endpoint phrase `Kitchen Speaker`, and returned exactly the
four legacy fields. The unchanged Google Home path constructed and sent
`Play Smooth Radio on Global Player on Kitchen Speaker`. Every recorded trace
finished successfully.

Across all three regressions, Media Intent Engine action traces contain no
MediaCat lookup step. No rollback trigger fired.

## Preserved boundaries and final checks

Final live hashes:

| Script | Stable hash |
| --- | --- |
| `script.astv_intent_engine_media` | `883e77ec37747186` |
| `script.astv_resolve_playback_method` | `2cc153d7961d0f6f` |
| `script.astv_select_area_playback_endpoint` | `898e552c10be950a` |
| `script.astv_select_intent_engine` | `e9759f8b814b63df` |
| `script.astv_select_execution_engine` | `338ddf0d9a75efc8` |
| `script.astv_ha_mplayer_engine` | `d4d5039b2ba6dc0b` |
| `script.astv_g_home_device_engine` | `32dba34e015c9156` |

The script configuration API mutation targeted only
`astv_intent_engine_media`. Configuration search found the dormant normalized
action reference only in that script. No dispatcher, execution script,
selection helper, intent data, MediaCat or AdvMedia implementation/data,
contract, central registry, or current-production diagram was changed.

Repository changes are limited to:

- `ASTV-60_VALIDATION.md`;
- `ASTV-60_Rollback/astv_intent_engine_media.pre-change.json`;
- `ASTV-60_Rollback/README.md`;
- `01_Architecture/ASTV_ARCHITECTURE.md`; and
- `CURRENT_STATE.md`.

## Limitations and cutover boundary

- The schema-v3 action is not registered or live, so this issue did not perform
  a live normalized lookup or normalized lookup-failure invocation. Contracted
  lookup failure will propagate from the first normalized action because the
  branch has no `continue_on_error`, duplicate notification, alternate lookup,
  or legacy fallback.
- The first live schema-v3 lookup-to-dispatch proof and the all-seven normalized
  record proof remain with `ASTV-65`.
- `ASTV-61` must carry the optional media-path `media_record` through Select
  Intent Engine and the dispatcher before normalized end-to-end operation.
- `ASTV-64` owns the inactive seven-record replacement bundle. No active intent
  data was changed here.
- The production filesystem snapshot lacks an independent capture manifest and
  remains secondary to the live evidence recorded above.
- Live configuration search remains partial for the YAML-defined items described
  above; this limitation existed before the change and is explicitly recorded.

The compatibility-safe script is installed, the legacy production path remains
proved, the normalized selection logic has focused non-live evidence, and the
rollback payload is operational. ASTV-60 is ready for `Review / Test`; only the
user may move it to `Done`.
