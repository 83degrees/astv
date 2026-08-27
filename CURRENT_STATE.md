# ASTV Current State

## Metadata

- Project: ASTV
- Document version: 1.1.0
- Updated (UTC): 2026-08-25
- Approved work instruction: `ASTV-78`
- Governance manifest: `00_Governance/projects/astv/manifest.json`
- Governance model: `controlled-production@1.0.0`
- Evidence baseline: `00_Governance/baselines/2026-08-14-astv-37/manifest.json`

## Current baseline

ASTV is the Home Assistant intent and orchestration product. It owns NFC/tag
entry, request and area resolution, intent routing, playback-method and endpoint
selection, and dispatch to the implemented execution paths.

The current four-phase flow is recorded in
`ASTV/01_Architecture/ASTV_ARCHITECTURE.md`. The exact visual structure and
manual layout are recorded in
`ASTV/01_Architecture/ASTV_Architecture.drawio`. Current interface names and
ownership are recorded in the three contracts listed below. The retained
validation records and post-baseline records through `ASTV-64_VALIDATION.md`,
together with the cross-product `ASTV-65` cutover evidence,
contain production hashes, normal-path and failure-path results, trace
identifiers, and rollback evidence.

`ASTV-60` through `ASTV-63` installed compatibility-safe transport and consumers
for normalized media context. `ASTV-64` prepared and tested the replacement
catalogue. `ASTV-65` coherently activated that design: all seven active media
records now carry `catalogue_id` and `item_id` without `params.sources`; each
request performs one normalized MediaCat lookup, one ASTV execution-method
selection, and one terminal action. The Home Assistant / AdvMedia and Google
Assistant branches are current, while the Routine path remains unchanged.

The byte-identical legacy catalogue under `ASTV/ASTV-64_Rollback/` and earlier
script packages remain historical rollback evidence. They are not the active
media flow. Immediate ASTV-65 proof at `2026-08-24T20:09:37.490Z` exercised all
seven media records sequentially through `script.astv_uid_gateway`, with clean
traces and logs and an audible user confirmation for every request. ASTV-76 then
removed the dormant v1 shape from `script.astv_adapter_advmedia`; the adapter now
accepts only normalized record context and calls the AdvMedia core once.

`ASTV-67` then implemented and proved AdvMedia's separately owned standalone
MediaCat gateway and retired its unused lookup wrapper. No ASTV runtime
definition changed. A post-retirement Classic FM regression passed through the
normal UID gateway, v2-only ASTV adapter, AdvMedia core, and terminal playback
action without calling the standalone gateway; audible playback was confirmed.

## Source-of-truth references

- Generated governance: `ASTV/AGENTS.md` and
  `ASTV/01_Architecture/AGENTS.md`, rendered from
  `controlled-production@1.0.0`.
- Current architecture: `ASTV/01_Architecture/ASTV_ARCHITECTURE.md`.
- Authoritative diagram: `ASTV/01_Architecture/ASTV_Architecture.drawio`.
- Internal dispatch contract:
  `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md`.
- Current MediaCat lookup contract:
  `contracts/MEDIACAT_ITEM_LOOKUP_INTERFACE.md`.
- Cross-product contract: `contracts/ASTV_ADVMEDIA_INTERFACE.md`.
- Read-only evidence root: `Production_ReadOnly/starburst/`.
- Historical context: `ASTV/00_PreProject_History/CONTEXT_HANDOVER.md`.

Follow the precedence in `ASTV/AGENTS.md`. This document is a restart index; it
does not replace current production evidence, contracts, architecture, the
authoritative diagram, generated governance, validation records, or rollback
packages.

## Contract metadata

The ASTV manifest registers these existing contracts through relative-path
metadata only:

| Contract | ASTV role | Other product |
| --- | --- | --- |
| `contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` | ASTV owns, provides, and consumes the internal Phase 2-to-Phase 3 boundary. | None. |
| `contracts/ASTV_ADVMEDIA_INTERFACE.md` | ASTV owns the boundary adapter, supplies the documented playback context, and consumes AdvMedia's documented response. | AdvMedia owns its entry point and internal playback preparation. |

The registration does not change either contract. Field names, requiredness,
return structure, caller ownership, and the distinction between a caller's
capture variable and a child's returned fields remain contractual.

