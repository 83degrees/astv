# ASTV-60 Rollback

`astv_intent_engine_media.pre-change.json` contains the exact live
`script.astv_intent_engine_media` definition captured immediately before the
ASTV-60 update.

- Script storage key: `astv_intent_engine_media`
- Pre-change stable configuration hash: `b36661a38e022b4b`
- Script category: `01K9QMV1C04YWV4HAS8G6V7FRV`

## Restoration procedure

1. Retrieve the current `script.astv_intent_engine_media` definition and stable
   configuration hash.
2. Use the supported Home Assistant script configuration API to replace only
   `astv_intent_engine_media` with the complete `config` object in
   `astv_intent_engine_media.pre-change.json`, retaining the recorded category.
3. Supply the freshly retrieved current hash as the optimistic-lock value. Do
   not restore if the hash changed unexpectedly; investigate first.
4. Allow the narrow script configuration update to reload the saved script. Do
   not reload unrelated configuration or restart Home Assistant.
5. Retrieve the restored definition and confirm it is structurally identical to
   the captured `config` object. Re-run the three ASTV-60 legacy regressions
   before returning the system to normal use.

This package restores only `script.astv_intent_engine_media`. It does not change
intent data, selection helpers, dispatchers, execution scripts, MediaCat,
AdvMedia, contracts, or the architecture diagram.
