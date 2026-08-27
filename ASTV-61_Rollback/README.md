# ASTV-61 coordinated rollback

This package contains the exact four live script definitions captured on
2026-08-24 immediately before the ASTV-61 installation. Treat the four
definitions as one rollback unit.

| Script | Pre-change stable configuration hash | Snapshot |
| --- | --- | --- |
| `script.astv_select_intent_engine` | `e9759f8b814b63df` | `astv_select_intent_engine.pre-change.json` |
| `script.astv_select_execution_engine` | `338ddf0d9a75efc8` | `astv_select_execution_engine.pre-change.json` |
| `script.astv_ha_mplayer_engine` | `d4d5039b2ba6dc0b` | `astv_ha_mplayer_engine.pre-change.json` |
| `script.astv_g_home_device_engine` | `32dba34e015c9156` | `astv_g_home_device_engine.pre-change.json` |

All four scripts were in category `01K9QMV1C04YWV4HAS8G6V7FRV`.

## Coordinated restoration procedure

1. Retrieve all four current live definitions and stable hashes. Confirm they
   match the reviewed ASTV-61 installed definitions. Stop and investigate any
   unexpected drift.
2. Restore `astv_select_intent_engine` first using the complete `config`
   object from its snapshot, the retained category, and its freshly retrieved
   hash as the optimistic-lock value. This removes the new caller handoff first.
3. Restore `astv_select_execution_engine` using the same narrow configuration
   mechanism and a fresh hash.
4. Restore `astv_g_home_device_engine`, then
   `astv_ha_mplayer_engine`, from their complete snapshots with fresh hashes.
5. Allow each narrow script configuration update to make the saved definition
   queryable. Do not reload unrelated configuration and do not restart Home
   Assistant.
6. Re-read all four definitions. Confirm structural identity with the captured
   `config` objects and confirm the stable hashes above.
7. Re-run the Classic FM, BBC Radio 2, Smooth Radio, and Morning Routine legacy
   regressions before returning the system to normal use.

If any restoration step fails, do not continue normal operation with a partial
dispatcher boundary. Complete restoration of all four definitions or escalate
the exact failure and current hashes.

This package changes no intent data, MediaCat or AdvMedia implementation, media
engine execution sequence, Google Automation logic, contract registry, or
architecture diagram.

