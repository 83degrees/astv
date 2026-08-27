# ASTV-12 rollback snapshot

Created: 2026-08-11

Before the production cutover, live Home Assistant returned the complete storage-mode configuration for `script.astv_uid_gateway` with configuration hash `bef76d1a1a449709`. The exact configuration is recorded in `astv_uid_gateway.pre-cutover.json`.

The snapshot is recoverable through Home Assistant's normal script configuration API: restore the JSON object's `config` value to the bare script ID `astv_uid_gateway`, preserving its recorded category. Then verify the returned configuration and hash before any reload or test.

The legacy package lookup `script.astv_find_uid_record` and `starburst/assistive/astv_tags2.yaml` are retained unchanged as an additional controlled fallback.
