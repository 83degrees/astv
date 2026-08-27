# ASTV-63 Validation

## Result

ASTV-63 installed the inactive normalized Google Home Device consumer and the
dual-shape Google Assist provider in live Home Assistant. Smooth Radio, LBC
Radio, and News Briefing passed the normal legacy entry path with unchanged
commands and exactly one Google Assistant SDK action each. Normalized command
composition and every required failure were proved without a successful SDK
call. No intent record, endpoint, command builder, dispatcher, MediaCat,
AdvMedia, Google Cast, or Google Assistant SDK integration was changed.

## Authorization and source checks

- Linear issue `ASTV-63` was retrieved from team `astv` in `Ready`; ASTV-34,
  ASTV-54, ASTV-61, and ASTV-62 were all `Done`.
- The issue was checked against generated governance,
  `01_Architecture/ASTV_ARCHITECTURE.md`,
  `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md`, and
  `contracts/MEDIACAT_ITEM_LOOKUP_INTERFACE.md`, then moved to `In Progress`
  before mutation.
- Live reads confirmed the ASTV-61 dispatcher and Google Home receiving
  baseline (`9d2eedaeba1f5b86` and `d9edfefe78b6f590`) and the ASTV-62 HA Media
  Player baseline (`7f2e5588e9a9cedb`).
- The static production snapshot has no capture manifest and predates ASTV-61
  through ASTV-63. It was used only for limited read-only intent and UID
  reference evidence and supplemented by fresh live configuration reads.
- Fresh live lookup of all seven active media records returned only `output`
  and legacy `sources` under `params`; none supplied `catalogue_id` or `item_id`.
  Service discovery returned only `curated_media.resolve_item`. The normalized
  branch is therefore installed but inactive.

## Pre-change evidence and rollback

| Script | Pre-change hash | Category |
| --- | --- | --- |
| `script.astv_provider_g_assist` | `09cdf48a46000450` | `01KY5BCDDWE2CK0HM5RT0KXTNX` (`ASTV (Providers)`) |
| `script.astv_g_home_device_engine` | `d9edfefe78b6f590` | `01K9QMV1C04YWV4HAS8G6V7FRV` (`Assistive Tech`) |

The exact definitions were captured before mutation in `ASTV-63_Rollback/`.
Snapshot SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `astv_provider_g_assist.pre-change.json` | `a41f7185f07baae2930c49c75dbe4e464a8afdae3a1a858d598eb7e1495f2025` |
| `astv_g_home_device_engine.pre-change.json` | `d8a16d9d492313a49a03d8e01ea31a74034950cdf2f0b04af1dc1c91d2030429` |
| `README.md` | `8bc1be6f09a05a4014f7e9ca2f8b083e69aa9224f31b5aa619f6d9f7a5893d8e` |

The atomic restoration order is provider first, then engine, followed by fresh
hash reads and all three legacy regressions.

## Controlled installation and exercised rollback

The provider was installed first and returned all three existing legacy
commands unchanged before the engine was installed. The first engine attempt
exposed that a child-script `stop` did not prevent its caller from continuing:
missing command, blank command, and unusable endpoint fixtures reached the
shared SDK action with no usable command (`adb171626cf29295e1508fb452e4857d`,
`4c2b5122444e2787cd8a022dd051642e`, and
`649ee5d5594393500d6aa1bc9b5c2071`).

That result met the issue's rollback trigger. The provider was restored first
to `09cdf48a46000450`, then the engine to `d9edfefe78b6f590`; structural identity
with both snapshots was confirmed and Smooth Radio, LBC Radio, and News
Briefing all passed again. The corrected engine performs normalized command and
endpoint checks before calling the provider and rejects an unusable provider
response before the one shared SDK action. A later non-assistant source fixture
exposed an early `append_target` evaluation error
(`4b6be9637d4989260fac8f2f9ecac4b4`); command-specific extraction was moved
after source-type and provider validation, and that case then stopped explicitly.

No restart or broad reload occurred. The final installed definitions are:

| Script | Installed hash |
| --- | --- |
| `script.astv_provider_g_assist` | `052ce3c242fe4e93` |
| `script.astv_g_home_device_engine` | `a51304a3b2c88287` |

## Live legacy regression

All three final tests entered through `script.astv_uid_gateway` with
`sensor.pi_nfc_99_last_uid`. Each trace had neither normalized input, selected
the legacy branch, called the existing provider and builder, and contained one
`google_assistant_sdk.send_text_command` action.

