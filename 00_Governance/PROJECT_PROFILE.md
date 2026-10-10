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

ASTV is the Home Assistant intent and orchestration product. It receives
canonical intent invocations through its governed provider boundary, resolves
requests and household area context, routes intents, selects playback methods
and endpoints, and dispatches to the applicable execution path.

## Scope

### In scope

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
- AdvNFC NFC-reader event consumption, reader-state filtering, UID normalization,
  tag lookup, or tag mapping.
- Home Assistant platform, MQTT infrastructure, Google Assistant, Google Home,
  or Matter ownership.
- The external Google Home automation that reacts to ASTV's Matter-exposed
  helper state.
- Undocumented internals of consumed products or external systems.

## Ownership and boundaries

| Boundary or capability | Relationship | Owner | Notes |
| --- | --- | --- | --- |
| ASTV intent and orchestration pipeline | owned | ASTV | Begins at the governed Intent Invocation boundary and includes request/area resolution, routing, selection, and dispatch. |
| ASTV Intent Invocation boundary | provided | ASTV | Supported caller entry through `script.astv_intent_gateway`; exact request and failure semantics are defined by `03_Contracts/ASTV_INTENT_INVOCATION_INTERFACE.md`. AdvNFC is the active NFC-entry caller. |
| ASTV execution-dispatch boundary | owned | ASTV | Exact fields and failure behaviour are defined by `03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md`. |
| MediaCat normalized item lookup and returned record | consumed | MediaCat | ASTV consumes the provider-owned contract and does not own the record schema. |
| AdvMedia playback-preparation boundary | consumed | AdvMedia | ASTV's HA Media Player Engine calls the AdvMedia direct core and owns the final playback action; AdvMedia owns its entry point and internals. |
| Home Assistant runtime and metadata registries | external | Home Assistant | Runtime truth remains external to this repository. |
| Google Assistant, Google Home, and Matter execution surfaces | external | Their respective platforms | ASTV uses governed/configured entry points without owning those platforms. |

## Approved architecture location

- Approved architecture location: `01_Architecture/ASTV_ARCHITECTURE.md`
- Governed diagram: `01_Architecture/Diagrams/ASTV_ARCHITECTURE.drawio`
- Architecture state: current approved
- Material DDRs: `02_Decisions/DDR-01-001_DIRECT_INTENT_ENGINE_EXECUTION_DISPATCH.md`, `02_Decisions/DDR-01-002_IMMUTABLE_RUNTIME_INTENT_CATALOGUE_REGISTRY.md`, and `02_Decisions/DDR-01-003_DURABLE_SHARED_INTENT_CATALOGUE_DRAFT_AND_EXPLICIT_ACTIVATION.md`

The Markdown file is the semantic architecture authority. The diagram is its
governed representation.

## Contracts provided

| Contract | Status/version | Authoritative provider-owned location | Consumers | Notes |
| --- | --- | --- | --- | --- |
| `ASTV_INTENT_INVOCATION_INTERFACE.md` | current v1.0.0 | `03_Contracts/ASTV_INTENT_INVOCATION_INTERFACE.md` | AdvNFC; future governed callers | Supported ASTV Intent Gateway invocation boundary. AdvNFC is the active NFC-entry caller following the accepted cutover. |
| `ASTV_EXECUTION_DISPATCH_INTERFACE.md` | current v4.1.0 | `03_Contracts/ASTV_EXECUTION_DISPATCH_INTERFACE.md` | ASTV | Internal three-context boundary from Phase 2 producers through the Phase 3 execution engines; ASTV is both provider and consumer. |
| `ASTV_INTENT_CATALOGUE_LOOKUP_INTERFACE.md` | current v1.0.0; provided by the ASTV-334 HACS Beta `v0.2.0-beta.1c4064b` deployed and validated on `starburst` | `03_Contracts/ASTV_INTENT_CATALOGUE_LOOKUP_INTERFACE.md` | `script.astv_find_intent_record` after governed cutover | Read-only immutable-active-snapshot lookup boundary; the existing script remains the record-only compatibility adapter. |
| `ASTV_INTENT_CATALOGUE_ADMINISTRATION_INTERFACE.md` | current v1.0.0 staged operations deployed through ASTV-334 HACS Beta `v0.2.0-beta.1c4064b`; ASTV-335 activation candidate not deployed | `03_Contracts/ASTV_INTENT_CATALOGUE_ADMINISTRATION_INTERFACE.md` | provider-independent managers | ASTV-334 discovery, status, active reads, validation, guarded durable staging and discard are runtime-active on `starburst`; stable integration release `v0.2.0` is published. ASTV-335 adds explicit activation in the review candidate only. Activation preflights distinct MediaCat references and retains active, persisted and draft state on pre-commit failure. Storage serialization is not exposed. |

## Contracts consumed

| Contract | Status/version | Provider/owner | Authoritative location | Local use |
| --- | --- | --- | --- | --- |
| `MEDIACAT_ITEM_LOOKUP_INTERFACE.md` | current v2.0.0 | MediaCat | `MediaCat/03_Contracts/MEDIACAT_ITEM_LOOKUP_INTERFACE.md` | Normalized lookup through the sole current producer, `mediacat.resolve_media_record`, before ASTV selects a method and endpoint. |
| `ASTV_ADVMEDIA_INTERFACE.md` | current v3.0.0 | AdvMedia | `AdvMedia/03_Contracts/ASTV_ADVMEDIA_INTERFACE.md` | The HA Media Player Engine passes playback context directly to the AdvMedia core and consumes its playback payload before ASTV's final playback action. |

