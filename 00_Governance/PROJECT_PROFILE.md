# PROJECT_PROFILE: ASTV

## Profile conformance

This profile contains the required product-profile subjects and
is current under the approved Central Governance authority.

## Document status

- Governance state: current approved
- Exact migration baseline: `aa62fb8edac8b5ad0d184c19b96e7124367dc7cb`

## Product identity

- Product name: ASTV
- Repository: `83degrees/astv`
- DDR origin code: `01`

## Linear work routing

- Default Linear team: `ASTV`

## Purpose

ASTV is the Home Assistant intent and orchestration product. It receives entry
events, resolves requests and household area context, routes intents, selects
playback methods and endpoints, and dispatches to the applicable execution
path.

## Scope

### In scope

- NFC/tag entry and request resolution.
- Intent-catalogue lookup, household area resolution, and intent routing.
- Area/domain preference, playback-method selection, endpoint selection, and
  fallback order.
- Dispatch to ASTV-owned execution paths and governed external interfaces.
- Final Home Assistant media playback and Google Assistant SDK actions, plus
  the ASTV-owned helper action that initiates the external Google Automation
  path.

### Out of scope

- MediaCat catalogue structure, media identity, metadata, membership, and
  available delivery-route facts.
- AdvMedia internal lookup, media-source preparation, media-player-profile
  processing, and payload-generation implementation.
- Home Assistant platform, MQTT infrastructure, Google Assistant, Google Home,
  or Matter ownership.
- The external Google Home automation that reacts to ASTV's Matter-exposed
  helper state.
- Undocumented internals of consumed products or external systems.

## Ownership and boundaries

| Boundary or capability | Relationship | Owner | Notes |
| --- | --- | --- | --- |
| ASTV intent and orchestration pipeline | owned | ASTV | Includes entry, request/area resolution, routing, selection, and dispatch. |
| ASTV execution-dispatch boundary | owned | ASTV | Exact fields and failure behaviour are defined by `03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md`. |
| MediaCat normalized item lookup and returned record | consumed | MediaCat | ASTV consumes the provider-owned contract and does not own the record schema. |
| AdvMedia playback-preparation boundary | consumed | AdvMedia | ASTV owns its adapter and final playback action; AdvMedia owns its entry point and internals. |
| Home Assistant runtime and metadata registries | external | Home Assistant | Runtime truth remains external to this repository. |
| MQTT reader delivery | external | MQTT / reader infrastructure | ASTV consumes configured reader-sensor state changes. |
| Google Assistant, Google Home, and Matter execution surfaces | external | Their respective platforms | ASTV uses governed/configured entry points without owning those platforms. |

## Approved architecture location

- Approved architecture location: `01_Architecture/ASTV_ARCHITECTURE.md`
- Governed diagram: `01_Architecture/Diagrams/ASTV_ARCHITECTURE.drawio`
- Architecture state: current approved
- Material DDRs: None

The Markdown file is the semantic architecture authority. The diagram is its
governed representation.

## Contracts provided

| Contract | Status/version | Authoritative provider-owned location | Consumers | Notes |
| --- | --- | --- | --- | --- |
| `ASTV_EXECUTION_DISPATCH_INTERFACE.md` | current v2.0.0 | `03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` | ASTV | Internal Phase 2-to-Phase 3 boundary; ASTV is both provider and consumer. |

## Contracts consumed

| Contract | Status/version | Provider/owner | Authoritative location | Local use |
| --- | --- | --- | --- | --- |
| `MEDIACAT_ITEM_LOOKUP_INTERFACE.md` | current registry v1.0.0 | MediaCat | `MediaCat/03_Contracts/MEDIACAT_ITEM_LOOKUP_INTERFACE.md` | Normalized lookup and complete returned record used before ASTV selects a method and endpoint. |
| `ASTV_ADVMEDIA_INTERFACE.md` | current v2.0.0 | AdvMedia | `AdvMedia/03_Contracts/ASTV_ADVMEDIA_INTERFACE.md` | Playback context passed through the ASTV adapter; AdvMedia's contracted result is consumed before ASTV's final playback action. |

The provider-owned locations above are the sole operational contract
authorities. Former shared Governance 1.2 copies under
`Home_Assistant/contracts/` are retired and non-authoritative; any temporarily
retained recovery copy must not be used for current work.

