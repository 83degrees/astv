# ASTV-64 Validation

## Result

ASTV-64 prepared and tested the complete inactive eight-record ASTV intent
catalogue for the coordinated MediaCat v3 cutover. Seven media records now use
only retained ASTV fields plus method-neutral `catalogue_id` / `item_id`
references. `morning_routine` is unchanged. A byte-for-byte legacy rollback
copy and restoration procedure are included.

No production file, Home Assistant script, runtime configuration, endpoint or
tag data, MediaCat or AdvMedia workspace, shared contract, service registry, or
external system was changed. No Home Assistant action, reload, restart,
playback, assistant command, or routine action was invoked.

## Pickup and authority

- Linear issue `ASTV-64` was retrieved in full from team `astv` in `Ready`.
- Dependencies `ASTV-35`, `ASTV-56`, `ASTV-59`, `ASTV-60`, `ASTV-61`,
  `ASTV-62`, and `ASTV-63` were all `Done`.
- The parent `CURRENT_WORK.md` was only its inactive template and did not
  conflict with Linear.
- The issue was checked against current production evidence, all three
  applicable contracts, `01_Architecture/ASTV_ARCHITECTURE.md`,
  `CURRENT_STATE.md`, the ASTV-56 catalogue and migration matrix, and generated
  governance.
- No contract, ownership, routing, scope, or acceptance-criteria conflict was
  found. The issue was moved to `In Progress` before repository changes.

## Source capture and freshness evidence

The complete preparation source was read from the governed read-only production
evidence mount before any ASTV repository edit.

| Evidence | Path | Size | SHA-256 |
| --- | --- | ---: | --- |
| Legacy eight-record source | `Production_ReadOnly/starburst/assistive/astv_intent_catalogue.yaml` | 2,309 bytes | `8b99b82a4d2e5c47f787a1393b844486086f726c12b4cefc9eb48b71181ecbd2` |
| ASTV-56 schema-v3 catalogue | `MediaCat/curated_media/catalogue.yaml` | 11,243 bytes | `067b2948bba11cbd418f90dc94f39b80f7f530091c3f388bc3e4313de03510c7` |
| Existing area endpoints | `Production_ReadOnly/starburst/assistive/astv_area_endpoints2.yaml` | 982 bytes | `34e3b8db445a522487d496fb89c51a5f88a38f485e0cada04c47c79218db369d` |

The source hash matches the ASTV evidence index and ASTV-56 source capture. It
contains exactly the expected ordered baseline: seven media records followed by
`morning_routine`. Same-day live evidence in `ASTV-60_VALIDATION.md` and
`ASTV-63_VALIDATION.md` re-resolved all seven active media records and confirmed
that each still had `output` plus legacy `sources`, with no MediaCat identifiers.
`ASTV-61_VALIDATION.md` also exercised the unchanged Morning Routine through its
normal entry path.

Fresh read-only configuration reads during ASTV-64 confirmed the installed
compatibility hashes:

| Script | Stable hash |
| --- | --- |
| `script.astv_intent_engine_media` | `883e77ec37747186` |
| `script.astv_select_intent_engine` | `bda1d825cd330779` |
| `script.astv_select_execution_engine` | `9d2eedaeba1f5b86` |
| `script.astv_ha_mplayer_engine` | `7f2e5588e9a9cedb` |
| `script.astv_adapter_advmedia` | `fe00d0cea795cc06` |
| `script.astv_g_home_device_engine` | `a51304a3b2c88287` |
| `script.astv_provider_g_assist` | `052ce3c242fe4e93` |

Live service discovery still returned only `curated_media.resolve_item` and no
`advmedia_process_media_record`. The replacement therefore remains inactive and
ASTV-65 activation conditions are not yet met.

The read-only filesystem snapshot still has no capture manifest. Its source,
capture procedure, completeness, exclusions, and capture timestamp are not
independently established. The Home Assistant configuration API cannot return
the YAML-defined `script.astv_find_intent_record` or its expanded `!include`, so
ASTV-64 did not obtain a second byte stream from live Home Assistant. The static
complete source is supplemented by the same-day live record-shape and installed
hash evidence above; no service invocation was used to bypass this limitation.

## Prepared and rollback artifacts

| Artifact | Path | SHA-256 |
| --- | --- | --- |
| Inactive replacement | `assistive/astv_intent_catalogue.yaml` | `a9c3bb87a933847d25e1f06f73b3780ae4e1338d10e5441742c51ff7075ed703` |
| Legacy rollback copy | `ASTV-64_Rollback/starburst/assistive/astv_intent_catalogue.yaml` | `8b99b82a4d2e5c47f787a1393b844486086f726c12b4cefc9eb48b71181ecbd2` |

The rollback copy is byte-for-byte equal to the read-only source. Recovery does
not depend on Git history. `ASTV-64_Rollback/README.md` names the exact production
target, configuration validation, script-only reload, coordinated rollback, and
post-restore checks. No rollback step was run against production.

## Seven-record before/after matrix

Every row retains its key, request-facing `title`, `intent:
media.play_source`, and `params.output.domain: audio`. No title was derived from
MediaCat.

