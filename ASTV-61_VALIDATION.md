# ASTV-61 Validation

Date: 2026-08-24

## Pickup and authority

- Linear issue: `ASTV-61`, "Implement ASTV execution-dispatch media context changes".
- Team: `astv`.
- Retrieved full issue status: `Ready`.
- Dependencies re-read from Linear: `ASTV-53` and `ASTV-60` were `Done`.
- This separate implementation task checked current live configuration, the
  approved-target dispatcher contract, ASTV architecture, current state, and
  generated governance, then moved ASTV-61 to `In Progress` before any
  implementation mutation.
- Exact authorized live scope was Select Intent Engine, Select Execution Engine,
  and input declarations only on the HA Media Player and Google Home Device
  engines.
- No Git repository was present or required by the issue.

## Evidence provenance and limitations

Fresh live Home Assistant configuration reads and traces are the primary
evidence. The copied production snapshot was used read-only and remains
secondary because it has no capture manifest; its source, capture procedure,
completeness, exclusions, and freshness are not independently established.

| Read-only snapshot | SHA-256 |
| --- | --- |
| `Production_ReadOnly/starburst/scripts.yaml` | `F13C5BFAA7E895C1E8BDE0202365ECDD31D00D806923F9AE5D2A19D42647277C` |
| `Production_ReadOnly/starburst/assistive/astv_intent_catalogue.yaml` | `8B99B82A4D2E5C47F787A1393B844486086F726C12B4CEFC9EB48B71181ECBD2` |

Live configuration-body search before and after installation found
`script.astv_select_intent_engine` as the only caller of
`script.astv_select_execution_engine`. The search remained partial: three
YAML-defined automations and three YAML-defined scripts were unavailable through
the per-item configuration endpoint. The matching read-only `scripts.yaml`
snapshot contains the known caller and no additional call site. This limitation
is retained rather than treating the live search as exhaustive.

## Pre-change live boundary

All four scoped scripts were read twice before mutation, had stable hashes, and
were in category `01K9QMV1C04YWV4HAS8G6V7FRV`.

| Script | Pre-change hash | Pre-change inputs |
| --- | --- | --- |
| `script.astv_select_intent_engine` | `e9759f8b814b63df` | `request`, `target_area` |
| `script.astv_select_execution_engine` | `338ddf0d9a75efc8` | required `execution_method`, `request`, `target_area`, `selected_endpoint` |
| `script.astv_ha_mplayer_engine` | `d4d5039b2ba6dc0b` | `request`, `selected_endpoint` |
| `script.astv_g_home_device_engine` | `32dba34e015c9156` | `request`, `selected_endpoint` |

The out-of-scope starting boundary was also re-read:

| Script | Hash | Result |
| --- | --- | --- |
| `script.astv_intent_engine_media` | `883e77ec37747186` | Matched the ASTV-60 installed hash; active legacy response has four fields and dormant normalized response adds complete `media_record`. |
| `script.astv_intent_engine_routine` | `26a9cd9cc3f31ce0` | Current four-field Routine response. |
| `script.astv_g_automation_engine` | `6aa39b6b39d12378` | Current unchanged Routine consumer. |

Service discovery returned only `curated_media.resolve_item`;
`curated_media.resolve_media_record` remains absent under schema v2. Live
side-effect-free Find Intent Record trace
`595e39618bb3801ddf7bde99e70e71ea` loaded the current complete intent
catalogue. Its seven media records were:

| Intent | Method | `params` keys | MediaCat identifiers |
| --- | --- | --- | --- |
| `classic_fm` | `ha_mplayer` | `output`, `sources` | absent |
| `lbc_news` | `ha_mplayer` | `output`, `sources` | absent |
| `gold_radio` | `ha_mplayer` | `output`, `sources` | absent |
| `bbc_radio_2` | `ha_mplayer` | `output`, `sources` | absent |
| `smooth_radio` | `g_home_device` | `output`, `sources` | absent |
| `lbc_radio` | `g_home_device` | `output`, `sources` | absent |
| `news_briefing` | `g_home_device` | `output`, `sources` | absent |

Every media record retained `output.domain: audio`. The normalized path was
dormant before mutation and remains dormant after installation.

## Coordinated rollback package

`ASTV-61_Rollback` existed before the first live mutation and contains the
exact four pre-change definitions plus one coordinated restoration procedure.