## Product dependencies

| Dependency | Type | Owner | Governed interface/evidence | Required state | Failure boundary |
| --- | --- | --- | --- | --- | --- |
| Home Assistant | platform | Home Assistant | Current verified production evidence | Configured ASTV entities, services, area/label metadata, and helpers available | ASTV stops visibly at its documented validation boundaries. |
| MQTT and configured NFC reader sensors | external | MQTT / reader infrastructure | `01_Architecture/ASTV_ARCHITECTURE.md` and production evidence | Reader state changes delivered to Home Assistant | No entry event reaches ASTV when delivery is unavailable. |
| MediaCat | product/service | MediaCat | `MEDIACAT_ITEM_LOOKUP_INTERFACE.md` | Normalized item lookup available and contracted result returned | ASTV stops before method and endpoint selection on lookup failure. |
| AdvMedia | product/service | AdvMedia | `ASTV_ADVMEDIA_INTERFACE.md` | Contracted processing entry point available for the selected HA media-player path | The selected path fails; ASTV does not select another method automatically. |
| Google Assistant SDK / Google Home / Matter | external | Their respective platforms | `01_Architecture/ASTV_ARCHITECTURE.md` and production evidence | Configured external actions and helper exposure available | Failure remains at the selected execution path; no automatic retry is promised. |
| ASTV configuration data | data | ASTV | `astv_tag_mapping.yaml`, `astv_intent_catalogue.yaml`, and `astv_area_endpoints2.yaml` in current production evidence | Files present and loadable at their configured Home Assistant paths | Lookup or resolution fails at the documented ASTV boundary. |

## Implementation namespace / naming identity

- Implementation namespace / naming identity: `astv_`

ASTV owns the `astv_` prefix for its Home Assistant scripts, automation, data
files, and package naming, including `script.astv_*`,
`automation.astv_tag_listener`, `astv_*.yaml`, and `packages/astv`. The prefix
identifies ASTV implementation ownership; it does not transfer ownership of
reused product, platform, service, entity, or infrastructure names.

| Identity | Classification | Owner | Permitted use | Evidence |
| --- | --- | --- | --- | --- |
| `astv_`, `script.astv_*`, `automation.astv_tag_listener`, `packages/astv` | owned | ASTV | ASTV implementation and configuration | Architecture and repository source |
| `curated_media` | consumed | MediaCat | Governed MediaCat lookup only | MediaCat contract |
| `advmedia_`, `script.advmedia_*` | consumed | AdvMedia | Governed AdvMedia entry points only | AdvMedia contract |
| Home Assistant entity/service domains and MQTT sensor identities | external | Home Assistant / infrastructure owners | Configured platform use | Architecture and production evidence |
| `google_assistant_sdk` and Google Home / Matter identities | external | Their respective platforms | Configured external execution | Architecture and production evidence |

## Production and evidence route

- Production route: ASTV runs in the Home Assistant `starburst` instance. Its
  current configured implementation includes `/config/packages/astv/astv_scripts.yaml`
  and ASTV data under `/config/assistive/`; storage-managed definitions are
  operated through Home Assistant's governed configuration route.
- Evidence route: sibling read-only evidence under
  `Production_ReadOnly/starburst/`, supplemented where authorized by verified
  live read-only Home Assistant inspection.
- Provenance and freshness requirement: verify source, capture time, procedure,
  included/excluded content, integrity, and freshness before relying on a
  snapshot. The retained snapshot has no capture manifest, so its provenance,
  completeness, and freshness are not independently established.
- Secrets and mutable-state boundary: credentials, secrets, mutable Home
  Assistant state, and production snapshots remain outside this repository.
- Validation evidence route: Linear records the governed work and validation;
  Git/GitHub records the exact candidate and accepted repository SHAs.
- Known limitations: static snapshot hashes do not prove current live state;
  live per-item configuration search is partial for YAML-defined entities.

Current deployable source deliberately remains at
`04_Source/assistive/astv_intent_catalogue.yaml` and
`04_Source/astv_adapter_advmedia.json`. No complete current ASTV script
package is promoted from read-only production evidence or historical rollback
payloads into this repository by this migration.
