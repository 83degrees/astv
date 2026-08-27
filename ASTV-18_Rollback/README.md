# ASTV-18 rollback baseline

Accepted ASTV-17 production configurations captured before the ASTV-18
Phase 2 convergence cutover on 2026-08-12.

| Script | Stable Home Assistant configuration hash | Snapshot |
| --- | --- | --- |
| `script.astv_select_intent_engine` | `325c73773e53f0ab` | `astv_select_intent_engine.pre-cutover.json` |
| `script.astv_intent_engine_media` | `16606dea116a7cdc` | `astv_intent_engine_media.pre-cutover.json` |
| `script.astv_intent_engine_routine` | `26a9cd9cc3f31ce0` | `astv_intent_engine_routine.pre-cutover.json` |

These files preserve the exact accepted branch-local ASTV-17 topology. If
rollback is required, restore all three configurations together before
restoring the matching contract and architecture documentation.