| File | SHA-256 |
| --- | --- |
| `astv_select_intent_engine.pre-change.json` | `E4A62126EF09CB881871B0ADAF3B4EAE38F9EDA99833DBDD40DEBF6881CB0284` |
| `astv_select_execution_engine.pre-change.json` | `B17D84DB46B1B277D3CC467EE4F73B75085D2CE145B2988D453A7D4CC982C51E` |
| `astv_ha_mplayer_engine.pre-change.json` | `C99C1CCE980155F5AFCE8067E1A0D35013B72E0F709BDBAFC197EB6D93E64CF3` |
| `astv_g_home_device_engine.pre-change.json` | `322BA9687D01A9669DE33F521DF454ED0023DF83C7C925224D087983C7A5B5F3` |
| `README.md` | `EEA3BC104ED5229D13C73AB5AE2C89471249887EAC905A546D2533D00C7D851C` |

Rollback removes the new caller handoff first, then restores the dispatcher and
both receiving engines from fresh optimistic-lock hashes. All four definitions
must be restored together.

## Reviewed change and static checks

The Home Assistant best-practices guide and its safe-refactoring,
action-pattern, and template references were read before mutation. The reviewed
definitions proved before installation:

- both media-engine `sequence` arrays were structurally identical to their
  captured pre-change definitions;
- only optional, no-default `execution_method` and `media_record` fields were
  added to each media engine;
- the dispatcher retained its four required fields unchanged and added one
  optional, no-default object field named `media_record`;
- the dispatcher Routine branch, failure default, endpoint checks, and method
  checks were structurally unchanged;
- normalized media child calls contain exactly `request`,
  `selected_endpoint`, `execution_method`, and `media_record`;
- legacy media child calls contain exactly `request` and `selected_endpoint`;
- Select Intent Engine's intent choice was structurally unchanged and its
  installed definition contains exactly one dispatcher call after that choice;
- no `selected_execution_method`, MediaCat action, record filtering, record
  mutation, retry, fallback, or new content validation was introduced.

The conditional dispatcher mapping template was evaluated with three responses:

| Response | Template request ID | Result |
| --- | --- | --- |
| Normalized media | `141415` | Four current fields plus complete unchanged fixture `media_record`. |
| Legacy media | `140887` | Exactly four current fields; no `media_record`. |
| Routine | `140342` | Exactly four current fields; no `media_record`. |

The fixture included both nested execution methods and an unknown additive field;
all were retained. The configuration API emitted one advisory for the
pre-existing templated media-player target in the unchanged HA sequence, and a
generic template-condition advisory for optional-variable presence checks. The
first is unchanged and outside scope; Home Assistant has no native entity-state
condition for the second. The templates were evaluated before installation.

## Controlled installation

The definitions were installed with fresh optimistic-lock hashes in the required
order. Each narrow script update waited until the definition was queryable and
was immediately re-read. No restart or broad reload occurred.

| Order | Script | Before | Installed |
| ---: | --- | --- | --- |
| 1 | `script.astv_ha_mplayer_engine` | `d4d5039b2ba6dc0b` | `62a363022c26ca89` |
| 2 | `script.astv_g_home_device_engine` | `32dba34e015c9156` | `d9edfefe78b6f590` |
| 3 | `script.astv_select_execution_engine` | `338ddf0d9a75efc8` | `9d2eedaeba1f5b86` |
| 4 | `script.astv_select_intent_engine` | `e9759f8b814b63df` | `bda1d825cd330779` |

No installation step failed, so the atomic rollback trigger did not fire.

## Normal-entry compatibility regressions

All four tests entered through `script.astv_uid_gateway` with
`sensor.pi_nfc_99_last_uid` and resolved Kitchen area
`5fa17a3cccaf4af0a5daef18141375fd`.

| Path | UID | Select Intent | Dispatcher | Child | Result |
| --- | --- | --- | --- | --- | --- |
| Classic FM / Radio Browser / `ha_mplayer` | `7AB06354E000` | `17c9fcf7b75ff9f3b3660f4e0e0be73f` | `0b9a3e9a0d8348875399e0b203927149` | HA `90af0a5c9906fca14fcf07cd44c5670c` | Finished; Classic FM loaded on `media_player.kitchen_speaker`. |
| BBC Radio 2 / legacy AdvMedia / `ha_mplayer` | `DEADBEEF` | `63a5131eb7afd70b3476794c730de1d4` | `a58741c1bfb80a234406948c6c213455` | HA `5d0e6bbc16b60b89e49b6c23d5fa6781` | Finished; existing catalogue-reference path loaded BBC Radio 2. |
| Smooth Radio / `g_home_device` | `DEADSMOOTH` | `dd1b657dba3541d7cab881e82faa72e6` | `d969903f27553da60f9f90b6b93c0acd` | Google Home `eb6b3e7c0907b545226dd133c23feff7` | Finished; sent `Play Smooth Radio on Global Player on Kitchen Speaker`. |
| Morning Routine / `g_automation` | `DEADMORNING` | `a536440a676cc30450fe722a59cf8646` | `8811a13c628936f4374f5067ad972615` | Google Automation `9382e66fb4591dc0d834ef707f7297db` | Finished; activated `input_boolean.gh_trigger_101`. |

