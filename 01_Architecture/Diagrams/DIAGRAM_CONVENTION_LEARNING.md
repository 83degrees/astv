# ASTV Diagram Convention Learning

## Status

This file records ASTV-local visual conventions observed in the current
governed diagram and the historical, non-authoritative Governance 1.2 ASTV
architecture overlay. It does not define architecture and does not amend the
central Architecture Diagram Standard.

## Established ASTV-local conventions

- Blue represents main ASTV pipeline scripts.
- Green represents supporting functions and providers.
- Yellow represents data sources.
- Purple represents external actions.
- Neutral grey represents Home Assistant entities.
- A grey hexagon represents an external subsystem.
- ASTV script and function boxes show both the friendly name and technical
  entity ID.
- Decision diamonds use the established compact 50×50 baseline and must not be
  enlarged without explicit approval.
- Cross-functional phase bands and manually corrected layout are preserved.
- Phase 3 execution branches may occupy separate local regions and must not be
  forced into equal vertical lanes.
- The ASTV diagram may show the AdvMedia adapter and external subsystem, but
  never AdvMedia's internal function chain.
- Established branch-outcome labels include `Media`, `Routine`,
  `HA Media Player`, `Google Home Device`, `AdvMedia`, and `Radio Browser`.

Shared connector, variable-label, gateway, boundary, editing, and review rules
remain defined only by `00_Governance/01_Central/01_Standards/ARCHITECTURE_DIAGRAM_STANDARD.md`.