| Case | UID | Engine trace | Command | SDK calls |
| --- | --- | --- | --- | ---: |
| Smooth Radio | `DEADSMOOTH` | `9e01c39d9213e018f1475edcc0d1b0f6` | `Play Smooth Radio on Global Player on Kitchen Speaker` | 1 |
| LBC Radio | `DEADLBC` | `f6140285e10d3d27cff4e7c37e2297d2` | `play LBC Radio on Global Player on Kitchen Speaker` | 1 |
| News Briefing | `DEADNEWSBRIEF` | `21b95a5e67bfa9efeac2d5b099caa345` | `Play my news briefing on Kitchen Speaker` | 1 |

The LBC result intentionally remains the current legacy command; the corrected
endpoint-independent source is inactive until cutover.

## Non-live normalized composition

Direct normalized provider calls exercised the installed provider and existing
unchanged command builder without invoking the Google Home Device engine or
SDK. Home Assistant template request `927918` separately proved that selecting
`g_home_device` reads the exact
`media_record.execution_methods[execution_method].source` mapping from a record
that also contained an unselected method and an unknown additive field.

| Fixture | Composed command |
| --- | --- |
| Smooth Radio / Kitchen | `Play Smooth Radio on Global Player on Kitchen Speaker` |
| News Briefing / Kitchen | `Play my news briefing on Kitchen Speaker` |
| LBC / Kitchen | `play LBC Radio on Global Player on Kitchen Speaker` |
| LBC / synthetic Bedroom endpoint | `play LBC Radio on Global Player on Bedroom Speaker` |
| `append_target: false` | `Play Test Station` |

The two LBC results prove that endpoint identity is not embedded in the
MediaCat command.

## Normalized failure proof

Every engine fixture included a legacy trap command, `DO NOT USE LEGACY
FALLBACK`. Each trace selected no legacy branch and contained zero provider and
zero SDK calls.

| Case | Trace | Explicit stop |
| --- | --- | --- |
| Method only | `b15f9dd19a5bb9d42f0ae345d0c7009e` | Incomplete normalized handoff |
| Record only | `e86beee12ab0016151cb6b1d4dd9826d` | Incomplete normalized handoff |
| Selected method absent | `86a2dbc8282de5b63d956b8bb50ed2a0` | Selected execution method absent |
| Source absent | `fb5178a6324c63f884b5830d1d35a3bb` | Selected method has no assistant source |
| Wrong `source_type` | `d318c08b28f196b1665062abc45b7752` | Source is not `assistant_command` |
| Unsupported assistant provider | `b1a111d395f0037f56ec7b02a6f3da37` | Unsupported normalized assistant provider |
| Command missing | `b565f9f8044cacf0a68ea34f062a7ff3` | Command missing or blank |
| Command blank | `c83197d7c6d08ab5a884b6940a88872d` | Command missing or blank |
| Required endpoint unusable | `7436388a8de638f4c462cc4d3933122f` | Usable endpoint phrase required |

A direct provider call containing both complete legacy and normalized shapes
stopped as `Incomplete or mixed Google Assistant provider context` before the
builder (`0d77eb2732c435ddca1c45fa0b52b7c8`). The provider contains no SDK action.

## Installed-definition audit and scope

A 19-assertion audit passed. It confirmed exclusive both-or-neither engine
branches; exact selected-source access; no normalized legacy-request access,
lookup, or reselection; source/provider/command/endpoint checks; a normalized
provider-response guard; preserved legacy engine and provider mappings; one SDK
invocation point; normalized provider use of only `assistant_source.command`
and `assistant_source.append_target`; reuse of the existing builder; and no
`continue_on_error`.

Unchanged live hashes include:

- `script.astv_cmd_builder_media`: `ee4b5a81ebcc30fa`;
- `script.astv_select_execution_engine`: `9d2eedaeba1f5b86`; and
- `script.astv_ha_mplayer_engine`: `7f2e5588e9a9cedb`.

The shared dispatch contract changed implementation-status wording only. No
field, requiredness, meaning, status, or version changed. The current-production
diagram remains unchanged because all seven active records still use the legacy
shape. Live normalized execution, record activation, MediaCat v3, and coordinated
cross-product proof remain with ASTV-64 and ASTV-65.