Each legacy media Select Intent trace built exactly the four-field dispatcher
mapping. Each dispatcher trace selected the record-absent `else` path and called
its media engine with only `request` and `selected_endpoint`. The child root
variables contained no `execution_method` or `media_record`. The Routine call
retained only `request` and `target_area`; no media context reached Google
Automation.

## Normalized context transport proof

A direct dispatcher fixture contained required top-level context, both nested
execution methods, and
`unknown_additive_field: {nested: [preserve, 1], flag: true}`.

| Branch | Dispatcher trace | Child trace | Result |
| --- | --- | --- | --- |
| `ha_mplayer` | `80974b5571b30f236d9e231d09d15e52` | `a84d48ab85f0859363fb7d521f9002f6` | Finished through unchanged three-step HA sequence. |
| `g_home_device` | `6d5d1b6374e2ced601f9bdac0bc7b79b` | `04e74a28fe2278f96d5c3553da46b30c` | Finished through unchanged three-step Google Home sequence. |

For both branches, programmatic trace comparison proved:

- child service data keys were exactly `request`, `selected_endpoint`,
  `execution_method`, and `media_record`;
- raw execution method and selected endpoint arrived unchanged;
- the complete record was structurally identical at dispatcher and child roots;
- the unknown additive field and both nested execution methods were present;
- child action paths remained `sequence/0`, `sequence/1`, `sequence/2`; and
- neither child consumed the new inputs.

These tests prove transport only, not MediaCat lookup-to-dispatch or normalized
source consumption.

## Failure regression

Each direct dispatcher test retained its existing stop reason and stopped with
`error: true`:

| Case | Dispatcher trace | Stop reason |
| --- | --- | --- |
| Blank method | `cab98fb6d64b278f6921634aa78e0c22` | `Unsupported or blank execution method` |
| Unsupported method | `afd778aed21cde84b05256f56675b9b6` | `Unsupported or blank execution method` |
| Missing HA endpoint | `c6f00de32947c4a8be200d945d8d6afc` | `No valid HA Media Player endpoint supplied` |
| Missing Google Home endpoint | `17f8da02116873945ca66e3b19a0ea05` | `No valid Google Home Device endpoint supplied` |
| Blank routine | `d42ced1852a4d7c280f990e9117736d9` | `No valid routine supplied` |
| Blank routine target area | `2afbd2a278504b9611267e76a6de105e` | `No valid target area supplied` |

Before and after the batch, the newest downstream traces were unchanged:

- HA Media Player: `a84d48ab85f0859363fb7d521f9002f6`;
- Google Home Device: `04e74a28fe2278f96d5c3553da46b30c`;
- Google Automation: `9382e66fb4591dc0d834ef707f7297db`.

No failed validation invoked a downstream engine.

## Final live checks and scope

All four installed definitions retained their reviewed hashes after runtime
tests. The out-of-scope Media Intent Engine, Routine Intent Engine, and Google
Automation hashes remained `883e77ec37747186`, `26a9cd9cc3f31ce0`, and
`6aa39b6b39d12378`. Service discovery still returned only
`curated_media.resolve_item`, and all seven media records remain legacy.

Changed durable artifacts are limited to:

- `ASTV-61_VALIDATION.md`;
- `ASTV-61_Rollback/`;
- `01_Architecture/ASTV_ARCHITECTURE.md`;
- `CURRENT_STATE.md`; and
- approved-target wording in `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md`.

The current-production diagram, central contract registry, intent and endpoint
data, MediaCat, AdvMedia, media-engine execution logic, Google Automation, and
activation state were not changed.

## Retained proof boundary

The first live MediaCat lookup through Select Intent Engine remains unavailable
while schema v2 is active. Lookup-to-dispatch proof and coordinated activation
remain with `ASTV-65`. HA Media Player / AdvMedia source consumption remains with
`ASTV-62`; Google Home `assistant_command` consumption remains with `ASTV-63`;
inactive replacement records remain with `ASTV-64`.

ASTV-61 is ready for user Review / Test. Only the user may move it to `Done`.