The MediaCat item-lookup, ASTV execution-dispatch, ASTV-AdvMedia, and AdvMedia
standalone-gateway contracts are current central-registry entries at governance
release 1.1.3. Their v2 boundaries are current after `ASTV-65` and `ASTV-67`
proof. `ASTV-76` retired only the dormant v1 branch of the ASTV-owned AdvMedia
adapter. The existing `astv-advmedia` registry entry remains version `2.0.0`
and `current` unchanged.

## Production evidence index

The following snapshot files were hash-checked read-only on 2026-08-14. They are
the principal static files used by the current architecture and retained
validation records.

| Home_Assistant-relative path | SHA-256 |
| --- | --- |
| `Production_ReadOnly/starburst/packages/astv/astv_scripts.yaml` | `5edb053f79fbd299730d45ac8ac7c29a84456af718159b18136ecd2a565ff5d9` |
| `Production_ReadOnly/starburst/scripts.yaml` | `f13c5bfaa7e895c1e8bde0202365ecdd31d00d806923f9ae5d2a19d42647277c` |
| `Production_ReadOnly/starburst/automations.yaml` | `c23f9ef1c502707e75be2b63046c97e3ed34bb0ec1868e0e2506dfe82ca17bbc` |
| `Production_ReadOnly/starburst/assistive/astv_tag_mapping.yaml` | `44a4180f84d0acc7477b2ca7bd4b45ca08585ba9dbedba5ba971e5eb0211bebd` |
| `Production_ReadOnly/starburst/assistive/astv_intent_catalogue.yaml` | `8b99b82a4d2e5c47f787a1393b844486086f726c12b4cefc9eb48b71181ecbd2` |
| `Production_ReadOnly/starburst/assistive/astv_area_endpoints2.yaml` | `34e3b8db445a522487d496fb89c51a5f88a38f485e0cada04c47c79218db369d` |

These hashes identify files only. They do not establish snapshot capture time,
completeness, deployment, runtime activation, or current live state.

### ASTV-60 live configuration evidence

The live script configuration API was read immediately before and after the
authorized update:

| Script | Pre-change hash | Installed hash |
| --- | --- | --- |
| `script.astv_intent_engine_media` | `b36661a38e022b4b` | `883e77ec37747186` |

Live lookup of all seven active media intent records confirmed that each still
contains only `output` and `sources` under `params`; none contains
`catalogue_id` or `item_id`. Current service discovery returned only
`curated_media.resolve_item`, as expected with schema v2 active. The installed
normalized branch is therefore dormant.

### ASTV-61 live configuration evidence

The four scoped definitions were captured as one rollback unit before mutation,
installed in receiving-boundary-first order, and re-read after validation:

| Script | Pre-change hash | Installed hash |
| --- | --- | --- |
| `script.astv_select_intent_engine` | `e9759f8b814b63df` | `bda1d825cd330779` |
| `script.astv_select_execution_engine` | `338ddf0d9a75efc8` | `9d2eedaeba1f5b86` |
| `script.astv_ha_mplayer_engine` | `d4d5039b2ba6dc0b` | `62a363022c26ca89` |
| `script.astv_g_home_device_engine` | `32dba34e015c9156` | `d9edfefe78b6f590` |

Classic FM, BBC Radio 2, Smooth Radio, and Morning Routine passed through the
normal entry path. Legacy media child calls retained only `request` and
`selected_endpoint`; the Routine call remained `request` plus `target_area`.
Focused direct dispatcher traces proved complete unchanged normalized context
transport, including an unknown additive field, to both media engines without
changing their execution sequences. Six dispatcher failure regressions stopped
before any downstream engine.

### ASTV-62 live configuration evidence

The two scoped definitions were captured as one rollback unit, installed in
adapter-before-caller order, and re-read after validation:

| Script | Pre-change hash | Installed hash |
| --- | --- | --- |
| `script.astv_adapter_advmedia` | `1ddc07631782c3a4` | `fe00d0cea795cc06` |
| `script.astv_ha_mplayer_engine` | `62a363022c26ca89` | `7f2e5588e9a9cedb` |

