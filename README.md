# ASTV Repository

This repository contains ASTV's Governance 2.0 authorities, maintained product
source, and explicitly separated historical context. Product meaning is defined
by the applicable authority, not by this directory guide.

## Current structure

| Path | Durable role |
| --- | --- |
| `AGENTS.md` | Governance loader for repository work. |
| `CENTRAL_GOVERNANCE.md` | Deployed Governance 2.0 rulebook. |
| `PROJECT_PROFILE.md` | ASTV product identity, scope, boundaries, dependencies, source and evidence routes. |
| `AAR_REGISTER.md` | Product AAR register. |
| `01_Architecture/` | Current semantic architecture and its governed diagram. |
| `03_Contracts/` | ASTV-owned provider contracts. |
| `Standards/` | Deployed shared standards applicable to this product. |
| `assistive/` | Maintained ASTV data source that mirrors its Home Assistant data role. |
| `scripts/` | Maintained ASTV script source exports. |
| `00_History/` | Historical context retained for dependency and recovery use; not current authority. |

The current authority locations and the production/evidence route are recorded
in `PROJECT_PROFILE.md`. Historical files must not override those authorities.

## Pre-normalization root disposition

The pre-normalization root was reviewed as follows:

| Pre-change location | Disposition | Reason |
| --- | --- | --- |
| `AGENTS.md`, `CENTRAL_GOVERNANCE.md`, `PROJECT_PROFILE.md`, `AAR_REGISTER.md` | Retain | Required Governance 2.0 product artefacts. |
| `.gitattributes` | Retain | Repository-level Git configuration. |
| `01_Architecture/` | Retain | Approved ASTV architecture authority and governed diagram location. |
| `03_Contracts/` | Retain | Provider-owned ASTV contract authority. |
| `Standards/` | Retain | Required deployed Architecture Diagram Standard. |
| `assistive/` | Retain | Durable maintained data-source role and established Home Assistant path relationship. |
| `ASTV-76_Source/` | Rename to `scripts/` | The content is current maintained script source; its durable role is not the issue that created it. |
| `00_PreProject_History/` and `CURRENT_STATE.md` | Consolidate under `00_History/` | Both are explicitly historical; one neutral history boundary removes root-level authority ambiguity while preserving ASTV-81's required current-state record. |

No runtime, architecture, contract, ownership, or behaviour change is implied by
these physical dispositions.
