# ASTV-16 Rollback

`astv_intent_engine_media.pre-cutover.json` contains the exact accepted
pre-cutover configuration captured from Home Assistant immediately before the
ASTV-16 caller migration.

- Script: `script.astv_intent_engine_media`
- Stable configuration hash: `af4f068ab94770a3`

To roll back, restore the `config` object to `astv_intent_engine_media` and
confirm the resulting script again calls `script.astv_select_media_engine` with
`request` and `playback_endpoint`.
