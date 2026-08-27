# ASTV-17 Rollback Baseline

These files contain the exact accepted ASTV-16 production configurations
captured immediately before ASTV-17 changed the global execution dispatcher
and Select Intent Engine.

- `astv_select_execution_engine.pre-cutover.json`
- `astv_select_intent_engine.pre-cutover.json`

To roll back, restore each file's `config` object to the corresponding
Home Assistant script and confirm the resulting stable hash matches the
recorded `config_hash`.