Classic FM through Radio Browser and BBC Radio 2 through legacy AdvMedia passed
the normal UID entry path with one final playback action each. Six partial,
mixed, or absent-shape calls stopped before a child or playback action. Non-live
Home Assistant template checks preserved complete direct-URL and HA-media-source
records, including unknown additive fields, and an installed-definition audit
confirmed direct v2 composition, no duplicate lookup, no fallback, and one
shared final playback action. The AdvMedia v2 core was not invoked and remains
absent from live service discovery.

### ASTV-63 live configuration evidence

The two scoped definitions were captured as one rollback unit and installed in
provider-before-engine order:

| Script | Pre-change hash | Installed hash |
| --- | --- | --- |
| `script.astv_provider_g_assist` | `09cdf48a46000450` | `052ce3c242fe4e93` |
| `script.astv_g_home_device_engine` | `d9edfefe78b6f590` | `a51304a3b2c88287` |

Smooth Radio, LBC Radio, and News Briefing passed through the normal UID entry
path. Each selected the legacy branch, constructed its existing command, and
reached the single Google Assistant SDK action exactly once. Five non-live
normalized provider compositions produced the agreed commands, including LBC
with Kitchen Speaker and a synthetic Bedroom Speaker endpoint. Nine normalized
engine failures and one mixed provider call stopped explicitly with no legacy
branch and no SDK action. An initial failed attempt exposed child-error
propagation to the shared SDK action; both scripts were restored as one rollback
unit, all three legacy regressions passed, and the corrected definition added
engine-side prechecks and a provider-response guard before reinstallation.

## Validation and rollback index

The accepted central baseline inventories every retained ASTV validation file
and every rollback payload by relative path, SHA-256, size, and UTC modification
time. On 2026-08-14, all 34 indexed ASTV validation and rollback files matched
that baseline: eight validation records and 26 files across nine rollback
packages.

Retained validation records:

| Work | Validation record | SHA-256 |
| --- | --- | --- |
| ASTV-7 | `ASTV/ASTV-7_VALIDATION.md` | `fe9ca67dbb5b3ed3cd1e60822ed46612cd72daf004bd8261249d451935a10a07` |
| ASTV-11 | `ASTV/ASTV-11_VALIDATION.md` | `87a4f00d79ba65ae24caafb96ee72bd8fc4288518dda1b1a288e64b9c3b7cbc7` |
| ASTV-12 | `ASTV/ASTV-12_VALIDATION.md` | `3805f4dd5184edba2b9fb3cb717b40c3d0c25e360142033a0875157da2412d5f` |
| ASTV-13 | `ASTV/ASTV-13_VALIDATION.md` | `f0ebc5afe692e1f56c432d587b8fe968a69bbbd7981db245f69dcdc35b3b40cf` |
| ASTV-16 | `ASTV/ASTV-16_VALIDATION.md` | `c93c13873a0c9a03256f8b00a8e43a988408031851c51a182afa1a719e810d25` |
| ASTV-17 | `ASTV/ASTV-17_VALIDATION.md` | `cb21cceb9f819ae77418aa015f0e75f36f09b4293913dc4ba07594bc22c06283` |
| ASTV-18 | `ASTV/ASTV-18_VALIDATION.md` | `a463d99459d9fe9f28a5f65a7a7fbcb5ff0d1a473b6422bbd3a0dd033d3138dc` |
| ASTV-20 | `ASTV/ASTV-20_VALIDATION.md` | `d605e447bb6a0b0005bca4d715d57147702ab9467bc1db505c8e90ab60cd5981` |

`ASTV-60_VALIDATION.md`, `ASTV-61_VALIDATION.md`,
`ASTV-62_VALIDATION.md`, `ASTV-63_VALIDATION.md`, and
`ASTV-64_VALIDATION.md` are post-baseline evidence for the compatibility
installations, focused and normal-entry regressions, inactive data preparation,
trace identifiers, and their rollback packages. They are
intentionally not added to the historical ASTV-37 central baseline by these
issues.

Retained rollback packages:

| Package | Indexed files | Recovery scope |
| --- | ---: | --- |
| `ASTV/ASTV-7_Rollback/` | 3 | Tag mapping and intent-catalogue test baseline. |
| `ASTV/ASTV-10_Rollback/` | 2 | Lookup package baseline. |
| `ASTV/ASTV-11_Rollback/` | 2 | Pre-Intent-Gateway package and removal procedure. |
| `ASTV/ASTV-12_Rollback/` | 2 | UID Gateway pre-cutover configuration. |
| `ASTV/ASTV-13_Rollback/` | 3 | Retired legacy lookup and data restoration. |
| `ASTV/ASTV-16_Rollback/` | 2 | Media intent-engine pre-cutover configuration. |
| `ASTV/ASTV-17_Rollback/` | 3 | Dispatcher and Select Intent Engine pre-cutover configurations. |
| `ASTV/ASTV-18_Rollback/` | 4 | Phase 2 convergence pre-cutover configurations. |
| `ASTV/ASTV-20_Rollback/` | 5 | Google Automation interface cutover and review-revision baselines. |
| `ASTV/ASTV-61_Rollback/` | 5 | Coordinated pre-change definitions for Select Intent, dispatcher, and both media engines. |
| `ASTV/ASTV-62_Rollback/` | 3 | Coordinated pre-change definitions for the AdvMedia adapter and HA Media Player engine. |
| `ASTV/ASTV-63_Rollback/` | 3 | Coordinated pre-change definitions for the Google Assist provider and Google Home Device engine. |
| `ASTV/ASTV-64_Rollback/` | 2 | Complete byte-identical legacy intent catalogue and coordinated restoration procedure. |

Use each package's `README.md` for its exact recovery procedure. The central
baseline manifest is the file-level checksum index. This restart document does
not duplicate or rewrite rollback payloads, trace evidence, or validation
narratives.

## Verified status

The retained validation series establishes the accepted implementation through
ASTV-20. `ASTV-60_VALIDATION.md` through `ASTV-63_VALIDATION.md` add the current
compatibility installations, exact rollback baselines, before/after live hashes,
normal-entry traces, focused transport proof, and failure regressions.
`ASTV-64_VALIDATION.md` adds the prepared eight-record catalogue, byte-identical
legacy rollback, isolated all-record composition proof, and rollback rehearsal.
`ASTV-65` then supplied coordinated live proof at
`2026-08-24T20:09:37.490Z`: all seven UID requests completed with exactly one
lookup, one selection, one terminal action, clean traces and logs, and audible
user confirmation. `ASTV-76` deployed the v2-only AdvMedia adapter at live hash
`f3cd9fa7b196ccce`. A normal Classic FM UID request completed one normalized
lookup, one method selection, one adapter/core call, and one playback action;
the kitchen speaker entered `playing`, and the user confirmed audible playback.

## Known limitations and unresolved items

- The production snapshot has no capture manifest, so its source, capture
  procedure, completeness, and freshness are not independently established.
- Static snapshot hashes do not prove current live configuration or runtime
  behavior. The scoped ASTV-65 live proof supplements them for the tested paths
  but is not a continuous monitor or a complete new production capture.
- Production evidence is exposed with broader filesystem permissions than the
  intended read-only policy. The governed rule remains: never write to
  `Production_ReadOnly/`.
- Home Assistant mutation tools may be available in some environments. They must
  remain unused unless a separately picked-up issue explicitly authorizes the
  exact live change.
- The validation and rollback index proves retained file integrity against the
  accepted ASTV-37 baseline; it does not replay old runtime tests.
- Live configuration search is partial because three YAML-defined automations
  and three YAML-defined scripts are not exposed by the per-item configuration
  endpoint. The known caller was confirmed from the live searchable
  configuration and the hash-checked static `scripts.yaml` snapshot.
- The ASTV-65 operational rollback window was explicitly closed on 2026-08-25;
  its packages remain read-only historical evidence. ASTV-76 has its own exact
  pre-change adapter rollback package.

## Working model

Design tasks may inspect evidence, develop requirements, and prepare Linear work
instructions, but they do not implement. ASTV implementation requires a separate
Codex task started with an eligible issue, followed by the hard `Ready` to
`In Progress` pickup gate. Completed implementation and validation move to
`Review / Test`; only the user may move an issue to `Done`.

Production-changing work additionally requires explicit mutation scope,
pre-change evidence and a tested restoration path. Validation evidence must
record the relevant configuration hashes, normal and failure-path outcomes, and
trace identifiers where runtime traces are part of the acceptance criteria.

## Next authorized step

Review and test the ASTV-67 cross-product documentation and its recorded normal
ASTV v2 regression. No ASTV runtime script changed under ASTV-67. Only the user
may move `ASTV-67` from `Review / Test` to `Done` after the issue reaches that
state.