The provider-owned locations above are the sole operational contract
authorities. Former shared Governance 1.2 copies under
`Home_Assistant/contracts/` are retired and non-authoritative; any temporarily
retained recovery copy must not be used for current work.

## Product dependencies

| Dependency | Type | Owner | Governed interface/evidence | Required state | Failure boundary |
| --- | --- | --- | --- | --- | --- |
| Home Assistant | platform | Home Assistant | Current verified production evidence | Configured ASTV entities, services, area/label metadata, and helpers available | ASTV stops visibly at its documented validation boundaries. |
| MediaCat | product/service | MediaCat | `MEDIACAT_ITEM_LOOKUP_INTERFACE.md` | Normalized item lookup available and contracted result returned | ASTV stops before method and endpoint selection on lookup failure. |
| AdvMedia | product/service | AdvMedia | `ASTV_ADVMEDIA_INTERFACE.md` | Contracted processing entry point available for the selected HA media-player path | The selected path fails; ASTV does not select another method automatically. |
| Google Assistant SDK / Google Home / Matter | external | Their respective platforms | `01_Architecture/ASTV_ARCHITECTURE.md` and production evidence | Configured external actions and helper exposure available | Failure remains at the selected execution path; no automatic retry is promised. |
| ASTV configuration data | data | ASTV | `astv_intent_catalogue.yaml` and `astv_area_endpoints.yaml` in current production evidence | Files present and loadable at their configured Home Assistant paths | Lookup or resolution fails at the documented ASTV boundary. |

## Implementation namespace / naming identity

- Implementation namespace / naming identity: `astv_`

ASTV owns the `astv_` prefix for its Home Assistant scripts, automation, data
files, and package naming, including `script.astv_*`,
`astv_*.yaml`, and `packages/astv`. The prefix
identifies ASTV implementation ownership; it does not transfer ownership of
reused product, platform, service, entity, or infrastructure names.

| Identity | Classification | Owner | Permitted use | Evidence |
| --- | --- | --- | --- | --- |
| `astv_`, `script.astv_*`, `packages/astv` | owned | ASTV | ASTV implementation and configuration | Architecture and repository source |
| `mediacat` | consumed | MediaCat | Sole current Home Assistant action namespace for governed MediaCat lookup | MediaCat contract |
| `curated_media` catalogue identity | consumed | MediaCat | Logical catalogue identifier passed to MediaCat; not an integration/action namespace or runtime rollback surface | MediaCat contract |
| `advmedia_`, `script.advmedia_*` | consumed | AdvMedia | Governed AdvMedia entry points only | AdvMedia contract |
| Home Assistant entity/service domains | external | Home Assistant | Configured platform use | Architecture and production evidence |
| `google_assistant_sdk` and Google Home / Matter identities | external | Their respective platforms | Configured external execution | Architecture and production evidence |

## Production and evidence route

- Production route: ASTV runs in the Home Assistant `starburst` instance. AdvNFC
  supplies NFC-originated canonical intent invocations through the governed ASTV
  Intent Invocation boundary. ASTV's current configured implementation includes
  `/config/packages/astv/astv_scripts.yaml` and ASTV-owned data under
  `/config/astv/`; storage-managed definitions are operated through Home
  Assistant's governed configuration route.
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

## Repository source baseline

The current ASTV implementation baseline is held under
`04_Implementation/haos/source/config/`.

## Deployable units

| Deployable unit | Type | Authoritative source | Target | Mechanism | Detailed authority |
| --- | --- | --- | --- | --- | --- |
| ASTV Home Assistant configuration | `haos_config` | `04_Implementation/haos/source/config/**` | `starburst` Home Assistant `/config/**`; exact path mappings are recorded in the ASTV deployment runbook | `operator_selected` | `00_Governance/01_Central/01_Standards/HOME_ASSISTANT_CONFIG_DEPLOYMENT_STANDARD.md` and `08_Deployment/ASTV_HAOS_CONFIG_DEPLOYMENT_RUNBOOK.md` |
| ASTV Intent Catalogue provider (ASTV-334 Beta staged administration deployed; ASTV-335 activation candidate not deployed) | `haos_integration` | `custom_components/astv_intent_catalogue/**` under the approved HACS source exception | `starburst` Home Assistant `/config/custom_components/astv_intent_catalogue/**` | `hacs` | `00_Governance/01_Central/01_Standards/HOME_ASSISTANT_INTEGRATION_DEPLOYMENT_STANDARD.md` and `08_Deployment/ASTV_INTENT_CATALOGUE_INTEGRATION_MIGRATION_PLAN.md` |

The provider-integration row records the ASTV-334 HACS Beta
`v0.2.0-beta.1c4064b` staged-administration provider as installed and validated
on `starburst`, including successful live staging. Stable release `v0.2.0` is
published. The ASTV-335 explicit-activation implementation remains a review
candidate: it has not been deployed, accepted in Beta, or established as
current runtime state.

The operator selects the practical transport for each authorised configuration deployment.
No transport is an ASTV product dependency merely because an operator uses it.