| Record | Retained title | Before `params` | Prepared `params` | Removed legacy method/provider |
| --- | --- | --- | --- | --- |
| `classic_fm` | `Play Classic FM` | `output`, `sources` | `output`, `catalogue_id: curated_media`, `item_id: classic_fm` | `ha_mplayer` / `radio_browser` |
| `lbc_news` | `Play LBC News` | `output`, `sources` | `output`, `catalogue_id: curated_media`, `item_id: lbc_news` | `ha_mplayer` / `radio_browser` |
| `gold_radio` | `Play Gold Radio` | `output`, `sources` | `output`, `catalogue_id: curated_media`, `item_id: gold_radio` | `ha_mplayer` / `radio_browser` |
| `bbc_radio_2` | `Play BBC Radio 2` | `output`, `sources` | `output`, `catalogue_id: curated_media`, `item_id: bbc_radio_2` | `ha_mplayer` / `advmedia` |
| `smooth_radio` | `Smooth Radio` | `output`, `sources` | `output`, `catalogue_id: curated_media`, `item_id: smooth_radio` | `g_home_device` / `g_assist` |
| `lbc_radio` | `LBC` | `output`, `sources` | `output`, `catalogue_id: curated_media`, `item_id: lbc_radio` | `g_home_device` / `g_assist` |
| `news_briefing` | `News Briefing` | `output`, `sources` | `output`, `catalogue_id: curated_media`, `item_id: news_briefing` | `g_home_device` / `g_assist` |

The prepared file contains no `params.sources`, compatibility alias, media
wrapper, translation table, dormant copy, or commented legacy payload in any
media record.

## Isolated eight-record proof

The proof used the actual ASTV-56 schema-v3 loader and `CatalogueResolver`. It
loaded the prepared catalogue, rollback catalogue, ASTV-56 catalogue, and area
endpoints without writing to those workspaces. A pure local composition harness
modelled the contracted installed ASTV selection and dispatch boundaries and
recorded every downstream side effect instead of calling it.

Area `5fa17a3cccaf4af0a5daef18141375fd` was used because its `audio` preference is
`ha_mplayer`, then `g_home_device`, and it has a valid endpoint for both.

| Record | Resolved method | Selected endpoint | Consumer result |
| --- | --- | --- | --- |
| `classic_fm` | `ha_mplayer` | `media_player.kitchen_speaker` | Complete record reached ASTV AdvMedia handoff; core/playback intercepted |
| `lbc_news` | `ha_mplayer` | `media_player.kitchen_speaker` | Complete record reached ASTV AdvMedia handoff; core/playback intercepted |
| `gold_radio` | `ha_mplayer` | `media_player.kitchen_speaker` | Complete record reached ASTV AdvMedia handoff; core/playback intercepted |
| `bbc_radio_2` | `ha_mplayer` | `media_player.kitchen_speaker` | Complete record reached ASTV AdvMedia handoff; core/playback intercepted |
| `smooth_radio` | `g_home_device` | `Kitchen Speaker` | `Play Smooth Radio on Global Player on Kitchen Speaker`; SDK intercepted |
| `lbc_radio` | `g_home_device` | `Kitchen Speaker` | `play LBC Radio on Global Player on Kitchen Speaker`; SDK intercepted |
| `news_briefing` | `g_home_device` | `Kitchen Speaker` | `Play my news briefing on Kitchen Speaker`; SDK intercepted |

For every media record, the harness proved:

- reference fields are present and `params.sources` is absent;
- the target item exists once and occurs once in ordered radio membership;
- the actual ASTV-56 resolver was called exactly once;
- the returned record exposes only the expected available method;
- ASTV preference selects that method and a compatible area endpoint;
- the complete normalized record compares equal before and after dispatch;
- endpoint identity is absent from the prepared intent and MediaCat record; and
- no alternate lookup, method, endpoint, or legacy fallback is selected.

Interception totals: four AdvMedia-core handoffs, four
`media_player.play_media` actions, three
`google_assistant_sdk.send_text_command` actions, and one routine
`input_boolean.turn_on` action. Executed external actions: zero.

`morning_routine` is parsed-equal before and after, and its isolatable source
block is byte-equal through end of file. The harness routed it as
`g_automation` through the Routine intent and dispatcher path, then intercepted
the terminal `input_boolean.turn_on` action.

## Isolated rollback rehearsal

The rehearsal used in-memory mappings only:

1. loaded the prepared eight-record catalogue;
2. confirmed all seven normalized references and no legacy `sources`;
3. replaced the in-memory active mapping with the rollback catalogue;
4. confirmed all seven original `params.sources` mappings were restored; and
5. confirmed `morning_routine` remained equal.

Result: seven prepared records, seven restored original source mappings, and one
unchanged routine. No active file was replaced or reloaded.

## ASTV-65 handoff and activation conditions

ASTV-65 must not activate this complete eight-record artifact until:

- the ASTV-56 schema-v3 catalogue is ready for activation;
- schema-v3 MediaCat normalized lookup and Home Assistant Media Source handling
  are ready;
- the normalized AdvMedia core and required legacy compatibility path are
  deployed;
- ASTV-60 through ASTV-63 still match their accepted installed baseline; and
- complete MediaCat, ASTV, and AdvMedia rollback packages are available.

Current read-only discovery shows schema-v3 normalized lookup and the AdvMedia
core are not deployed, so this is a handoff artifact, not cutover authorization.
ASTV-65 owns the paused media-request window, atomic deployment, activation,
immediate all-seven live proof, and coordinated rollback on any failure.

## Changed files

Changes are limited to the approved ASTV-64 scope:

- `assistive/astv_intent_catalogue.yaml`;
- `ASTV-64_VALIDATION.md`;
- `ASTV-64_Rollback/README.md`;
- `ASTV-64_Rollback/starburst/assistive/astv_intent_catalogue.yaml`;
- `CURRENT_STATE.md`; and
- `01_Architecture/ASTV_ARCHITECTURE.md`.

No Git repository is present at the ASTV root, and Git history is not required
for recovery. Only the user may move ASTV-64 to `Done`.
